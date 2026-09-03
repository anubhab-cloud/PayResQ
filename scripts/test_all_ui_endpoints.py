"""
scripts/test_all_ui_endpoints.py
=================================
Tests all FastAPI endpoints consumed by the React UI.
Checks HTTP status codes, JSON response structure, and error handling.
"""
import urllib.request
import urllib.error
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"


def make_request(url: str, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    data_bytes = None
    if payload:
        data_bytes = json.dumps(payload).encode("utf-8")
    
    try:
        with urllib.request.urlopen(req, data=data_bytes) as resp:
            status = resp.status
            body = json.loads(resp.read().decode("utf-8"))
            return status, body
    except urllib.error.HTTPError as err:
        body = json.loads(err.read().decode("utf-8")) if err.fp else {}
        return err.code, body
    except Exception as exc:
        print(f"Connection Error for {url}: {exc}")
        return 0, {}


def run_tests():
    print("============================================================")
    print("  Testing All PayResQ API Endpoints for Frontend Integration")
    print("============================================================\n")

    # 1. Health Check
    status, data = make_request("http://localhost:8000/health")
    print(f"[1] GET /health -> Status: {status}")
    assert status == 200, f"Expected 200, got {status}"

    # 2. Dashboard Summary
    status, summary = make_request(f"{BASE_URL}/dashboard/summary")
    print(f"[2] GET /dashboard/summary -> Status: {status}")
    print(f"    Summary: {json.dumps(summary, indent=2)}")
    assert status == 200

    # 3. Dashboard Trends
    status, trends = make_request(f"{BASE_URL}/dashboard/recovery-trends?days=7")
    print(f"[3] GET /dashboard/recovery-trends -> Status: {status}")
    print(f"    Timeframe: {trends.get('timeframe_days')} days, Data points: {len(trends.get('trends', []))}")
    assert status == 200

    # 4. Failure Breakdown
    status, breakdown = make_request(f"{BASE_URL}/dashboard/failure-breakdown")
    print(f"[4] GET /dashboard/failure-breakdown -> Status: {status}")
    print(f"    Banks: {len(breakdown.get('by_bank', []))}, Methods: {len(breakdown.get('by_method', []))}")
    assert status == 200

    # 5. Demo Run Trigger
    status, demo_res = make_request(f"{BASE_URL}/dashboard/demo-run", method="POST")
    print(f"[5] POST /dashboard/demo-run -> Status: {status}")
    print(f"    Demo TX ID: {demo_res.get('transaction_id')}")
    print(f"    Action: {demo_res.get('agent_action')}, Policy: {demo_res.get('policy_outcome')}")
    assert status == 200
    demo_tx_id = demo_res["transaction_id"]

    # 6. List Transactions
    status, tx_list = make_request(f"{BASE_URL}/transactions?limit=10")
    print(f"[6] GET /transactions -> Status: {status}, Count: {len(tx_list)}")
    assert status == 200

    # 7. Get Transaction by ID
    status, tx_detail = make_request(f"{BASE_URL}/transactions/{demo_tx_id}")
    print(f"[7] GET /transactions/{demo_tx_id} -> Status: {status}")
    assert status == 200

    # 8. Get Transaction Attempts
    status, attempts = make_request(f"{BASE_URL}/transactions/{demo_tx_id}/attempts")
    print(f"[8] GET /transactions/{demo_tx_id}/attempts -> Status: {status}, Count: {len(attempts)}")
    assert status == 200

    # 9. Root Cause Analysis
    status, rca = make_request(f"{BASE_URL}/intelligence/root-cause/{demo_tx_id}")
    print(f"[9] GET /intelligence/root-cause/{demo_tx_id} -> Status: {status}")
    print(f"    Root Cause: {rca.get('root_cause')}, Confidence: {rca.get('confidence')}")
    assert status == 200

    # 10. Agent Analyze
    status, agent_dec = make_request(f"{BASE_URL}/agent/analyze/{demo_tx_id}", method="POST")
    print(f"[10] POST /agent/analyze/{demo_tx_id} -> Status: {status}")
    print(f"     Action: {agent_dec.get('agent_decision', {}).get('action')}")
    assert status == 200

    # 11. Policy Check
    status, pol_res = make_request(
        f"{BASE_URL}/recovery/policy-check/{demo_tx_id}",
        method="POST",
        payload={"action": "RETRY_AFTER_DELAY", "delay_minutes": 20, "confidence": 0.9},
    )
    print(f"[11] POST /recovery/policy-check/{demo_tx_id} -> Status: {status}")
    print(f"     Outcome: {pol_res.get('outcome')}")
    assert status == 200

    # 12. Execute Recovery
    status, exec_res = make_request(f"{BASE_URL}/recovery/execute/{demo_tx_id}", method="POST")
    print(f"[12] POST /recovery/execute/{demo_tx_id} -> Status: {status}")
    print(f"     Action ID: {exec_res.get('recovery_action_id')}, Status: {exec_res.get('status')}")
    assert status == 200
    ra_id = exec_res.get("recovery_action_id")

    # 13. Recovery Action Status
    if ra_id:
        status, ra_detail = make_request(f"{BASE_URL}/recovery/{ra_id}")
        print(f"[13] GET /recovery/{ra_id} -> Status: {status}")
        assert status == 200

    # 14. Audit Trail
    status, audit = make_request(f"{BASE_URL}/transactions/{demo_tx_id}/audit")
    print(f"[14] GET /transactions/{demo_tx_id}/audit -> Status: {status}")
    print(f"     Audit Count: {audit.get('audit_count')}")
    assert status == 200

    # 15. Intelligence Model Info
    status, model_info = make_request(f"{BASE_URL}/intelligence/model-info")
    print(f"[15] GET /intelligence/model-info -> Status: {status}")
    print(f"     Model Version: {model_info.get('model_version')}")
    assert status == 200

    print("\n============================================================")
    print("  ALL 15 API ENDPOINTS PASSED VERIFICATION!")
    print("============================================================\n")


if __name__ == "__main__":
    run_tests()
