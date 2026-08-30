"""
app/schemas/intelligence.py
============================
Pydantic schemas for the intelligence API endpoints.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class RecoveryPredictRequest(BaseModel):
    transaction_id: str


class RecoveryPredictions(BaseModel):
    RETRY_NOW: float
    RETRY_AFTER_DELAY: float
    SEND_PAYMENT_LINK: float
    CHANGE_PAYMENT_METHOD: float


class RecoveryPredictResponse(BaseModel):
    transaction_id: str
    predictions: dict[str, float]
    recommended_action: str
    model_version: str
    timestamp: str
    note: str


class RootCauseResponse(BaseModel):
    transaction_id: str
    root_cause: str
    confidence: float
    affected_bank: str
    affected_method: str
    baseline_failure_rate: float
    recent_failure_rate: float
    rate_ratio: float
    evidence: list[str]
    note: str


class ModelInfoResponse(BaseModel):
    model_version: str
    training_timestamp: Optional[str] = None
    feature_count: int
    feature_columns: list[str]
    training_rows: Optional[int] = None
    test_rows: Optional[int] = None
    evaluation: dict[str, Any] = {}
    note: str
