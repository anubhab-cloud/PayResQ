"""
tests/test_intelligence_api.py
Tests for intelligence API endpoints.
Uses a pre-trained mini model via fixture — does not retrain per test.
"""
import json
import pytest
import pytest_asyncio
import tempfile
import numpy as np
from pathlib import Path

from ml.features.encodings import (
    DEFAULT_ENCODINGS, FEATURE_COLUMNS, TARGET_COLUMN,
    save_encodings,
)
from ml.services.prediction_service import RecoveryPredictionService


# -----------------------------------------------------------------------
# Mini model fixture (trained once per session)
# -----------------------------------------------------------------------

@pytest.fixture(scope="module")
def trained_model_dir():
    """Train a tiny XGBoost model and return the artifacts directory."""
    import xgboost as xgb
    from ml.data.generators.payment_generator import PaymentDataGenerator
    from ml.features.builder import MLDatasetBuilder

    gen = PaymentDataGenerator(seed=42)
    raw = gen.generate_all(n_merchants=3, n_customers=50, n_transactions=1000)
    builder = MLDatasetBuilder(encodings=DEFAULT_ENCODINGS)
    df = builder.build(raw)
    df_labeled = df.dropna(subset=[TARGET_COLUMN]).copy()
    df_labeled[TARGET_COLUMN] = df_labeled[TARGET_COLUMN].astype(int)

    if len(df_labeled) < 10:
        pytest.skip("Not enough labeled rows")

    X = df_labeled[FEATURE_COLUMNS].values.astype(np.float32)
    y = df_labeled[TARGET_COLUMN].values.astype(int)

    model = xgb.XGBClassifier(
        n_estimators=10, max_depth=3, random_state=42,
        eval_metric="logloss"
    )
    model.fit(X, y)

    tmp = tempfile.mkdtemp()
    tmp_path = Path(tmp)
    model_path = tmp_path / "recovery_model.json"
    enc_path = tmp_path / "encodings.json"
    meta_path = tmp_path / "metadata.json"

    model.save_model(str(model_path))
    enc_ser = {k: {str(kk): vv for kk, vv in v.items()} for k, v in DEFAULT_ENCODINGS.items()}
    save_encodings(enc_path, enc_ser)
    metadata = {
        "model_version": "test-1.0",
        "training_timestamp": "2026-01-01T00:00:00Z",
        "training_rows": len(X),
        "test_rows": 0,
        "feature_columns": FEATURE_COLUMNS,
    }
    with open(meta_path, "w") as f:
        json.dump(metadata, f)

    yield tmp_path


@pytest_asyncio.fixture(scope="function")
async def api_client_with_model(async_engine, trained_model_dir):
    """HTTP client with DB override AND model loaded from trained_model_dir."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    from app.core.db import get_db
    from app.main import app
    from ml.services.prediction_service import prediction_service
    from httpx import AsyncClient, ASGITransport

    TestSessionLocal = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async def override_get_db():
        async with TestSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    # Load test model
    prediction_service.load(
        model_path=trained_model_dir / "recovery_model.json",
        encodings_path=trained_model_dir / "encodings.json",
        metadata_path=trained_model_dir / "metadata.json",
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# -----------------------------------------------------------------------
# Helper: create a failed transaction in the test DB
# -----------------------------------------------------------------------

async def _create_failed_tx(client):
    m = await client.post("/api/v1/merchants", json={"name": "IntelMerchant"})
    merchant_id = m.json()["id"]
    c = await client.post("/api/v1/customers", json={
        "merchant_id": merchant_id,
        "external_customer_id": "INT-001",
        "name": "Test User",
    })
    customer_id = c.json()["id"]
    tx = await client.post("/api/v1/transactions", json={
        "merchant_id": merchant_id,
        "customer_id": customer_id,
        "external_transaction_id": "INT-TX-001",
        "amount": "2500.00",
    })
    return tx.json()["id"]


# -----------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_recovery_predict_endpoint(api_client_with_model):
    tx_id = await _create_failed_tx(api_client_with_model)
    resp = await api_client_with_model.post(
        "/api/v1/intelligence/recovery-predict",
        json={"transaction_id": tx_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "predictions" in data
    assert "recommended_action" in data
    assert "model_version" in data
    preds = data["predictions"]
    for action in ["RETRY_NOW", "RETRY_AFTER_DELAY", "SEND_PAYMENT_LINK", "CHANGE_PAYMENT_METHOD"]:
        assert action in preds
        assert 0.0 <= preds[action] <= 1.0


@pytest.mark.asyncio
async def test_recovery_predict_invalid_tx(api_client_with_model):
    resp = await api_client_with_model.post(
        "/api/v1/intelligence/recovery-predict",
        json={"transaction_id": "nonexistent-000"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_root_cause_endpoint(api_client_with_model):
    tx_id = await _create_failed_tx(api_client_with_model)
    # Need a unique tx for root cause (create a new one)
    m = await api_client_with_model.post("/api/v1/merchants", json={"name": "RCA_Merchant"})
    merchant_id = m.json()["id"]
    c = await api_client_with_model.post("/api/v1/customers", json={
        "merchant_id": merchant_id,
        "external_customer_id": "RCA-C-001",
        "name": "RCA User",
    })
    customer_id = c.json()["id"]
    tx2 = await api_client_with_model.post("/api/v1/transactions", json={
        "merchant_id": merchant_id,
        "customer_id": customer_id,
        "external_transaction_id": "RCA-TX-001",
        "amount": "1500.00",
    })
    tx_id2 = tx2.json()["id"]

    resp = await api_client_with_model.get(
        f"/api/v1/intelligence/root-cause/{tx_id2}"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "root_cause" in data
    assert "confidence" in data
    assert "evidence" in data
    assert "EXPERIMENTAL" in data.get("note", "")


@pytest.mark.asyncio
async def test_root_cause_invalid_tx(api_client_with_model):
    resp = await api_client_with_model.get(
        "/api/v1/intelligence/root-cause/does-not-exist"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_model_info_endpoint(api_client_with_model):
    resp = await api_client_with_model.get("/api/v1/intelligence/model-info")
    assert resp.status_code == 200
    data = resp.json()
    assert "model_version" in data
    assert "feature_count" in data
    assert data["feature_count"] > 0
    assert "feature_columns" in data
    assert len(data["feature_columns"]) > 0
