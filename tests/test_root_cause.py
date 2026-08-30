"""
tests/test_root_cause.py
Tests for the deterministic root-cause analyzer.
"""
import pytest
from datetime import datetime, timezone, timedelta

from ml.analysis.root_cause import RootCauseAnalyzer


def _make_attempts(bank="ICICI", method="CARD", n_ok=50, n_fail=5,
                   failed_reason="TIMEOUT", recent_hours=0):
    """Generate a list of synthetic payment attempt dicts."""
    attempts = []
    base_time = datetime.now(timezone.utc) - timedelta(hours=24)
    idx = 0
    for i in range(n_ok):
        attempts.append({
            "id": f"a{idx}", "transaction_id": f"t{idx}",
            "attempt_number": 1, "bank": bank, "payment_method": method,
            "status": "SUCCESS", "failure_reason": None,
            "attempted_at": base_time + timedelta(minutes=idx * 10),
        })
        idx += 1
    for i in range(n_fail):
        # Place recent failures in the last `recent_hours` hours
        offset = timedelta(hours=24 - recent_hours) if recent_hours > 0 else timedelta(hours=12)
        attempts.append({
            "id": f"a{idx}", "transaction_id": f"t{idx}",
            "attempt_number": 1, "bank": bank, "payment_method": method,
            "status": "FAILED", "failure_reason": failed_reason,
            "attempted_at": base_time + offset + timedelta(minutes=i * 5),
        })
        idx += 1
    return attempts


def test_elevated_failure_pattern_detected():
    """
    Inject many recent failures for ICICI/CARD with only a few historic.
    The analyzer should detect a temporal anomaly.
    """
    # 50 successes, 5 random failures spread across 24h (baseline ~9%)
    base_attempts = _make_attempts("ICICI", "CARD", n_ok=50, n_fail=5, recent_hours=0)
    # Add 20 more recent failures in the last 6h (heavy spike)
    recent_failures = []
    ref_time = datetime.now(timezone.utc)
    for i in range(20):
        recent_failures.append({
            "id": f"recent_{i}", "transaction_id": f"recent_t_{i}",
            "attempt_number": 1, "bank": "ICICI", "payment_method": "CARD",
            "status": "FAILED", "failure_reason": "TIMEOUT",
            "attempted_at": ref_time - timedelta(hours=2, minutes=i * 3),
        })

    all_attempts = base_attempts + recent_failures

    # The "this transaction" attempts
    tx_attempts = [{
        "id": "tx1", "transaction_id": "target",
        "attempt_number": 1, "bank": "ICICI", "payment_method": "CARD",
        "status": "FAILED", "failure_reason": "TIMEOUT",
        "attempted_at": ref_time - timedelta(hours=1),
    }]

    analyzer = RootCauseAnalyzer(
        rate_ratio_threshold=1.5,
        min_delta=0.05,
        min_recent_samples=5,
        recent_window_hours=6,
    )
    result = analyzer.analyze_transaction(
        transaction_id="target",
        attempts=tx_attempts,
        all_attempts=all_attempts,
        reference_time=ref_time,
    )

    assert result["root_cause"] != "ISOLATED_TRANSACTION_FAILURE", \
        "Expected anomaly to be detected"
    assert result["confidence"] > 0.5
    assert len(result["evidence"]) > 0


def test_normal_pattern_no_false_alarm():
    """Low, consistent failure rate — should NOT trigger anomaly."""
    # All spread evenly, no spike
    attempts = _make_attempts("SBI", "UPI", n_ok=90, n_fail=5, recent_hours=0)

    analyzer = RootCauseAnalyzer(
        rate_ratio_threshold=1.8,
        min_delta=0.05,
        min_recent_samples=5,
        recent_window_hours=6,
    )
    tx_attempts = [attempts[-1]]  # last attempt
    result = analyzer.analyze_transaction(
        transaction_id="normal_tx",
        attempts=tx_attempts,
        all_attempts=attempts,
    )

    # Should be isolated or insufficient data, not a degradation alarm
    assert result["root_cause"] in (
        "ISOLATED_TRANSACTION_FAILURE", "INSUFFICIENT_DATA", "NO_FAILURE_DETECTED"
    )


def test_evidence_list_nonempty_on_anomaly():
    """Evidence must be populated when anomaly is detected."""
    ref_time = datetime.now(timezone.utc)
    many_failures = [
        {
            "id": f"f{i}", "transaction_id": f"t{i}",
            "attempt_number": 1, "bank": "HDFC", "payment_method": "CARD",
            "status": "FAILED", "failure_reason": "BANK_DECLINED",
            "attempted_at": ref_time - timedelta(hours=1, minutes=i),
        }
        for i in range(30)
    ]
    tx_attempts = [many_failures[0]]

    analyzer = RootCauseAnalyzer(
        rate_ratio_threshold=1.5,
        min_delta=0.02,
        min_recent_samples=5,
        recent_window_hours=6,
    )
    result = analyzer.analyze_transaction(
        transaction_id="hdfc_tx",
        attempts=tx_attempts,
        all_attempts=many_failures,
        reference_time=ref_time,
    )

    if result["root_cause"] != "ISOLATED_TRANSACTION_FAILURE":
        assert len(result["evidence"]) > 0


def test_confidence_in_range():
    """Confidence score must always be between 0 and 1."""
    attempts = _make_attempts("AXIS", "UPI", n_ok=30, n_fail=10, recent_hours=4)
    tx_attempts = [a for a in attempts if a["status"] == "FAILED"][:1]
    analyzer = RootCauseAnalyzer()
    result = analyzer.analyze_transaction("ax1", tx_attempts, attempts)
    assert 0.0 <= result["confidence"] <= 1.0


def test_no_data_returns_graceful_result():
    analyzer = RootCauseAnalyzer()
    result = analyzer.analyze_transaction("tx_empty", [], [])
    assert result["root_cause"] == "INSUFFICIENT_DATA"
    assert result["confidence"] == 0.0


def test_global_analysis_returns_list():
    attempts = _make_attempts("KOTAK", "NETBANKING", n_ok=20, n_fail=3)
    analyzer = RootCauseAnalyzer()
    results = analyzer.analyze_global(attempts)
    assert isinstance(results, list)


def test_experimental_note_in_result():
    """Every result must contain the EXPERIMENTAL label."""
    attempts = _make_attempts("PAYTM", "WALLET", n_ok=10, n_fail=2)
    tx_attempts = [a for a in attempts if a["status"] == "FAILED"][:1]
    analyzer = RootCauseAnalyzer()
    result = analyzer.analyze_transaction("note_test", tx_attempts, attempts)
    assert "EXPERIMENTAL" in result.get("note", "")
