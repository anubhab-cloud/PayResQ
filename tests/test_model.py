"""
tests/test_model.py
Tests for XGBoost model training and prediction.
Uses a tiny dataset (1,000 transactions) — fast, no large training run needed.
"""
import json
import pytest
import tempfile
from pathlib import Path
import numpy as np

from ml.data.generators.payment_generator import PaymentDataGenerator
from ml.features.builder import MLDatasetBuilder
from ml.features.encodings import (
    DEFAULT_ENCODINGS, FEATURE_COLUMNS, TARGET_COLUMN,
    save_encodings, load_encodings,
)
from ml.services.prediction_service import RecoveryPredictionService, CANDIDATE_ACTIONS


def _train_mini_model(tmp_dir: Path):
    """Train a minimal model for testing — returns (model, metadata_path)."""
    import xgboost as xgb

    gen = PaymentDataGenerator(seed=42)
    raw = gen.generate_all(n_merchants=3, n_customers=50, n_transactions=1000)

    builder = MLDatasetBuilder(encodings=DEFAULT_ENCODINGS)
    df = builder.build(raw)
    df_labeled = df.dropna(subset=[TARGET_COLUMN]).copy()
    df_labeled[TARGET_COLUMN] = df_labeled[TARGET_COLUMN].astype(int)

    if len(df_labeled) < 10:
        pytest.skip("Not enough labeled rows in mini dataset")

    X = df_labeled[FEATURE_COLUMNS].values.astype(np.float32)
    y = df_labeled[TARGET_COLUMN].values.astype(int)

    model = xgb.XGBClassifier(
        n_estimators=10, max_depth=3, random_state=42,
        eval_metric="logloss"
    )
    model.fit(X, y)

    model_path = tmp_dir / "recovery_model.json"
    enc_path = tmp_dir / "encodings.json"
    meta_path = tmp_dir / "metadata.json"

    model.save_model(str(model_path))
    save_encodings(enc_path, {k: {str(kk): vv for kk, vv in v.items()} for k, v in DEFAULT_ENCODINGS.items()})

    metadata = {
        "model_version": "test-1.0",
        "training_timestamp": "2026-01-01T00:00:00Z",
        "training_rows": len(X),
        "test_rows": 0,
        "feature_columns": FEATURE_COLUMNS,
    }
    with open(meta_path, "w") as f:
        json.dump(metadata, f)

    return model, model_path, enc_path, meta_path


def test_model_trains_successfully():
    with tempfile.TemporaryDirectory() as tmp:
        model, model_path, enc_path, meta_path = _train_mini_model(Path(tmp))
        assert model_path.exists()
        assert enc_path.exists()
        assert meta_path.exists()


def test_predictions_in_range():
    with tempfile.TemporaryDirectory() as tmp:
        model, model_path, enc_path, meta_path = _train_mini_model(Path(tmp))

        svc = RecoveryPredictionService()
        svc.load(model_path=model_path, encodings_path=enc_path, metadata_path=meta_path)

        result = svc.predict({
            "amount": 2500.0,
            "hour": 14,
            "day_of_week": 2,
            "tx_age_days": 0.5,
            "payment_method": "UPI",
            "bank": "HDFC",
            "failure_reason": "TIMEOUT",
            "attempt_number": 1,
            "retry_count": 0,
            "in_degradation_window": False,
            "customer_success_rate": 0.85,
            "customer_tx_count": 10,
            "customer_success_count": 8,
            "customer_avg_amount": 2000.0,
            "customer_failed_attempts": 2,
            "merchant_tx_count": 500,
            "merchant_failure_rate": 0.08,
        })

        preds = result["predictions"]
        for action in CANDIDATE_ACTIONS:
            assert action in preds, f"Missing prediction for action: {action}"
            assert 0.0 <= preds[action] <= 1.0, \
                f"Prediction out of range for {action}: {preds[action]}"


def test_all_candidate_actions_scored():
    with tempfile.TemporaryDirectory() as tmp:
        model, model_path, enc_path, meta_path = _train_mini_model(Path(tmp))
        svc = RecoveryPredictionService()
        svc.load(model_path=model_path, encodings_path=enc_path, metadata_path=meta_path)

        result = svc.predict({"amount": 1000.0, "failure_reason": "NETWORK_ERROR"})
        preds = result["predictions"]
        assert len(preds) == 4
        for action in CANDIDATE_ACTIONS:
            assert action in preds


def test_recommended_action_is_highest_probability():
    with tempfile.TemporaryDirectory() as tmp:
        model, model_path, enc_path, meta_path = _train_mini_model(Path(tmp))
        svc = RecoveryPredictionService()
        svc.load(model_path=model_path, encodings_path=enc_path, metadata_path=meta_path)

        result = svc.predict({"amount": 5000.0})
        preds = result["predictions"]
        recommended = result["recommended_action"]
        assert preds[recommended] == max(preds.values())


def test_model_artifact_save_load():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        model, model_path, enc_path, meta_path = _train_mini_model(tmp_path)

        # Load fresh instance
        svc = RecoveryPredictionService()
        svc.load(model_path=model_path, encodings_path=enc_path, metadata_path=meta_path)

        assert svc.is_loaded
        info = svc.get_model_info()
        assert info["model_version"] == "test-1.0"
        assert info["feature_count"] == len(FEATURE_COLUMNS)


def test_encodings_save_load_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "enc.json"
        save_encodings(path, DEFAULT_ENCODINGS)
        loaded = load_encodings(path)
        for k in DEFAULT_ENCODINGS:
            assert k in loaded
