"""
tests/test_synthetic_data.py
Tests for the synthetic data generator.
"""
import pytest
from ml.data.generators.payment_generator import PaymentDataGenerator


def make_small_dataset(seed: int = 42, n_transactions: int = 200):
    gen = PaymentDataGenerator(seed=seed)
    return gen.generate_all(
        n_merchants=3,
        n_customers=30,
        n_transactions=n_transactions,
    )


def test_merchant_count():
    data = make_small_dataset()
    assert len(data["merchants"]) == 3


def test_customer_count():
    data = make_small_dataset()
    assert len(data["customers"]) == 30


def test_transaction_count():
    data = make_small_dataset(n_transactions=200)
    assert len(data["transactions"]) == 200


def test_customer_foreign_keys_valid():
    data = make_small_dataset()
    merchant_ids = {m["id"] for m in data["merchants"]}
    for customer in data["customers"]:
        assert customer["merchant_id"] in merchant_ids, (
            f"Customer {customer['id']} has invalid merchant_id"
        )


def test_transaction_foreign_keys_valid():
    data = make_small_dataset()
    merchant_ids = {m["id"] for m in data["merchants"]}
    customer_ids = {c["id"] for c in data["customers"]}
    for tx in data["transactions"]:
        assert tx["merchant_id"] in merchant_ids
        assert tx["customer_id"] in customer_ids


def test_payment_attempts_fk_valid():
    data = make_small_dataset()
    tx_ids = {tx["id"] for tx in data["transactions"]}
    for attempt in data["payment_attempts"]:
        assert attempt["transaction_id"] in tx_ids


def test_failed_attempts_have_failure_events():
    data = make_small_dataset(n_transactions=300)
    attempt_ids_with_events = {fe["payment_attempt_id"] for fe in data["failure_events"]}
    failed_attempt_ids = {
        a["id"]
        for a in data["payment_attempts"]
        if a["status"] == "FAILED"
    }
    # All failure events must reference a failed attempt
    for fe in data["failure_events"]:
        assert fe["payment_attempt_id"] in failed_attempt_ids

    # Most failed attempts should have at least one failure event
    coverage = len(attempt_ids_with_events) / max(len(failed_attempt_ids), 1)
    assert coverage > 0.80, f"Low failure event coverage: {coverage:.2%}"


def test_some_transactions_have_multiple_attempts():
    data = make_small_dataset(n_transactions=300)
    attempt_counts: dict[str, int] = {}
    for a in data["payment_attempts"]:
        tx_id = a["transaction_id"]
        attempt_counts[tx_id] = attempt_counts.get(tx_id, 0) + 1

    multi_attempt_txns = [v for v in attempt_counts.values() if v > 1]
    assert len(multi_attempt_txns) > 0, "Expected some transactions with multiple attempts"


def test_recovery_actions_fk_valid():
    data = make_small_dataset()
    tx_ids = {tx["id"] for tx in data["transactions"]}
    for ra in data["recovery_actions"]:
        assert ra["transaction_id"] in tx_ids


def test_recovery_outcomes_fk_valid():
    data = make_small_dataset()
    ra_ids = {ra["id"] for ra in data["recovery_actions"]}
    for ro in data["recovery_outcomes"]:
        assert ro["recovery_action_id"] in ra_ids


def test_reproducibility_same_seed():
    data1 = make_small_dataset(seed=99, n_transactions=100)
    data2 = make_small_dataset(seed=99, n_transactions=100)
    assert len(data1["transactions"]) == len(data2["transactions"])
    assert len(data1["payment_attempts"]) == len(data2["payment_attempts"])
    assert len(data1["failure_events"]) == len(data2["failure_events"])
    # External transaction IDs must be identical (same seed → same sequence)
    ids1 = sorted(tx["external_transaction_id"] for tx in data1["transactions"])
    ids2 = sorted(tx["external_transaction_id"] for tx in data2["transactions"])
    assert ids1 == ids2


def test_different_seeds_produce_different_data():
    data1 = make_small_dataset(seed=1, n_transactions=100)
    data2 = make_small_dataset(seed=2, n_transactions=100)
    ids1 = sorted(tx["external_transaction_id"] for tx in data1["transactions"])
    ids2 = sorted(tx["external_transaction_id"] for tx in data2["transactions"])
    assert ids1 != ids2


def test_amounts_are_positive():
    data = make_small_dataset()
    for tx in data["transactions"]:
        assert tx["amount"] > 0, f"Transaction amount must be positive: {tx['amount']}"


def test_recovery_actions_only_for_failed_transactions():
    data = make_small_dataset(n_transactions=300)
    failed_tx_ids = {tx["id"] for tx in data["transactions"] if tx["status"] == "FAILED"}
    for ra in data["recovery_actions"]:
        assert ra["transaction_id"] in failed_tx_ids, (
            "Recovery action on non-failed transaction"
        )
