"""
tests/test_dashboard_api.py
Integration tests for dashboard summary, trends, failure breakdown, and demo endpoints.
"""
import pytest
import pytest_asyncio


@pytest.mark.asyncio
async def test_dashboard_summary_endpoint(async_client):
    resp = await async_client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "revenue_at_risk" in data
    assert "recovered_revenue" in data
    assert "recovery_rate" in data
    assert "failed_transactions" in data


@pytest.mark.asyncio
async def test_dashboard_recovery_trends_endpoint(async_client):
    resp = await async_client.get("/api/v1/dashboard/recovery-trends?days=7")
    assert resp.status_code == 200
    data = resp.json()
    assert data["timeframe_days"] == 7
    assert len(data["trends"]) == 7


@pytest.mark.asyncio
async def test_dashboard_failure_breakdown_endpoint(async_client):
    resp = await async_client.get("/api/v1/dashboard/failure-breakdown")
    assert resp.status_code == 200
    data = resp.json()
    assert "by_bank" in data
    assert "by_method" in data


@pytest.mark.asyncio
async def test_dashboard_demo_run_endpoint(async_client):
    resp = await async_client.post("/api/v1/dashboard/demo-run")
    assert resp.status_code == 200
    data = resp.json()
    assert "transaction_id" in data
    assert "agent_action" in data
    assert "policy_outcome" in data
    assert data["status"] in ("ENQUEUED", "COMPLETED", "APPROVED")
