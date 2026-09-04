# PayResQ — Phase 4: AI Recovery Agent

## Objective

Build the AI-driven recovery orchestration layer of PayResQ.

Phase 3 already provides:

- XGBoost recovery predictions
- Root-cause analysis
- Intelligence APIs
- Historical payment features

Phase 4 must use those intelligence outputs to allow an LLM-based agent to reason about a failed payment, select an appropriate recovery action, pass the decision through deterministic safety policies, and execute the approved action asynchronously.

The architecture must follow:

LLM recommends → Policy validates → Executor executes → Outcome recorded

Do NOT allow the LLM to directly execute financial/recovery actions.

---

# 1. END-TO-END WORKFLOW

The intended workflow is:

Failed Payment
    ↓
Transaction Context
    ↓
Root Cause Analysis
    ↓
XGBoost Recovery Predictions
    ↓
LLM Recovery Agent
    ↓
Structured Decision
    ↓
Policy Engine
    ↓
ALLOW / BLOCK / HUMAN_APPROVAL
    ↓
Recovery Queue
    ↓
Worker
    ↓
Payment Simulator
    ↓
Recovery Outcome
    ↓
PostgreSQL
    ↓
Audit Log

The system must be deterministic and observable wherever possible.

---

# 2. LLM PROVIDER ABSTRACTION

Do not tightly couple the application to one LLM provider.

Create a small provider abstraction/interface.

Conceptually:

LLMProvider
    ↓
generate_decision(...)

The implementation may initially use one configured provider.

The provider/API key must come from environment configuration.

Never hardcode API keys.

The application must fail gracefully if the LLM provider is unavailable.

Do not make the entire system dependent on the LLM being available for basic database/API functionality.

---

# 3. AGENT RESPONSIBILITY

The LLM agent is responsible for reasoning over structured information.

It should receive relevant information such as:

- transaction details
- customer history
- merchant context
- failure context
- root-cause analysis
- XGBoost candidate-action probabilities
- previous recovery attempts
- applicable constraints/policy information

The LLM should NOT receive unnecessary raw database dumps.

Provide only the context required for the decision.

---

# 4. AGENT TOOLS

Implement controlled tools for the agent.

At minimum:

### Read tools

- get_transaction
- get_customer_history
- get_failure_context
- get_recovery_predictions
- get_merchant_context
- get_previous_recovery_actions

Each tool must:

- validate its inputs
- return structured data
- enforce appropriate access boundaries
- avoid exposing secrets
- fail gracefully

The agent should use tools instead of directly accessing PostgreSQL.

The LLM must NEVER receive direct database credentials or arbitrary SQL access.

---

# 5. ACTION TOOLS

Implement bounded action tools.

At minimum:

- schedule_retry
- send_payment_link
- change_payment_method
- escalate_case

These tools must NOT bypass the policy engine.

Conceptually:

Agent
    ↓
Action Request
    ↓
Policy Engine
    ↓
Approved?
    ↓
Action Executor

The LLM should not be able to invoke arbitrary application functions.

Only explicitly registered recovery actions may be requested.

---

# 6. STRUCTURED AGENT DECISION

The LLM must return a structured decision.

Do not rely on free-form text parsing.

Use a schema similar to:

{
    "action": "RETRY_AFTER_DELAY",
    "delay_minutes": 20,
    "reason": "Temporary bank degradation is likely and delayed retry has the highest predicted recovery probability.",
    "confidence": 0.91
}

Allowed actions:

- RETRY_NOW
- RETRY_AFTER_DELAY
- SEND_PAYMENT_LINK
- CHANGE_PAYMENT_METHOD
- NOTIFY_CUSTOMER
- ESCALATE
- STOP

Additional fields may be included where useful:

- transaction_id
- selected_probability
- model_version
- root_cause
- supporting_evidence

Validate all LLM output through a strict Pydantic schema.

Reject malformed or unsupported actions.

---

# 7. AGENT DECISION RULES

The agent should consider:

1. Root cause
2. XGBoost probabilities
3. Customer history
4. Merchant context
5. Number of previous recovery attempts
6. Failure type
7. Transaction amount
8. Previous recovery outcomes
9. Safety constraints

Example:

XGBoost:

RETRY_NOW = 0.24
RETRY_AFTER_DELAY = 0.71
SEND_PAYMENT_LINK = 0.39
CHANGE_PAYMENT_METHOD = 0.55

Root cause:

TEMPORARY_BANK_DEGRADATION

