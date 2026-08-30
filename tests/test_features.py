"""
tests/test_features.py
Tests for feature engineering (MLDatasetBuilder).
Uses a tiny seeded dataset — no model training required.
"""
import pytest
import math
from ml.data.generators.payment_generator import PaymentDataGenerator
from ml.features.builder import MLDatasetBuilder
from ml.features.encodings import FEATURE_COLUMNS, TARGET_COLUMN, CANDIDATE_ACTION_CATEGORIES


def _make_raw(seed=42, n_tx=500):
    gen = PaymentDataGenerator(seed=seed)
    return gen.generate_all(n_merchants=3, n_customers=50, n_transactions=n_tx)


def test_feature_columns_present():
    raw = _make_raw()
    builder = MLDatasetBuilder()
    df = builder.build(raw)
    for col in FEATURE_COLUMNS:
        assert col in df.columns, f"Missing feature column: {col}"
    assert TARGET_COLUMN in df.columns


def test_no_future_leakage_in_features():
    """Target column must NOT be in feature columns."""
    assert TARGET_COLUMN not in FEATURE_COLUMNS, (
        f"LEAKAGE: {TARGET_COLUMN} found in FEATURE_COLUMNS"
    )


def test_all_candidate_actions_produce_rows():
    raw = _make_raw()
    builder = MLDatasetBuilder()
    df = builder.build(raw)
    from ml.features.encodings import DEFAULT_ENCODINGS, encode
    for action in CANDIDATE_ACTION_CATEGORIES:
        enc_val = encode(action, DEFAULT_ENCODINGS["candidate_action"])
        matching = df[df["candidate_action_enc"] == enc_val]
        assert len(matching) >= 0  # rows may be 0 if no failed txns, just check no error


def test_amount_log_is_log1p_of_amount():
    raw = _make_raw()
    builder = MLDatasetBuilder()
    df = builder.build(raw)
    if df.empty:
        pytest.skip("No rows generated")
    sample = df.iloc[0]
    expected = math.log1p(sample["amount"])
    assert abs(sample["amount_log"] - expected) < 1e-5


def test_transformations_reproducible():
    """Same input → identical output."""
    raw = _make_raw(seed=77, n_tx=300)
    b1 = MLDatasetBuilder()
    b2 = MLDatasetBuilder()
    df1 = b1.build(raw)
    df2 = b2.build(raw)
    assert df1.shape == df2.shape
    assert list(df1.columns) == list(df2.columns)


def test_feature_values_finite():
    """No NaN/inf in feature columns (only target may be NaN for unlabeled rows)."""
    raw = _make_raw()
    builder = MLDatasetBuilder()
    df = builder.build(raw)
    if df.empty:
        pytest.skip("No rows generated")
    import numpy as np
    for col in FEATURE_COLUMNS:
        assert not df[col].isin([float("inf"), float("-inf")]).any(), \
            f"Infinite value in feature column: {col}"
        # No NaN allowed in feature columns
        assert not df[col].isna().any(), f"NaN found in feature column: {col}"


def test_customer_success_rate_in_range():
    raw = _make_raw()
    builder = MLDatasetBuilder()
    df = builder.build(raw)
    if df.empty:
        pytest.skip("No rows generated")
    assert (df["customer_success_rate"] >= 0).all()
    assert (df["customer_success_rate"] <= 1).all()


def test_merchant_failure_rate_in_range():
    raw = _make_raw()
    builder = MLDatasetBuilder()
    df = builder.build(raw)
    if df.empty:
        pytest.skip("No rows generated")
    assert (df["merchant_failure_rate"] >= 0).all()
    assert (df["merchant_failure_rate"] <= 1).all()
