"""
tests/test_recovery_api.py
Integration tests for Phase 4 agent and recovery API endpoints.
"""
import pytest
import pytest_asyncio


@pytest.mark.asyncio
async def test_agent_analyze_endpoint(async_client):
    # Setup merchant, customer, transaction
    m = await async_client.post("/api/v1/merchants", json={"name": "API Agent Merchant"})
    m_id = m.json()["id"]

    c = await async_client.post("/api/v1/customers", json={
        "merchant_id": m_id, "external_customer_id": "C-API-AGENT-1", "name": "API Agent User"
    })
    c_id = c.json()["id"]

    tx = await async_client.post("/api/v1/transactions", json={
        "merchant_id": m_id, "customer_id": c_id,
        "external_transaction_id": "TX-API-AGENT-1", "amount": "4000.00"
    })
    tx_id = tx.json()["id"]

    resp = await async_client.post(f"/api/v1/agent/analyze/{tx_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "agent_decision" in data
    assert "policy_outcome" in data
    assert data["policy_outcome"] in ("ALLOW", "BLOCK", "HUMAN_APPROVAL")


@pytest.mark.asyncio
async def test_policy_check_endpoint(async_client):
    m = await async_client.post("/api/v1/merchants", json={"name": "Policy Merchant"})
    m_id = m.json()["id"]
    c = await async_client.post("/api/v1/customers", json={"merchant_id": m_id, "external_customer_id": "C-POL-1", "name": "Pol User"})
    c_id = c.json()["id"]
    tx = await async_client.post("/api/v1/transactions", json={"merchant_id": m_id, "customer_id": c_id, "external_transaction_id": "TX-POL-1", "amount": "2500.00"})
    tx_id = tx.json()["id"]

    resp = await async_client.post(
        f"/api/v1/recovery/policy-check/{tx_id}",
        json={
            "action": "RETRY_AFTER_DELAY",
            "delay_minutes": 20,
            "confidence": 0.9,
            "reason": "Test check",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["outcome"] == "ALLOW"


@pytest.mark.asyncio
async def test_execute_recovery_endpoint(async_client):
    m = await async_client.post("/api/v1/merchants", json={"name": "Exec API Merchant"})
    m_id = m.json()["id"]
    c = await async_client.post("/api/v1/customers", json={"merchant_id": m_id, "external_customer_id": "C-EXEC-API-1", "name": "Exec API User"})
    c_id = c.json()["id"]
    tx = await async_client.post("/api/v1/transactions", json={"merchant_id": m_id, "customer_id": c_id, "external_transaction_id": "TX-EXEC-API-1", "amount": "3500.00"})
    tx_id = tx.json()["id"]

    resp = await async_client.post(f"/api/v1/recovery/execute/{tx_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "recovery_action_id" in data
    assert "status" in data

    ra_id = data["recovery_action_id"]

    # Test recovery status endpoint
    status_resp = await async_client.get(f"/api/v1/recovery/{ra_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["recovery_action_id"] == ra_id

    # Test audit trail endpoint
    audit_resp = await async_client.get(f"/api/v1/transactions/{tx_id}/audit")
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()
    assert audit_data["audit_count"] >= 2