The agent may select:

RETRY_AFTER_DELAY

But the agent's recommendation is NOT automatically executable.

---

# 8. POLICY ENGINE

Create a deterministic policy engine independent from the LLM.

The policy engine must validate the proposed recovery action.

It should return a structured result such as:

{
    "decision": "ALLOW",
    "reason": "Action satisfies automated recovery policy.",
    "policy_version": "v1"
}

Supported policy outcomes:

- ALLOW
- BLOCK
- HUMAN_APPROVAL

---

# 9. INITIAL POLICY RULES

Implement sensible deterministic rules.

Examples:

### Already successful

If transaction is already SUCCESS:

BLOCK recovery.

Reason:

"Transaction already successful."

---

### Retry limit

If retry count reaches the configured maximum:

BLOCK automatic retry.

---

### High-value transaction

If amount exceeds configured automatic recovery limit:

HUMAN_APPROVAL

Do not hardcode the business threshold in application logic.

Put configurable thresholds in settings/environment.

---

### Duplicate recovery

If an equivalent recovery action is already pending or completed:

BLOCK duplicate execution.

---

### Invalid delay

If RETRY_AFTER_DELAY has an invalid/unsafe delay:

BLOCK.

---

### Unsupported action

If an action is not explicitly allowed:

BLOCK.

---

### Low-confidence decisions

If the configured confidence threshold is not met:

HUMAN_APPROVAL

The threshold must be configurable.

Do not assume the LLM's confidence is automatically trustworthy.

---

# 10. POLICY ENGINE MUST BE DETERMINISTIC

Do not ask the LLM:

"Is this action safe?"

The LLM may provide reasoning, but the policy engine decides whether the action is allowed.

Example:

LLM:

RETRY_AFTER_DELAY

Policy:

retry_count < 3 → TRUE
transaction successful → FALSE
amount below automatic limit → TRUE
duplicate action → FALSE

Result:

ALLOW

---

# 11. ASYNCHRONOUS RECOVERY

Approved actions must not block the API request.

Workflow:

API / Agent
    ↓
Policy Engine
    ↓
Approved
    ↓
Create Recovery Job
    ↓
Redis
    ↓
Worker
    ↓
Payment Simulator
    ↓
Outcome

Use the existing Redis infrastructure from Phase 1.

Do not introduce Kafka.

Do not introduce Celery unless there is a genuinely demonstrated requirement that cannot be handled cleanly with the existing Redis-based worker architecture.

Keep the worker implementation simple and reliable for the hackathon.

---

# 12. RECOVERY JOB

Create a recovery job representation containing enough information to execute the action safely.

Conceptually:

{
    "job_id": "...",
    "transaction_id": "...",
    "recovery_action_id": "...",
    "action": "RETRY_AFTER_DELAY",
    "scheduled_for": "...",
    "idempotency_key": "...",
    "created_at": "..."
}

Persist important job/recovery state in PostgreSQL.

Redis should be treated as the queue/transport layer, not the permanent source of truth.

---

# 13. IDEMPOTENCY

Idempotency is mandatory.

The same recovery action/job must not execute twice.

Example:

Worker receives:

JOB-123

Checks idempotency key.

If already successfully executed:

Skip execution.

If not executed:

Execute once.

This protects against:

- worker retries
- duplicate messages
- process crashes
- network retries

The implementation must make duplicate execution difficult/impossible for the same recovery action.

---

# 14. PAYMENT STATUS RECHECK

Before executing a scheduled recovery action, the worker must re-check the transaction/payment state.

Example:

Agent schedules retry.

Customer independently completes payment.

Transaction becomes:

SUCCESS

Worker later receives the retry job.

Worker must detect:

transaction already SUCCESS

and cancel/skip the recovery.

Never execute unnecessary recovery against an already successful transaction.

---

# 15. PAYMENT SIMULATOR

Implement a simulated payment/recovery executor.

We do not have access to real banking infrastructure.

The simulator should model recovery outcomes using the synthetic environment.

It should support:

- success
- failure
- configurable/probabilistic outcomes
- relevant payment/failure context

Do NOT make all retries succeed.

Do NOT use deterministic rules such as:

"ICICI always fails."

Use probabilities consistent with the synthetic data environment.

The simulator should allow us to demonstrate different recovery outcomes.

---

# 16. COUNTERFACTUAL / POLICY EVALUATION

The simulator should eventually allow us to evaluate candidate actions in the same synthetic environment.

