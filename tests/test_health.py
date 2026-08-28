import pytest
from unittest.mock import patch


@pytest.mark.asyncio
async def test_root_endpoint(async_client):
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Welcome to PayResQ API"
    assert "health" in data


@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "environment" in data
    assert "services" in data
    assert "database" in data["services"]
    assert "redis" in data["services"]


@pytest.mark.asyncio
async def test_api_v1_health_endpoint(async_client):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@pytest.mark.asyncio
async def test_health_degraded_when_service_fails(async_client):
    with patch("app.api.v1.health.check_db_health", return_value=False), \
         patch("app.api.v1.health.check_redis_health", return_value=True):
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["database"] is False
        assert data["services"]["redis"] is True
