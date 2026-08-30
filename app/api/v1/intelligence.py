"""
app/api/v1/intelligence.py
===========================
Intelligence API endpoints.

POST /api/v1/intelligence/recovery-predict  — predict recovery probabilities
GET  /api/v1/intelligence/root-cause/{tx_id} — root-cause analysis
GET  /api/v1/intelligence/model-info          — model metadata
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db import get_db
from app.schemas.intelligence import (
    RecoveryPredictRequest,
    RecoveryPredictResponse,
    RootCauseResponse,
    ModelInfoResponse,
)
from app.services import transaction_service
from app.models.transaction import Transaction
from app.models.payment_attempt import PaymentAttempt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])

# -----------------------------------------------------------------------
# Lazy-load the prediction service and root cause analyzer
# (both are stateless after loading — safe to reuse across requests)
# -----------------------------------------------------------------------
def _get_prediction_service():
    from ml.services.prediction_service import prediction_service
    if not prediction_service.is_loaded:
        try:
            prediction_service.load()
        except FileNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Model not available: {e}",
            )
    return prediction_service


def _get_rca():
    from ml.analysis.root_cause import RootCauseAnalyzer
    return RootCauseAnalyzer()


# -----------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------

@router.post(
    "/recovery-predict",
    response_model=RecoveryPredictResponse,
    summary="Predict recovery probabilities for a failed transaction",
)
async def recovery_predict(
    request: RecoveryPredictRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Given a transaction ID, predicts the probability that each candidate
    recovery action will successfully recover the payment.

    NOTE: EXPERIMENTAL — synthetic data only.
    """
    tx = await transaction_service.get_transaction_by_id(db, request.transaction_id)
    if tx is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {request.transaction_id} not found",
        )

    # Build feature context from transaction + its last payment attempt
    attempts = await transaction_service.get_payment_attempts(db, request.transaction_id)
    failed_attempts = [a for a in attempts if a.status == "FAILED"]

    last_attempt = max(failed_attempts, key=lambda a: a.attempt_number) if failed_attempts else None

    tx_time = tx.created_at
    now = datetime.now(timezone.utc)
    if tx_time.tzinfo is None:
        from datetime import timezone as tz
        tx_time = tx_time.replace(tzinfo=tz.utc)
    tx_age_days = max((now - tx_time).total_seconds() / 86400, 0)

    context = {
        "amount": float(tx.amount),
        "hour": tx_time.hour,
        "day_of_week": tx_time.weekday(),
        "tx_age_days": tx_age_days,
        "payment_method": last_attempt.payment_method if last_attempt else "UNKNOWN",
        "bank": last_attempt.bank if last_attempt else "UNKNOWN",
        "failure_reason": (last_attempt.failure_reason or "UNKNOWN") if last_attempt else "UNKNOWN",
        "attempt_number": last_attempt.attempt_number if last_attempt else 1,
        "retry_count": max((last_attempt.attempt_number - 1), 0) if last_attempt else 0,
        "in_degradation_window": False,
        # Customer/merchant context — defaults used if not available
        "customer_success_rate": 0.5,
        "customer_tx_count": 0,
        "customer_success_count": 0,
        "customer_avg_amount": float(tx.amount),
        "customer_failed_attempts": len(failed_attempts),
        "merchant_tx_count": 0,
        "merchant_failure_rate": 0.1,
    }

    svc = _get_prediction_service()
    result = svc.predict(context)

    return RecoveryPredictResponse(
        transaction_id=request.transaction_id,
        predictions=result["predictions"],
        recommended_action=result["recommended_action"],
        model_version=result["model_version"],
        timestamp=result["timestamp"],
        note=result["note"],
    )


@router.get(
    "/root-cause/{transaction_id}",
    response_model=RootCauseResponse,
    summary="Root-cause analysis for a failed transaction",
)
async def root_cause(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a data-driven root-cause diagnosis for a failed transaction.
    Fully deterministic — no LLM.

    NOTE: EXPERIMENTAL — synthetic data only.
    """
    tx = await transaction_service.get_transaction_by_id(db, transaction_id)
    if tx is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found",
        )

    # Fetch this transaction's attempts
    attempts = await transaction_service.get_payment_attempts(db, transaction_id)
    attempts_dicts = [
        {
            "id": a.id,
            "transaction_id": a.transaction_id,
            "attempt_number": a.attempt_number,
            "payment_method": a.payment_method,
            "bank": a.bank,
            "status": a.status,
            "failure_reason": a.failure_reason,
            "attempted_at": a.attempted_at,
        }
        for a in attempts
    ]

    # Fetch a broader set of recent attempts for baseline (last 500)
    result = await db.execute(
        select(PaymentAttempt).order_by(PaymentAttempt.attempted_at.desc()).limit(500)
    )
    all_attempts_objs = result.scalars().all()
    all_attempts_dicts = [
        {
            "id": a.id,
            "transaction_id": a.transaction_id,
            "attempt_number": a.attempt_number,
            "payment_method": a.payment_method,
            "bank": a.bank,
            "status": a.status,
            "failure_reason": a.failure_reason,
            "attempted_at": a.attempted_at,
        }
        for a in all_attempts_objs
    ]

    rca = _get_rca()
    diagnosis = rca.analyze_transaction(
        transaction_id=transaction_id,
        attempts=attempts_dicts,
        all_attempts=all_attempts_dicts,
    )

    return RootCauseResponse(
        transaction_id=transaction_id,
        root_cause=diagnosis.get("root_cause", "UNKNOWN"),
        confidence=diagnosis.get("confidence", 0.0),
        affected_bank=diagnosis.get("affected_bank", "UNKNOWN"),
        affected_method=diagnosis.get("affected_method", "UNKNOWN"),
        baseline_failure_rate=diagnosis.get("baseline_failure_rate", 0.0),
        recent_failure_rate=diagnosis.get("recent_failure_rate", 0.0),
        rate_ratio=diagnosis.get("rate_ratio", 1.0),
        evidence=diagnosis.get("evidence", []),
        note=diagnosis.get("note", "EXPERIMENTAL — synthetic data only"),
    )


@router.get(
    "/model-info",
    response_model=ModelInfoResponse,
    summary="Return model metadata and evaluation results",
)
async def model_info():
    """Returns the loaded model's metadata, version, and evaluation metrics."""
    svc = _get_prediction_service()
    info = svc.get_model_info()
    return ModelInfoResponse(
        model_version=str(info.get("model_version", "unknown")),
        training_timestamp=info.get("training_timestamp"),
        feature_count=int(info.get("feature_count", 0)),
        feature_columns=info.get("feature_columns", []),
        training_rows=info.get("training_rows"),
        test_rows=info.get("test_rows"),
        evaluation=info.get("evaluation", {}),
        note=str(info.get("note", "EXPERIMENTAL — synthetic data only")),
    )