For example:

Transaction T1:

RETRY_NOW → simulated probability/outcome
RETRY_AFTER_DELAY → simulated probability/outcome
SEND_PAYMENT_LINK → simulated probability/outcome
CHANGE_PAYMENT_METHOD → simulated probability/outcome

This allows Phase 5 to evaluate:

- baseline strategy
- ML-guided strategy
- agent/policy strategy
- recovered revenue
- recovery rate

Do not claim real-world recovery improvement.

All results must be clearly labeled as synthetic/experimental.

---

# 17. RECOVERY EXECUTOR

Create a clear execution boundary.

Conceptually:

RecoveryExecutor
    ↓
execute(action, transaction)

The executor should only execute actions that have already passed policy validation.

It should not make business decisions.

Its responsibility is execution.

Example:

Policy:

ALLOW RETRY_AFTER_DELAY

Executor:

perform simulated retry.

---

# 18. HUMAN APPROVAL

Support a HUMAN_APPROVAL state.

Example:

High-value transaction:

LLM recommends retry.

Policy:

HUMAN_APPROVAL

Do NOT execute automatically.

Persist the decision and expose it through the API for later frontend integration.

The frontend approval workflow will be completed in Phase 5.

---

# 19. AUDIT LOGGING

Every important agent/recovery step must be auditable.

Record:

- transaction ID
- agent/provider
- model name if available
- model version
- root cause
- XGBoost predictions
- selected action
- agent reasoning
- agent confidence
- policy decision
- policy version
- execution status
- recovery outcome
- timestamps

Do not store secrets or API keys.

Audit logs should make it possible to reconstruct:

"What happened and why?"

---

# 20. ERROR HANDLING

Handle:

- LLM timeout
- LLM API failure
- malformed LLM response
- unsupported action
- database failure
- Redis failure
- worker crash
- duplicate job
- transaction already successful
- payment simulator failure

The system must fail safely.

If the LLM is unavailable:

Do NOT automatically execute an unsafe fallback action.

A safe fallback may be:

HUMAN_APPROVAL

or

STOP

depending on the situation.

---

# 21. API ENDPOINTS

Implement clean APIs for Phase 4.

At minimum:

### Analyze transaction

POST /api/v1/agent/analyze/{transaction_id}

Returns the agent's structured decision.

---

### Policy evaluation

POST /api/v1/recovery/policy-check/{transaction_id}

Returns:

- proposed action
- policy decision
- reason
- policy version

---

### Execute recovery

POST /api/v1/recovery/execute/{transaction_id}

This endpoint must NOT allow direct unsafe execution.

It must:

1. obtain/validate a recovery action
2. run policy validation
3. create a recovery job if allowed
4. enqueue the job
5. return the job/recovery status

---

### Recovery status

GET /api/v1/recovery/{recovery_action_id}

Returns current recovery state.

---

### Audit trail

GET /api/v1/transactions/{transaction_id}/audit

Returns relevant audit events.

Keep API routes thin.

Use:

Router
    ↓
Service
    ↓
Agent / Policy / Executor
    ↓
Repository
    ↓
Database

---

# 22. WORKER DESIGN

Create a dedicated worker process.

Suggested structure:

worker/
    __init__.py
    main.py
    recovery_worker.py

The worker should:

1. receive a job
2. validate job structure
3. check idempotency
4. load current transaction state
5. re-check payment status
6. execute approved recovery action
7. record outcome
8. update recovery action status
9. create audit log
10. acknowledge/remove the job

Handle retries safely.

Do not endlessly retry poison jobs.

---

# 23. CONFIGURATION

Make important configuration environment-based.

Examples:

LLM_PROVIDER
LLM_MODEL
LLM_API_KEY
AGENT_CONFIDENCE_THRESHOLD
MAX_AUTOMATIC_RETRIES
MAX_AUTOMATIC_RECOVERY_AMOUNT
RECOVERY_WORKER_POLL_INTERVAL

Use existing configuration infrastructure.

Do not hardcode secrets.

Update .env.example with placeholders only.

Never commit .env.

---

# 24. OBSERVABILITY

Add useful structured logs around:

- agent decision
- policy decision
- job creation
- job execution
- idempotency checks
- recovery outcome
- errors

Logs should include identifiers such as:

- transaction_id
- recovery_action_id
- job_id

Do not log sensitive credentials.

---

# 25. TESTING

Add tests for:

## Agent

