# PayResQ — Safety, Policy Engine & Guardrails

In financial systems, autonomous AI agents **must never execute unrestricted financial actions**. PayResQ enforces absolute safety through a deterministic Policy Engine that acts as the authoritative execution boundary.

---

## 1. Deterministic Policy Architecture

```text
       LLM Agent Recommendation
                  │
                  ▼
   ┌─────────────────────────────┐
   │  Policy Engine Verification │
   │                             │
   │  1. Check Retry Limits      │
   │  2. Check Amount Thresholds │
   │  3. Check Idempotency       │
   │  4. Check Transaction State │
   └──────────────┬──────────────┘
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
   [ ALLOW ] [ HUMAN_APPROVAL ] [ BLOCK ]
```

---

## 2. Core Safety Guardrails

### Rule 1: Maximum Automatic Retry Limit
- **Condition:** If `retry_count >= 3`
- **Action:** Policy Engine returns **`BLOCK`**.
- **Rationale:** Prevents infinite retry loops, card network penalties, and customer harassment.

### Rule 2: High-Value Transaction Escalation
- **Condition:** If `amount > ₹50,000` (Configurable via `MAX_AUTOMATIC_RECOVERY_AMOUNT`)
- **Action:** Policy Engine returns **`HUMAN_APPROVAL`**.
- **Rationale:** High-value payments carry elevated financial and compliance risk and require explicit merchant sign-off.

### Rule 3: Payment-Status Recheck
- **Condition:** If transaction status is already `SUCCESS`
- **Action:** Policy Engine returns **`BLOCK`** (or worker cancels job).
- **Rationale:** Prevents double charging customers who completed payment through alternative channels.

### Rule 4: Provider Failure & Malformed Output Fallback
- **Condition:** If LLM API times out, returns invalid JSON, or fails network calls.
- **Action:** Agent safely degrades to **`STOP`** recommendation (`confidence: 0.0`).
- **Rationale:** System degradation must always fail safe rather than executing random or unvalidated recovery actions.

---

## 3. Auditability & Compliance Logging

Every decision and state transition produces an immutable record in the `AuditLog` table:

```sql
SELECT id, transaction_id, event_type, actor_type, action, reason, created_at 
FROM audit_logs 
WHERE transaction_id = 'TX-12345' 
ORDER BY created_at ASC;
```

### Recorded Actors:
- `AI_AGENT`: Contextual recommendation + confidence score.
- `POLICY_ENGINE`: Rule validation outcome (`ALLOW`, `HUMAN_APPROVAL`, `BLOCK`).
- `SYSTEM`: Worker execution, simulator result, or status cancellation.
- `HUMAN_OPERATOR`: Manual approval or rejection entries.
