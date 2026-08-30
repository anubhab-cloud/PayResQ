"""
ml/features/encodings.py
========================
Label encoding maps for categorical features.

Stored as plain dicts (str → int) so they can be serialised to JSON
and loaded identically at inference time — no sklearn LabelEncoder
dependency needed at inference.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Canonical category lists — order determines integer encoding.
# Adding new values must be done at the END to preserve backward compat.
BANK_CATEGORIES: list[str] = [
    "ICICI", "HDFC", "SBI", "AXIS", "KOTAK",
    "YES", "IDFC", "PAYTM", "PHONEPE", "UNKNOWN",
]

PAYMENT_METHOD_CATEGORIES: list[str] = [
    "CARD", "UPI", "NETBANKING", "WALLET",
]

FAILURE_REASON_CATEGORIES: list[str] = [
    "TIMEOUT", "BANK_DECLINED", "INSUFFICIENT_FUNDS",
    "NETWORK_ERROR", "AUTHENTICATION_FAILED", "UNKNOWN",
]

CANDIDATE_ACTION_CATEGORIES: list[str] = [
    "RETRY_NOW", "RETRY_AFTER_DELAY",
    "SEND_PAYMENT_LINK", "CHANGE_PAYMENT_METHOD",
]


def _make_map(categories: list[str]) -> dict[str, int]:
    return {v: i for i, v in enumerate(categories)}


# Default encoding maps (built at import time)
DEFAULT_ENCODINGS: dict[str, dict[str, int]] = {
    "bank": _make_map(BANK_CATEGORIES),
    "payment_method": _make_map(PAYMENT_METHOD_CATEGORIES),
    "failure_reason": _make_map(FAILURE_REASON_CATEGORIES),
    "candidate_action": _make_map(CANDIDATE_ACTION_CATEGORIES),
}


def encode(value: str, mapping: dict[str, int], default_key: str = "UNKNOWN") -> int:
    """Encode a categorical value; falls back to the 'UNKNOWN' entry."""
    return mapping.get(value, mapping.get(default_key, -1))


def save_encodings(path: Path, encodings: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(encodings, f, indent=2)


def load_encodings(path: Path) -> dict[str, Any]:
    with open(path) as f:
        return json.load(f)


# The canonical ML feature column order — must match builder output exactly.
FEATURE_COLUMNS: list[str] = [
    # Transaction
    "amount",
    "amount_log",
    "hour",
    "day_of_week",
    "tx_age_days",
    # Payment / Failure
    "payment_method_enc",
    "bank_enc",
    "failure_reason_enc",
    "attempt_number",
    "retry_count",
    "in_degradation_window",
    # Customer
    "customer_success_rate",
    "customer_tx_count",
    "customer_success_count",
    "customer_avg_amount",
    "customer_failed_attempts",
    # Merchant
    "merchant_tx_count",
    "merchant_failure_rate",
    # Candidate action
    "candidate_action_enc",
]

TARGET_COLUMN = "recovery_success"
