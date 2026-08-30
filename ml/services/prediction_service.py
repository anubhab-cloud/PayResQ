"""
ml/services/prediction_service.py
==================================
Recovery prediction service.

Loads the trained XGBoost model and encoding maps once at startup.
Never retrains. Provides predictions for all 4 candidate actions
given a transaction's feature context.
"""
from __future__ import annotations

import json
import logging
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent.parent / "models"
MODEL_PATH = MODEL_DIR / "recovery_model.json"
ENCODINGS_PATH = MODEL_DIR / "encodings.json"
METADATA_PATH = MODEL_DIR / "metadata.json"

CANDIDATE_ACTIONS = [
    "RETRY_NOW",
    "RETRY_AFTER_DELAY",
    "SEND_PAYMENT_LINK",
    "CHANGE_PAYMENT_METHOD",
]


class RecoveryPredictionService:
    """
    Singleton-style prediction service.
    Call load() once at app startup.
    """

    def __init__(self) -> None:
        self._model = None
        self._encodings: dict = {}
        self._metadata: dict = {}
        self._feature_columns: list[str] = []
        self._loaded = False

    def load(self, model_path: Path | None = None, encodings_path: Path | None = None, metadata_path: Path | None = None) -> None:
        """Load model + encodings + metadata from disk."""
        import xgboost as xgb
        from ml.features.encodings import FEATURE_COLUMNS

        mp = model_path or MODEL_PATH
        ep = encodings_path or ENCODINGS_PATH
        mtp = metadata_path or METADATA_PATH

        if not mp.exists():
            raise FileNotFoundError(
                f"Model artifact not found at {mp}. "
                "Run: python -m ml.train --transactions 75000 --seed 42"
            )

        self._model = xgb.XGBClassifier()
        self._model.load_model(str(mp))

        if ep.exists():
            with open(ep) as f:
                self._encodings = json.load(f)
        else:
            from ml.features.encodings import DEFAULT_ENCODINGS
            self._encodings = DEFAULT_ENCODINGS
            logger.warning("Encodings file not found; using defaults")

        if mtp.exists():
            with open(mtp) as f:
                self._metadata = json.load(f)

        self._feature_columns = FEATURE_COLUMNS
        self._loaded = True
        logger.info("RecoveryPredictionService loaded: %s", mp)

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def get_model_info(self) -> dict[str, Any]:
        if not self._loaded:
            return {"status": "model_not_loaded"}
        return {
            "model_version": self._metadata.get("model_version", "unknown"),
            "training_timestamp": self._metadata.get("training_timestamp"),
            "feature_count": len(self._feature_columns),
            "feature_columns": self._feature_columns,
            "training_rows": self._metadata.get("training_rows"),
            "test_rows": self._metadata.get("test_rows"),
            "evaluation": self._metadata.get("evaluation", {}),
            "note": "EXPERIMENTAL — synthetic data only",
        }

    def predict(self, transaction_context: dict[str, Any]) -> dict[str, Any]:
        """
        Predict recovery probability for all 4 candidate actions.

        transaction_context keys (all optional, defaults used if missing):
            amount, hour, day_of_week, tx_age_days,
            payment_method, bank, failure_reason,
            attempt_number, retry_count, in_degradation_window,
            customer_success_rate, customer_tx_count, customer_success_count,
            customer_avg_amount, customer_failed_attempts,
            merchant_tx_count, merchant_failure_rate
        """
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        from ml.features.encodings import encode

        enc = self._encodings
        amount = float(transaction_context.get("amount", 1000))
        hour = int(transaction_context.get("hour", 12))
        day_of_week = int(transaction_context.get("day_of_week", 1))
        tx_age_days = float(transaction_context.get("tx_age_days", 0))
        payment_method = str(transaction_context.get("payment_method", "UNKNOWN"))
        bank = str(transaction_context.get("bank", "UNKNOWN"))
        failure_reason = str(transaction_context.get("failure_reason", "UNKNOWN"))
        attempt_number = int(transaction_context.get("attempt_number", 1))
        retry_count = int(transaction_context.get("retry_count", 0))
        in_degradation = int(bool(transaction_context.get("in_degradation_window", False)))
        cust_success_rate = float(transaction_context.get("customer_success_rate", 0.5))
        cust_tx_count = int(transaction_context.get("customer_tx_count", 0))
        cust_success_count = int(transaction_context.get("customer_success_count", 0))
        cust_avg_amount = float(transaction_context.get("customer_avg_amount", amount))
        cust_failed_attempts = int(transaction_context.get("customer_failed_attempts", 0))
        merch_tx_count = int(transaction_context.get("merchant_tx_count", 0))
        merch_failure_rate = float(transaction_context.get("merchant_failure_rate", 0.1))

        predictions: dict[str, float] = {}
        rows = []

        for action in CANDIDATE_ACTIONS:
            row = [
                amount,
                math.log1p(amount),
                hour,
                day_of_week,
                tx_age_days,
                encode(payment_method, enc.get("payment_method", {})),
                encode(bank, enc.get("bank", {})),
                encode(failure_reason, enc.get("failure_reason", {})),
                attempt_number,
                retry_count,
                in_degradation,
                cust_success_rate,
                cust_tx_count,
                cust_success_count,
                cust_avg_amount,
                cust_failed_attempts,
                merch_tx_count,
                merch_failure_rate,
                encode(action, enc.get("candidate_action", {})),
            ]
            rows.append(row)

        X = np.array(rows, dtype=np.float32)
        proba = self._model.predict_proba(X)[:, 1]  # P(success)

        for action, prob in zip(CANDIDATE_ACTIONS, proba):
            predictions[action] = round(float(prob), 4)

        recommended = max(predictions, key=predictions.__getitem__)

        return {
            "predictions": predictions,
            "recommended_action": recommended,
            "model_version": self._metadata.get("model_version", "unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": "EXPERIMENTAL — synthetic data only",
        }


# Module-level singleton — loaded once at app startup
prediction_service = RecoveryPredictionService()
