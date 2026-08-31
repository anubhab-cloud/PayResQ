"""
tests/test_agent.py
Tests for the AI Recovery Agent, read tools, and LLM providers.
"""
import pytest
import pytest_asyncio
from app.agents.providers.fake import FakeLLMProvider
from app.agents.providers import get_provider
from app.agents.recovery_agent import RecoveryAgent
from app.agents.schemas import AgentDecision
from app.models.enums import RecoveryActionType
from app.agents.tools.read_tools import (
    get_transaction,
    get_customer_history,
    get_failure_context,
    get_recovery_predictions,
    get_merchant_context,
    get_previous_recovery_actions,
)


@pytest.mark.asyncio
async def test_fake_llm_provider_valid_decision():
    provider = FakeLLMProvider()
    response = await provider.generate_decision("prompt")
    assert "RETRY_AFTER_DELAY" in response


@pytest.mark.asyncio
async def test_fake_llm_provider_failure():
    provider = FakeLLMProvider(should_fail=True)
    with pytest.raises(Exception):
        await provider.generate_decision("prompt")


@pytest.mark.asyncio
async def test_provider_factory():
    fake_p = get_provider("fake")
    assert fake_p.provider_name == "fake"


@pytest.mark.asyncio
async def test_recovery_agent_analysis_success(db_session, async_client):
    # Setup merchant, customer, transaction
    m_resp = await async_client.post("/api/v1/merchants", json={"name": "Agent Merchant"})
    m_id = m_resp.json()["id"]

    c_resp = await async_client.post("/api/v1/customers", json={
        "merchant_id": m_id, "external_customer_id": "C-AGENT-1", "name": "Agent User"
    })
    c_id = c_resp.json()["id"]

    tx_resp = await async_client.post("/api/v1/transactions", json={
        "merchant_id": m_id, "customer_id": c_id,
        "external_transaction_id": "TX-AGENT-1", "amount": "4500.00"
    })
    tx_id = tx_resp.json()["id"]

    provider = FakeLLMProvider()
    agent = RecoveryAgent(provider=provider)

    decision = await agent.analyze(tx_id, db_session)

    assert isinstance(decision, AgentDecision)
    assert decision.action in (RecoveryActionType.RETRY_AFTER_DELAY, RecoveryActionType.RETRY_NOW, RecoveryActionType.SEND_PAYMENT_LINK, RecoveryActionType.CHANGE_PAYMENT_METHOD)
    assert decision.confidence > 0.0


@pytest.mark.asyncio
async def test_recovery_agent_malformed_llm_output_fallback(db_session, async_client):
    m_resp = await async_client.post("/api/v1/merchants", json={"name": "Malformed Merchant"})
    m_id = m_resp.json()["id"]
    c_resp = await async_client.post("/api/v1/customers", json={"merchant_id": m_id, "external_customer_id": "C-MAL-1", "name": "Mal User"})
    c_id = c_resp.json()["id"]
    tx_resp = await async_client.post("/api/v1/transactions", json={"merchant_id": m_id, "customer_id": c_id, "external_transaction_id": "TX-MAL-1", "amount": "1000.00"})
    tx_id = tx_resp.json()["id"]

    provider = FakeLLMProvider(malformed_response=True)
    agent = RecoveryAgent(provider=provider)

    decision = await agent.analyze(tx_id, db_session)

    # Should safely fallback to STOP
    assert decision.action == RecoveryActionType.STOP
    assert decision.confidence == 0.0
    assert "fallback" in decision.reason.lower()


@pytest.mark.asyncio
async def test_read_tools(db_session, async_client):
    m_resp = await async_client.post("/api/v1/merchants", json={"name": "Tool Merchant"})
    m_id = m_resp.json()["id"]
    c_resp = await async_client.post("/api/v1/customers", json={"merchant_id": m_id, "external_customer_id": "C-TOOL-1", "name": "Tool User"})
    c_id = c_resp.json()["id"]
    tx_resp = await async_client.post("/api/v1/transactions", json={"merchant_id": m_id, "customer_id": c_id, "external_transaction_id": "TX-TOOL-1", "amount": "2000.00"})
    tx_id = tx_resp.json()["id"]

    tx_data = await get_transaction(tx_id, db_session)
    assert tx_data["amount"] == 2000.0

    cust_data = await get_customer_history(c_id, db_session)
    assert cust_data["total_transactions"] == 1

    merch_data = await get_merchant_context(m_id, db_session)
    assert merch_data["name"] == "Tool Merchant"

    prev_actions = await get_previous_recovery_actions(tx_id, db_session)
    assert prev_actions["recovery_action_count"] == 0