- valid structured decision
- malformed LLM output rejected
- unsupported action rejected
- LLM failure handled safely

## Tools

- transaction retrieval
- customer history
- recovery predictions
- failure context
- merchant context

## Policy

- successful transaction blocked
- retry limit enforced
- high-value transaction requires human approval
- duplicate action blocked
- valid action allowed
- low-confidence decision handled correctly

## Idempotency

- duplicate job does not execute twice
- already executed recovery is skipped

## Worker

- valid job executes
- already-successful transaction is skipped
- failed execution records outcome
- retry behavior works safely

## API

- agent analysis endpoint
- policy endpoint
- recovery execution endpoint
- recovery status endpoint
- audit endpoint

Do not require a real LLM API during normal unit tests.

Use mocked/fake provider implementations.

---

# 26. LLM MOCK / FAKE PROVIDER

Create a deterministic fake LLM provider for tests.

Example:

FakeLLMProvider
    ↓
returns structured decision

This allows tests to run without:

- API keys
- network calls
- real LLM cost

Production/development can use the configured real provider.

---

# 27. SECURITY

Never:

- expose API keys
- allow arbitrary SQL through tools
- allow arbitrary function execution
- trust raw LLM output
- bypass policy validation
- execute an action solely because the LLM requested it

Treat LLM output as untrusted input.

Validate everything.

---

# 28. ARCHITECTURE BOUNDARIES

Keep these components separate:

Agent
    ↓
Decision

Policy Engine
    ↓
Authorization

Recovery Queue
    ↓
Scheduling/transport

Worker
    ↓
Execution orchestration

Payment Simulator
    ↓
Simulated external payment behavior

Repository
    ↓
Persistence

Do not merge these responsibilities into one large service.

Do not introduce unnecessary microservices.

A modular monolith is still preferred for this hackathon.

---

# 29. DO NOT IMPLEMENT

Do NOT implement:

- Kubernetes
- Kafka
- Celery unless genuinely necessary
- microservices
- GraphQL
- CQRS
- event sourcing
- vector database
- complex RAG
- frontend
- authentication
- real payment gateway integration
- production banking integrations

These are unnecessary for this milestone.

Keep the architecture extensible without adding infrastructure that does not provide value for the prototype.

---

# 30. DEFINITION OF DONE

Phase 4 is complete only when the following end-to-end flow works:

1. A failed transaction exists.
2. Agent retrieves relevant context through tools.
3. Root-cause analysis is available.
4. XGBoost predictions are available.
5. LLM produces a structured recovery decision.
6. Decision passes Pydantic validation.
7. Policy engine evaluates the decision.
8. Approved action creates a recovery job.
9. Job enters Redis.
10. Worker receives the job.
11. Worker performs idempotency check.
12. Worker re-checks current payment status.
13. Payment simulator executes the action.
14. Recovery outcome is recorded.
15. Recovery action status is updated.
16. Audit trail records the complete flow.
17. Duplicate jobs cannot execute the same recovery twice.
18. LLM failure results in a safe fallback.
19. Human-approval actions are not automatically executed.
20. Tests pass.

---

# 31. DEMO SCENARIO

Create a deterministic demo scenario that can be used later by the frontend.

Example:

Transaction:

₹7,500

Payment method:

CARD

Bank:

ICICI

Failure:

TIMEOUT

Root cause:

TEMPORARY_BANK_DEGRADATION

XGBoost:

RETRY_NOW = 0.24
RETRY_AFTER_DELAY = 0.71
SEND_PAYMENT_LINK = 0.39
CHANGE_PAYMENT_METHOD = 0.55

Agent:

RETRY_AFTER_DELAY

Policy:

ALLOW

Worker:

EXECUTE

Simulator:

SUCCESS

Outcome:

₹7,500 recovered

The exact numbers do not need to match this example. The scenario must simply be reproducible.

---

# 32. STOP CONDITION

This is Phase 4 only.

Do NOT start Phase 5.

Do not build the frontend.

Do not redesign completed Phase 1–3 components unless required for integration.

After implementation, report:

1. Final directory structure
2. LLM provider abstraction
3. Agent workflow
4. Tools implemented
5. Structured decision schema
6. Policy rules
7. Redis/worker architecture
8. Idempotency implementation
9. Payment simulator behavior
10. API endpoints
11. Audit logging
12. Error handling
13. Test results
14. End-to-end demo result
15. Any limitations
16. Any assumptions
17. Anything that should be reviewed before Phase 5