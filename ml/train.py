"""
ml/train.py
===========
Offline training script for the PayResQ recovery prediction model.

Usage
-----
    python -m ml.train [options]

Options
-------
    --transactions  INT   Number of synthetic transactions (default: 75000)
    --merchants     INT   Number of merchants (default: 20)
    --customers     INT   Number of customers (default: 2000)
    --seed          INT   Random seed (default: 42)
    --output-dir    STR   Directory for model artifacts (default: ml/models)

Training pipeline
-----------------
1. Generate synthetic data in-memory via PaymentDataGenerator
2. Build ML dataset via MLDatasetBuilder (one row per failed_txn x action)
3. Temporal train/test split (80/20 sorted by transaction created_at)
4. Train XGBoost binary classifier
5. Evaluate: ROC-AUC, Precision, Recall, F1, Log Loss + business metrics
6. Evaluate simple baseline (always RETRY_NOW)
7. Save model artifact, encodings, and metadata/evaluation to output-dir

EXPERIMENTAL: All results are based on synthetic data.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Repo root on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main() -> None:
    parser = argparse.ArgumentParser(description="PayResQ ML Training Script")
    parser.add_argument("--transactions", type=int, default=75000)
    parser.add_argument("--merchants", type=int, default=20)
    parser.add_argument("--customers", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=str, default="ml/models")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=== PayResQ ML Training ===")
    logger.info("Transactions: %d | Merchants: %d | Customers: %d | Seed: %d",
                args.transactions, args.merchants, args.customers, args.seed)

    # ------------------------------------------------------------------
    # 1. Generate synthetic data
    # ------------------------------------------------------------------
    logger.info("[1/7] Generating synthetic data...")
    from ml.data.generators.payment_generator import PaymentDataGenerator
    gen = PaymentDataGenerator(seed=args.seed)
    raw = gen.generate_all(
        n_merchants=args.merchants,
        n_customers=args.customers,
        n_transactions=args.transactions,
    )
    logger.info("  Transactions: %d | Failed with recovery: %d",
                len(raw["transactions"]),
                len(raw["recovery_actions"]))

    # ------------------------------------------------------------------
    # 2. Build ML dataset
    # ------------------------------------------------------------------
    logger.info("[2/7] Building ML dataset (feature engineering)...")
    from ml.features.builder import MLDatasetBuilder
    from ml.features.encodings import DEFAULT_ENCODINGS, FEATURE_COLUMNS, TARGET_COLUMN

    builder = MLDatasetBuilder(encodings=DEFAULT_ENCODINGS)
    df = builder.build(raw)

    # Keep only labeled rows for training
    df_labeled = df.dropna(subset=[TARGET_COLUMN]).copy()
    df_labeled[TARGET_COLUMN] = df_labeled[TARGET_COLUMN].astype(int)

    logger.info("  Total rows: %d | Labeled: %d | Positive (recovery success): %d (%.1f%%)",
                len(df), len(df_labeled),
                df_labeled[TARGET_COLUMN].sum(),
                100 * df_labeled[TARGET_COLUMN].mean())

    if len(df_labeled) < 50:
        logger.error("Too few labeled rows (%d). Increase --transactions.", len(df_labeled))
        sys.exit(1)

    # ------------------------------------------------------------------
    # 3. Temporal train/test split (80/20)
    # ------------------------------------------------------------------
    logger.info("[3/7] Temporal train/test split (80/20)...")
    df_labeled = df_labeled.reset_index(drop=True)
    split_idx = int(len(df_labeled) * 0.80)
    train_df = df_labeled.iloc[:split_idx]
    test_df = df_labeled.iloc[split_idx:]

    X_train = train_df[FEATURE_COLUMNS].values.astype(np.float32)
    y_train = train_df[TARGET_COLUMN].values.astype(int)
    X_test = test_df[FEATURE_COLUMNS].values.astype(np.float32)
    y_test = test_df[TARGET_COLUMN].values.astype(int)

    logger.info("  Train rows: %d | Test rows: %d", len(X_train), len(X_test))
    logger.info("  Train positive rate: %.1f%% | Test positive rate: %.1f%%",
                100 * y_train.mean(), 100 * y_test.mean())

    # ------------------------------------------------------------------
    # 4. Train XGBoost
    # ------------------------------------------------------------------
    logger.info("[4/7] Training XGBoost classifier...")
    import xgboost as xgb

    # Scale positive weight to handle class imbalance
    n_neg = (y_train == 0).sum()
    n_pos = (y_train == 1).sum()
    scale_pos_weight = n_neg / max(n_pos, 1)

    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
        random_state=args.seed,
        n_jobs=-1,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )
    logger.info("  Training complete.")

    # ------------------------------------------------------------------
    # 5. Evaluate ML model
    # ------------------------------------------------------------------
    logger.info("[5/7] Evaluating ML model on test set...")
    from sklearn.metrics import (
        roc_auc_score, precision_score, recall_score, f1_score, log_loss,
        confusion_matrix,
    )

    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)

    ml_metrics = {
        "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "log_loss": round(float(log_loss(y_test, y_prob)), 4),
    }
    cm = confusion_matrix(y_test, y_pred).tolist()
    ml_metrics["confusion_matrix"] = cm

    # Business metrics on test set
    ml_recovery_rate = float(y_pred[y_test == 1].mean()) if y_test.sum() > 0 else 0.0
    ml_metrics["recovery_rate_on_positives"] = round(ml_recovery_rate, 4)

    for k, v in ml_metrics.items():
        if k != "confusion_matrix":
            logger.info("  ML %s: %s", k, v)

    # ------------------------------------------------------------------
    # 6. Baseline comparison (always RETRY_NOW)
    # ------------------------------------------------------------------
    logger.info("[6/7] Evaluating baseline (always RETRY_NOW)...")
    from ml.features.encodings import DEFAULT_ENCODINGS, encode
    retry_now_enc = encode("RETRY_NOW", DEFAULT_ENCODINGS["candidate_action"])
    action_enc_col = FEATURE_COLUMNS.index("candidate_action_enc")

    # Baseline: on the test set, predict success only for RETRY_NOW action rows
    test_action = X_test[:, action_enc_col]
    baseline_mask = (test_action == retry_now_enc)
    baseline_pred = baseline_mask.astype(int)

    if baseline_pred.sum() > 0:
        baseline_precision = float(precision_score(y_test, baseline_pred, zero_division=0))
        baseline_recall = float(recall_score(y_test, baseline_pred, zero_division=0))
        baseline_f1 = float(f1_score(y_test, baseline_pred, zero_division=0))
        baseline_recovery_rate = float(y_test[baseline_mask].mean()) if baseline_mask.sum() > 0 else 0.0
    else:
        baseline_precision = baseline_recall = baseline_f1 = baseline_recovery_rate = 0.0

    baseline_metrics = {
        "strategy": "always_retry_now",
        "precision": round(baseline_precision, 4),
        "recall": round(baseline_recall, 4),
        "f1": round(baseline_f1, 4),
        "recovery_rate_on_positives": round(baseline_recovery_rate, 4),
    }

    logger.info("  Baseline recovery rate: %.1f%% | ML recovery rate: %.1f%%",
                100 * baseline_recovery_rate, 100 * ml_recovery_rate)
    logger.info("  ML F1: %.4f vs Baseline F1: %.4f", ml_metrics["f1"], baseline_metrics["f1"])

    # ------------------------------------------------------------------
    # 7. Save artifacts
    # ------------------------------------------------------------------
    logger.info("[7/7] Saving artifacts to %s ...", output_dir)

    model_path = output_dir / "recovery_model.json"
    model.save_model(str(model_path))
    logger.info("  Model saved: %s", model_path)

    from ml.features.encodings import save_encodings
    enc_path = output_dir / "encodings.json"
    # Convert dict keys to str (json requirement)
    enc_serialisable = {
        k: {str(kk): vv for kk, vv in v.items()}
        for k, v in DEFAULT_ENCODINGS.items()
    }
    save_encodings(enc_path, enc_serialisable)
    logger.info("  Encodings saved: %s", enc_path)

    metadata = {
        "model_version": "1.0",
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "n_transactions_generated": args.transactions,
        "n_merchants": args.merchants,
        "n_customers": args.customers,
        "training_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "positive_rate_train": round(float(y_train.mean()), 4),
        "positive_rate_test": round(float(y_test.mean()), 4),
        "feature_columns": FEATURE_COLUMNS,
        "feature_count": len(FEATURE_COLUMNS),
        "model_params": {
            "n_estimators": 200,
            "max_depth": 6,
            "learning_rate": 0.05,
            "scale_pos_weight": round(float(scale_pos_weight), 3),
        },
        "evaluation": ml_metrics,
        "baseline": baseline_metrics,
        "note": "EXPERIMENTAL — synthetic data only. Not real-world performance.",
    }

    meta_path = output_dir / "metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info("  Metadata saved: %s", meta_path)

    logger.info("\n=== Training Complete ===")
    logger.info("ROC-AUC: %.4f | F1: %.4f | Log Loss: %.4f",
                ml_metrics["roc_auc"], ml_metrics["f1"], ml_metrics["log_loss"])
    logger.info("ML recovery rate: %.1f%% vs Baseline: %.1f%%",
                100 * ml_recovery_rate, 100 * baseline_recovery_rate)
    logger.info("NOTE: EXPERIMENTAL results on synthetic data only.")


if __name__ == "__main__":
    main()
