"""
tests/test_api_domain.py
Tests for the Milestone 2 REST API endpoints.
"""
import pytest
from decimal import Decimal


@pytest.mark.asyncio
async def test_create_merchant(async_client):
    response = await async_client.post(
        "/api/v1/merchants",
        json={"name": "Acme Corp", "is_active": True},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Corp"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_customer(async_client):
    # Create merchant first
    merchant_resp = await async_client.post(
        "/api/v1/merchants",
        json={"name": "Merchant A"},
    )
    assert merchant_resp.status_code == 201
    merchant_id = merchant_resp.json()["id"]

    # Create customer
    response = await async_client.post(
        "/api/v1/customers",
        json={
            "merchant_id": merchant_id,
            "external_customer_id": "EXT-C-001",
            "name": "Alice Smith",
            "email": "alice@example.com",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["merchant_id"] == merchant_id
    assert data["name"] == "Alice Smith"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_customer_nonexistent_merchant(async_client):
    response = await async_client.post(
        "/api/v1/customers",
        json={
            "merchant_id": "00000000-0000-0000-0000-000000000000",
            "external_customer_id": "EXT-999",
            "name": "Ghost Customer",
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_transaction(async_client):
    # Setup merchant + customer
    m = await async_client.post("/api/v1/merchants", json={"name": "TxMerchant"})
    merchant_id = m.json()["id"]

    c = await async_client.post(
        "/api/v1/customers",
        json={
            "merchant_id": merchant_id,
            "external_customer_id": "EXT-TX-001",
            "name": "Bob Jones",
        },
    )
    customer_id = c.json()["id"]

    response = await async_client.post(
        "/api/v1/transactions",
        json={
            "merchant_id": merchant_id,
            "customer_id": customer_id,
            "external_transaction_id": "TXN-00001",
            "amount": "1500.00",
            "currency": "INR",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["merchant_id"] == merchant_id
    assert data["customer_id"] == customer_id
    assert data["status"] == "CREATED"
    assert float(data["amount"]) == 1500.0


@pytest.mark.asyncio
async def test_get_transaction(async_client):
    m = await async_client.post("/api/v1/merchants", json={"name": "GetMerchant"})
    merchant_id = m.json()["id"]
    c = await async_client.post(
        "/api/v1/customers",
        json={
            "merchant_id": merchant_id,
            "external_customer_id": "EXT-GET-001",
            "name": "Carol",
        },
    )
    customer_id = c.json()["id"]
    tx = await async_client.post(
        "/api/v1/transactions",
        json={
            "merchant_id": merchant_id,
            "customer_id": customer_id,
            "external_transaction_id": "TXN-GET-001",
            "amount": "750.00",
        },
    )
    tx_id = tx.json()["id"]

    get_resp = await async_client.get(f"/api/v1/transactions/{tx_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == tx_id


@pytest.mark.asyncio
async def test_get_transaction_not_found(async_client):
    resp = await async_client.get("/api/v1/transactions/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_transaction_attempts_empty(async_client):
    m = await async_client.post("/api/v1/merchants", json={"name": "AttemptMerchant"})
    merchant_id = m.json()["id"]
    c = await async_client.post(
        "/api/v1/customers",
        json={
            "merchant_id": merchant_id,
            "external_customer_id": "EXT-ATT-001",
            "name": "Dave",
        },
    )
    customer_id = c.json()["id"]
    tx = await async_client.post(
        "/api/v1/transactions",
        json={
            "merchant_id": merchant_id,
            "customer_id": customer_id,
            "external_transaction_id": "TXN-ATT-001",
            "amount": "200.00",
        },
    )
    tx_id = tx.json()["id"]

    resp = await async_client.get(f"/api/v1/transactions/{tx_id}/attempts")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_recovery_actions_empty(async_client):
    m = await async_client.post("/api/v1/merchants", json={"name": "RAMerchant"})
    merchant_id = m.json()["id"]
    c = await async_client.post(
        "/api/v1/customers",
        json={
            "merchant_id": merchant_id,
            "external_customer_id": "EXT-RA-001",
            "name": "Eve",
        },
    )
    customer_id = c.json()["id"]
    tx = await async_client.post(
        "/api/v1/transactions",
        json={
            "merchant_id": merchant_id,
            "customer_id": customer_id,
            "external_transaction_id": "TXN-RA-001",
            "amount": "300.00",
        },
    )
    tx_id = tx.json()["id"]

    resp = await async_client.get(f"/api/v1/transactions/{tx_id}/recovery-actions")
    assert resp.status_code == 200
    assert resp.json() == []
