"""
ml/analysis/root_cause.py
=========================
Deterministic, data-driven root-cause analysis for payment failures.

Algorithm
---------
1. Compute baseline failure rate per (bank, payment_method) over the full
   historical window.
2. Compute recent failure rate over a configurable recent window (hours).
3. If recent_rate / baseline_rate >= threshold AND absolute increase >= min_delta,
   flag as anomaly.
4. Identify the dominant failure reason driving the increase.
5. Return a structured diagnosis.

NO LLM is used. Results are purely statistical.
All results are clearly labeled as EXPERIMENTAL / synthetic data.
"""
from __future__ import annotations

import math
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Anomaly thresholds
DEFAULT_RATE_RATIO_THRESHOLD = 1.8   # recent rate must be >= 1.8x baseline
DEFAULT_MIN_DELTA = 0.03             # absolute rate increase must be >= 3%
DEFAULT_MIN_RECENT_SAMPLES = 5       # minimum events to declare an anomaly
DEFAULT_RECENT_WINDOW_HOURS = 6      # how far back "recent" means


class RootCauseAnalyzer:
    """
    Analyzes payment attempt data to identify likely root causes of
    elevated failure rates. Fully deterministic — no LLM involved.
    """

    def __init__(
        self,
        rate_ratio_threshold: float = DEFAULT_RATE_RATIO_THRESHOLD,
        min_delta: float = DEFAULT_MIN_DELTA,
        min_recent_samples: int = DEFAULT_MIN_RECENT_SAMPLES,
        recent_window_hours: int = DEFAULT_RECENT_WINDOW_HOURS,
    ):
        self.rate_ratio_threshold = rate_ratio_threshold
        self.min_delta = min_delta
        self.min_recent_samples = min_recent_samples
        self.recent_window_hours = recent_window_hours

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_transaction(
        self,
        transaction_id: str,
        attempts: list[dict],
        all_attempts: list[dict],
        reference_time: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Analyze root cause for a specific failed transaction.

        Parameters
        ----------
        transaction_id : str
        attempts : list[dict]
            Payment attempts for THIS transaction.
        all_attempts : list[dict]
            Full historical payment attempts (for baseline computation).
        reference_time : datetime, optional
            The point in time relative to which 'recent' is defined.
            Defaults to the latest attempt time.
        """
        if not attempts:
            return self._no_data_result(transaction_id)

        attempts_df = self._to_df(all_attempts)
        if attempts_df.empty:
            return self._no_data_result(transaction_id)

        # Determine the last failed attempt context
        this_attempts = [a for a in attempts if a.get("status") == "FAILED"]
        if not this_attempts:
            return {
                "transaction_id": transaction_id,
                "root_cause": "NO_FAILURE_DETECTED",
                "confidence": 1.0,
                "evidence": ["All attempts for this transaction succeeded"],
                "note": "EXPERIMENTAL — synthetic data only",
            }

        last_attempt = max(this_attempts, key=lambda a: a.get("attempt_number", 0))
        bank = last_attempt.get("bank", "UNKNOWN")
        method = last_attempt.get("payment_method", "UNKNOWN")
        failure_reason = last_attempt.get("failure_reason", "UNKNOWN")

        if reference_time is None:
            ref = pd.to_datetime(last_attempt.get("attempted_at"), utc=True)
        else:
            ref = pd.Timestamp(reference_time, tz="UTC") if reference_time.tzinfo is None else pd.Timestamp(reference_time)

        return self._diagnose(
            transaction_id=transaction_id,
            bank=bank,
            method=method,
            failure_reason=failure_reason,
            ref_time=ref,
            attempts_df=attempts_df,
        )

    def analyze_global(
        self,
        all_attempts: list[dict],
        reference_time: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """
        Scan all (bank, method) pairs and return a list of anomalies detected.
        Useful for a global health view.
        """
        attempts_df = self._to_df(all_attempts)
        if attempts_df.empty:
            return []

        dt = reference_time or datetime.now(timezone.utc)
        _ts = pd.Timestamp(dt)
        ref = _ts.tz_localize("UTC") if _ts.tzinfo is None else _ts.tz_convert("UTC")
        anomalies = []

        for (bank, method), group in attempts_df.groupby(["bank", "payment_method"]):
            baseline_rate = self._compute_failure_rate(group)
            recent_group = group[
                group["attempted_at"] >= ref - pd.Timedelta(hours=self.recent_window_hours)
            ]
            if len(recent_group) < self.min_recent_samples:
                continue
            recent_rate = self._compute_failure_rate(recent_group)

            if self._is_anomaly(baseline_rate, recent_rate):
                dominant_reason = self._dominant_failure_reason(recent_group)
                result = self._build_result(
                    transaction_id=None,
                    bank=bank,
                    method=method,
                    baseline_rate=baseline_rate,
                    recent_rate=recent_rate,
                    recent_count=len(recent_group),
                    dominant_reason=dominant_reason,
                    ref_time=ref,
                )
                anomalies.append(result)

        return anomalies

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _to_df(self, attempts: list[dict]) -> pd.DataFrame:
        if not attempts:
            return pd.DataFrame()
        df = pd.DataFrame(attempts)
        if "attempted_at" in df.columns:
            df["attempted_at"] = pd.to_datetime(df["attempted_at"], utc=True)
        return df

    def _compute_failure_rate(self, df: pd.DataFrame) -> float:
        if df.empty:
            return 0.0
        return float((df["status"] == "FAILED").sum() / len(df))

    def _is_anomaly(self, baseline: float, recent: float) -> bool:
        if baseline < 1e-9:  # avoid division by zero
            return recent > self.min_delta
        ratio = recent / baseline
        delta = recent - baseline
        return ratio >= self.rate_ratio_threshold and delta >= self.min_delta

    def _dominant_failure_reason(self, df: pd.DataFrame) -> str:
        failed = df[df["status"] == "FAILED"]
        if failed.empty or "failure_reason" not in failed.columns:
            return "UNKNOWN"
        counts = failed["failure_reason"].value_counts()
        return str(counts.index[0]) if not counts.empty else "UNKNOWN"

    def _compute_confidence(self, baseline: float, recent: float, n: int) -> float:
        """
        Heuristic confidence: higher when ratio is larger and sample is bigger.
        Capped at 0.99. Not a formal p-value.
        """
        if baseline < 1e-9:
            ratio = 10.0
        else:
            ratio = recent / baseline
        sample_factor = min(math.log1p(n) / math.log1p(50), 1.0)
        ratio_factor = min((ratio - 1.0) / 4.0, 1.0)
        confidence = 0.5 + 0.49 * ratio_factor * sample_factor
        return round(min(confidence, 0.99), 3)

    def _diagnose(
        self,
        transaction_id: str,
        bank: str,
        method: str,
        failure_reason: str,
        ref_time: pd.Timestamp,
        attempts_df: pd.DataFrame,
    ) -> dict[str, Any]:
        # Filter to same bank+method
        group = attempts_df[
            (attempts_df["bank"] == bank) &
            (attempts_df["payment_method"] == method)
        ]
        baseline_rate = self._compute_failure_rate(group)

        recent_group = group[
            group["attempted_at"] >= ref_time - pd.Timedelta(hours=self.recent_window_hours)
        ]
        recent_rate = self._compute_failure_rate(recent_group) if len(recent_group) >= 2 else baseline_rate
        recent_count = len(recent_group)
        dominant_reason = self._dominant_failure_reason(recent_group) if not recent_group.empty else failure_reason

        is_anomaly = self._is_anomaly(baseline_rate, recent_rate) and recent_count >= self.min_recent_samples

        return self._build_result(
            transaction_id=transaction_id,
            bank=bank,
            method=method,
            baseline_rate=baseline_rate,
            recent_rate=recent_rate,
            recent_count=recent_count,
            dominant_reason=dominant_reason,
            ref_time=ref_time,
            is_anomaly=is_anomaly,
            failure_reason=failure_reason,
        )

    def _build_result(
        self,
        transaction_id: str | None,
        bank: str,
        method: str,
        baseline_rate: float,
        recent_rate: float,
        recent_count: int,
        dominant_reason: str,
        ref_time: pd.Timestamp,
        is_anomaly: bool = True,
        failure_reason: str = "UNKNOWN",
    ) -> dict[str, Any]:
        rate_ratio = recent_rate / max(baseline_rate, 1e-9)

        if is_anomaly:
            root_cause = "TEMPORARY_BANK_DEGRADATION"
            if dominant_reason == "INSUFFICIENT_FUNDS":
                root_cause = "CUSTOMER_BALANCE_ISSUE"
            elif dominant_reason == "AUTHENTICATION_FAILED":
                root_cause = "AUTHENTICATION_DEGRADATION"
            elif dominant_reason == "BANK_DECLINED":
                root_cause = "BANK_POLICY_CHANGE"

            confidence = self._compute_confidence(baseline_rate, recent_rate, recent_count)
            evidence = [
                f"Recent {dominant_reason} rate is {rate_ratio:.1f}x above baseline for {bank}/{method}",
                f"Baseline failure rate: {baseline_rate:.1%}, recent rate: {recent_rate:.1%}",
                f"Observed over {recent_count} recent attempts in the last {self.recent_window_hours}h",
                f"Dominant failure type: {dominant_reason}",
            ]
        else:
            root_cause = "ISOLATED_TRANSACTION_FAILURE"
            confidence = 0.60
            evidence = [
                f"No significant elevation in {bank}/{method} failure rate detected",
                f"Baseline failure rate: {baseline_rate:.1%}",
                f"Failure reason: {failure_reason}",
                "Likely an isolated failure rather than a systemic issue",
            ]

        result: dict[str, Any] = {
            "root_cause": root_cause,
            "confidence": confidence,
            "affected_bank": bank,
            "affected_method": method,
            "baseline_failure_rate": round(baseline_rate, 4),
            "recent_failure_rate": round(recent_rate, 4),
            "rate_ratio": round(rate_ratio, 2),
            "recent_window_hours": self.recent_window_hours,
            "evidence": evidence,
            "note": "EXPERIMENTAL — synthetic data only. Not real-world performance.",
        }
        if transaction_id is not None:
            result["transaction_id"] = transaction_id
        return result

    def _no_data_result(self, transaction_id: str) -> dict[str, Any]:
        return {
            "transaction_id": transaction_id,
            "root_cause": "INSUFFICIENT_DATA",
            "confidence": 0.0,
            "evidence": ["No payment attempt data available for analysis"],
            "note": "EXPERIMENTAL — synthetic data only",
        }
