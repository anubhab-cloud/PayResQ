# PayResQ — Asynchronous Recovery Engine & Worker

The PayResQ Recovery Engine handles background job queueing, concurrency safety, idempotency, and simulated recovery execution.

---

## 1. Asynchronous Architecture

Payment recovery workflows should never block synchronously during HTTP request handling. PayResQ uses Redis and background worker processes to decouple decision-making from execution.

```text
FastAPI API Thread              Redis Queue             Background Worker Process
──────────────────              ───────────             ─────────────────────────
      │                              │                             │
      │ 1. Process Transaction       │                             │
      │    (Agent + Policy Check)    │                             │
      │                              │                             │
      │ 2. Enqueue Recovery Job      │                             │
      └─────────────────────────────►│                             │
      │    (Status: ENQUEUED)        │                             │
      │                              │ 3. Poll / BLPOP             │
      │                              │────────────────────────────►│
      │                              │                             │
      │                              │                             │ 4. Re-check Payment Status in DB
      │                              │                             │ 5. Execute Payment Simulator
      │                              │                             │ 6. Record Outcome & Audit Log
```

---

## 2. Recovery Action Lifecycle & States

Every recovery action passes through explicit state transitions:

```text
[ PENDING ] ──► [ APPROVED ] ──► [ EXECUTING ] ──► [ COMPLETED ]
                    │                                   │
                    ├──► [ BLOCKED ]                    └──► [ FAILED ]
                    │
                    └──► [ CANCELLED ] (If already SUCCESS)
```

- **`PENDING`**: Initial state upon agent recommendation.
- **`APPROVED`**: Passed deterministic policy engine check.
- **`BLOCKED`**: Policy engine rejected action (e.g., max retries exceeded).
- **`EXECUTING`**: Background worker has dequeued job and begun execution.
- **`COMPLETED`**: Recovery action executed successfully (simulated payment recovered).
- **`FAILED`**: Recovery action executed but simulated payment failed.
- **`CANCELLED`**: Execution skipped because payment status changed to `SUCCESS` prior to worker run.

---

## 3. Idempotency & Race Condition Prevention

Financial recovery systems must guarantee zero duplicate operations.

### Key Mechanisms:
1. **Unique Idempotency Key:** Each job enqueued in Redis contains an `idempotency_key` constructed as `demo-{recovery_action_id}`.
2. **Pre-Execution Database Lock / State Verification:** When the worker wakes up, it re-queries the transaction status. If `status == 'SUCCESS'`, the worker skips execution, marks the recovery action as `CANCELLED`, and logs an audit event.
3. **Action Status Check:** If the `RecoveryAction` status is already `COMPLETED` or `FAILED`, duplicate worker runs terminate immediately without re-invoking the simulator.

---

## 4. Payment Gateway Simulator (`PaymentSimulator`)

Since live payment gateway APIs require production merchant credentials and real monetary funds, PayResQ uses a payment gateway simulator (`app/recovery/simulator.py`).

- Simulates gateway network timeouts, bank authorization responses, and customer payment link interactions.
- Evaluates outcomes based on realistic probabilistic distributions.
- Returns explicit `SimulationResult` objects tracking `success`, `recovered_amount`, and `simulator_note`.
