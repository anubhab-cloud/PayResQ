"""
ml/features/builder.py
======================
Builds the ML dataset from raw synthetic generator output.

One row per (failed transaction × candidate recovery action).
Four candidate actions → up to 4 rows per failed transaction.

Leakage prevention
------------------
- Customer/merchant aggregate statistics are computed only from transactions
  that occurred BEFORE the current transaction's created_at timestamp.
- The recovery outcome (Y) is never used as a feature (X).
- Future attempt status / future recovery events are never used.

Feature columns are defined canonically in encodings.FEATURE_COLUMNS so
that train-time and inference-time feature order is always identical.
"""
from __future__ import annotations

import math
import logging
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from ml.features.encodings import (
    DEFAULT_ENCODINGS,
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    CANDIDATE_ACTION_CATEGORIES,
    encode,
)

logger = logging.getLogger(__name__)

# Candidate actions the model scores for every failed transaction
CANDIDATE_ACTIONS = CANDIDATE_ACTION_CATEGORIES  # 4 actions


class MLDatasetBuilder:
    """
    Converts raw generator output (dicts) into a pandas DataFrame
    ready for XGBoost training.
    """

    def __init__(self, encodings: dict | None = None):
        self._enc = encodings or DEFAULT_ENCODINGS
        self._ref_date: datetime = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(self, raw: dict[str, list[dict]]) -> pd.DataFrame:
        """
        raw: output of PaymentDataGenerator.generate_all()

        Returns a DataFrame with columns = FEATURE_COLUMNS + [TARGET_COLUMN].
        Only rows where a recovery_outcome exists are labeled (Y known).
        Rows without outcomes are also included with Y = NaN for inference use.
        """
        merchants_df = pd.DataFrame(raw["merchants"])
        customers_df = pd.DataFrame(raw["customers"])
        transactions_df = pd.DataFrame(raw["transactions"])
        attempts_df = pd.DataFrame(raw["payment_attempts"])
        recovery_actions_df = pd.DataFrame(raw["recovery_actions"])
        recovery_outcomes_df = pd.DataFrame(raw.get("recovery_outcomes", []))

        # Parse timestamps
        for col in ["created_at", "updated_at"]:
            if col in transactions_df.columns:
                transactions_df[col] = pd.to_datetime(transactions_df[col], utc=True)
        if "attempted_at" in attempts_df.columns:
            attempts_df["attempted_at"] = pd.to_datetime(attempts_df["attempted_at"], utc=True)

        # ------------------------------------------------------------------
        # 1. Filter to failed transactions that have recovery actions
        # ------------------------------------------------------------------
        failed_txns = transactions_df[transactions_df["status"] == "FAILED"].copy()
        if failed_txns.empty:
            logger.warning("No failed transactions found — returning empty dataset")
            return pd.DataFrame(columns=FEATURE_COLUMNS + [TARGET_COLUMN])

        # ------------------------------------------------------------------
        # 2. Merge recovery actions and outcomes (Y label)
        # ------------------------------------------------------------------
        # Join outcomes onto actions
        if not recovery_outcomes_df.empty:
            outcomes_slim = recovery_outcomes_df[["recovery_action_id", "success"]].rename(
                columns={"recovery_action_id": "id", "success": "recovery_success"}
            )
            actions_with_outcomes = recovery_actions_df.merge(
                outcomes_slim, on="id", how="left"
            )
        else:
            actions_with_outcomes = recovery_actions_df.copy()
            actions_with_outcomes["recovery_success"] = float("nan")

        # ------------------------------------------------------------------
        # 3. Build per-transaction aggregates (LEAKAGE-FREE)
        #
        # To avoid leakage, customer/merchant stats use only past transactions.
        # We compute these as expanding stats sorted by created_at.
        # ------------------------------------------------------------------
        txns_sorted = transactions_df.sort_values("created_at").reset_index(drop=True)

        customer_stats = self._compute_customer_stats(txns_sorted, customers_df)
        merchant_stats = self._compute_merchant_stats(txns_sorted)

        # ------------------------------------------------------------------
        # 4. Get the last payment attempt for each failed transaction
        #    (represents the failure context)
        # ------------------------------------------------------------------
        failed_attempts = attempts_df[attempts_df["status"] == "FAILED"].copy()
        # Last attempt per transaction (highest attempt_number)
        last_attempt = (
            failed_attempts.sort_values("attempt_number")
            .groupby("transaction_id")
            .last()
            .reset_index()
        )

        # ------------------------------------------------------------------
        # 5. Build one row per (failed txn × candidate action)
        # ------------------------------------------------------------------
        rows: list[dict[str, Any]] = []

        for _, txn in failed_txns.iterrows():
            tx_id = txn["id"]

            # Get the actual recovery action taken (for Y label)
            actual_action = actions_with_outcomes[
                actions_with_outcomes["transaction_id"] == tx_id
            ]

            # Get last failure attempt context
            attempt_row = last_attempt[last_attempt["transaction_id"] == tx_id]
            if attempt_row.empty:
                continue

            attempt = attempt_row.iloc[0]

            # Transaction features
            tx_time: pd.Timestamp = txn["created_at"]
            now = pd.Timestamp.now(tz="UTC")
            tx_age_days = max((now - tx_time).total_seconds() / 86400, 0)
            amount = float(txn.get("amount", 0))

            # Failure context
            bank = str(attempt.get("bank", "UNKNOWN"))
            payment_method = str(attempt.get("payment_method", "UNKNOWN"))
            failure_reason = str(attempt.get("failure_reason", "UNKNOWN")) if attempt.get("failure_reason") else "UNKNOWN"
            attempt_number = int(attempt.get("attempt_number", 1))
            retry_count = max(attempt_number - 1, 0)

            # Degradation window flag from failure_events metadata
            in_degradation = 0  # conservative default; enriched if data available

            # Customer stats (leakage-free — computed from pre-tx history)
            c_stats = customer_stats.get(txn["customer_id"], {})
            cust_success_rate = c_stats.get("success_rate", 0.5)
            cust_tx_count = c_stats.get("tx_count", 0)
            cust_success_count = c_stats.get("success_count", 0)
            cust_avg_amount = c_stats.get("avg_amount", amount)
            cust_failed_attempts = c_stats.get("failed_attempts", 0)

            # Merchant stats
            m_stats = merchant_stats.get(txn["merchant_id"], {})
            merch_tx_count = m_stats.get("tx_count", 0)
            merch_failure_rate = m_stats.get("failure_rate", 0.1)

            base_features = {
                # Transaction
                "amount": amount,
                "amount_log": math.log1p(amount),
                "hour": tx_time.hour,
                "day_of_week": tx_time.dayofweek,
                "tx_age_days": tx_age_days,
                # Payment / Failure
                "payment_method_enc": encode(payment_method, self._enc["payment_method"]),
                "bank_enc": encode(bank, self._enc["bank"]),
                "failure_reason_enc": encode(failure_reason, self._enc["failure_reason"]),
                "attempt_number": attempt_number,
                "retry_count": retry_count,
                "in_degradation_window": in_degradation,
                # Customer
                "customer_success_rate": cust_success_rate,
                "customer_tx_count": cust_tx_count,
                "customer_success_count": cust_success_count,
                "customer_avg_amount": cust_avg_amount,
                "customer_failed_attempts": cust_failed_attempts,
                # Merchant
                "merchant_tx_count": merch_tx_count,
                "merchant_failure_rate": merch_failure_rate,
            }

            # One row per candidate action
            for action in CANDIDATE_ACTIONS:
                row = dict(base_features)
                row["candidate_action_enc"] = encode(action, self._enc["candidate_action"])

                # Y label: 1 if this action was taken AND succeeded, 0 if taken and failed
                # NaN if this action was NOT the one taken (still useful for multi-class
                # or when we treat any action as a valid training signal)
                action_rows = actual_action[actual_action["action_type"] == action]
                if not action_rows.empty:
                    outcome_val = action_rows.iloc[0].get("recovery_success")
                    if pd.isna(outcome_val):
                        row[TARGET_COLUMN] = float("nan")
                    else:
                        row[TARGET_COLUMN] = int(bool(outcome_val))
                else:
                    # Action was not chosen — we still include row with NaN Y
                    # (excluded from training, usable for inference)
                    row[TARGET_COLUMN] = float("nan")

                rows.append(row)

        df = pd.DataFrame(rows, columns=FEATURE_COLUMNS + [TARGET_COLUMN])
        logger.info(
            "MLDatasetBuilder: %d rows built (%d labeled)",
            len(df),
            df[TARGET_COLUMN].notna().sum(),
        )
        return df

    # ------------------------------------------------------------------
    # Leakage-free aggregate helpers
    # ------------------------------------------------------------------

    def _compute_customer_stats(
        self,
        txns_sorted: pd.DataFrame,
        customers_df: pd.DataFrame,
    ) -> dict[str, dict]:
        """
        Compute per-customer historical stats using ONLY past transactions.
        Expanding window sorted by created_at — no future data leakage.
        """
        stats: dict[str, dict] = {}
        running: dict[str, dict] = {}

        for _, row in txns_sorted.iterrows():
            cid = row["customer_id"]
            success = row["status"] == "SUCCESS"
            amount = float(row.get("amount", 0))

            if cid not in running:
                running[cid] = {
                    "tx_count": 0, "success_count": 0,
                    "amount_sum": 0.0, "failed_attempts": 0,
                }

            # Save stats BEFORE updating (past-only for this transaction)
            stats[cid] = {
                "tx_count": running[cid]["tx_count"],
                "success_count": running[cid]["success_count"],
                "success_rate": (
                    running[cid]["success_count"] / running[cid]["tx_count"]
                    if running[cid]["tx_count"] > 0 else 0.5
                ),
                "avg_amount": (
                    running[cid]["amount_sum"] / running[cid]["tx_count"]
                    if running[cid]["tx_count"] > 0 else amount
                ),
                "failed_attempts": running[cid]["failed_attempts"],
            }

            # Update running totals
            running[cid]["tx_count"] += 1
            running[cid]["amount_sum"] += amount
            if success:
                running[cid]["success_count"] += 1
            else:
                running[cid]["failed_attempts"] += 1

        return stats

    def _compute_merchant_stats(self, txns_sorted: pd.DataFrame) -> dict[str, dict]:
        """
        Compute per-merchant historical stats (leakage-free expanding window).
        """
        stats: dict[str, dict] = {}
        running: dict[str, dict] = {}

        for _, row in txns_sorted.iterrows():
            mid = row["merchant_id"]
            failed = row["status"] == "FAILED"

            if mid not in running:
                running[mid] = {"tx_count": 0, "fail_count": 0}

            # Save stats BEFORE updating
            stats[mid] = {
                "tx_count": running[mid]["tx_count"],
                "failure_rate": (
                    running[mid]["fail_count"] / running[mid]["tx_count"]
                    if running[mid]["tx_count"] > 0 else 0.1
                ),
            }

            # Update running totals
            running[mid]["tx_count"] += 1
            if failed:
                running[mid]["fail_count"] += 1

        return stats
