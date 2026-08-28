# PayResQ — Agent Instructions

## 1. Project Overview

**Project name:** PayResQ

PayResQ is an AI-powered autonomous payment revenue recovery system.

The core problem:

When a payment fails, merchants often know that the payment failed, but don't have an intelligent system that determines **why it failed, what recovery action is most likely to work, whether that action is safe to execute, and whether the intervention actually recovered revenue.**

PayResQ aims to close that loop:

```text
Payment Failure
      ↓
Root Cause Analysis
      ↓
Recovery Probability Prediction
      ↓
AI Decision
      ↓
Policy / Safety Check
      ↓
Recovery Action
      ↓
Outcome
      ↓
Revenue Recovered
```

The system is being built for a fintech/AI hackathon and must demonstrate both:

* meaningful AI usage
* credible backend/system-design engineering

The project should feel like a realistic fintech prototype rather than a generic LLM wrapper.

---

# 2. Core Product Concept

PayResQ should answer:

> **"A payment failed. What should we do next to maximize the probability of recovering the revenue, while staying within safety and business policies?"**

Example:

```text
Payment:
₹7,500

Method:
Card

Bank:
ICICI

Failure:
Timeout

Customer:
Existing customer

Previous success rate:
93%

Retries:
0
```

The system may evaluate:

```text
Retry immediately       → 21%
Retry after 20 minutes  → 67%
Payment link             → 43%
Change payment method   → 51%
```

The system then selects the appropriate intervention subject to policy and safety constraints.

---

# 3. Important AI Architecture

AI must NOT mean "put an LLM everywhere."

Different components have different responsibilities.

## XGBoost

XGBoost is responsible for structured prediction.

It should estimate recovery probability for candidate recovery actions.

Conceptually:

```text
Transaction + Customer + Failure Context + Action
                    ↓
                 XGBoost
                    ↓
          Recovery Probability
```

Example:

```text
Retry now        → 0.21
Delayed retry    → 0.67
Payment link     → 0.43
Change method    → 0.51
```

XGBoost answers:

> "What is statistically likely to work?"

---

## LLM Agent

The LLM is responsible for contextual reasoning and orchestration.

It should use tools to retrieve information and reason over:

* transaction context
* customer history
* merchant context
* failure information
* ML predictions
* available recovery actions
* policies

The agent may produce a structured decision such as:

```json
{
  "diagnosis": "temporary_bank_failure",
  "recommended_action": "retry_after_delay",
  "delay_minutes": 20,
  "confidence": 0.91,
  "reason": "Bank-specific timeout failures increased significantly during the current period."
}
```

The LLM should NOT directly execute unrestricted financial actions.

---

## Policy Engine

The policy engine is deterministic.

It answers:

> "Is this action allowed?"

Examples:

```text
Retry count >= 3
        ↓
STOP

Amount > automatic approval threshold
        ↓
HUMAN APPROVAL

High risk transaction
        ↓
BLOCK / ESCALATE
```

Architecture:

```text
XGBoost
   ↓
LLM Agent
   ↓
Policy Engine
   ↓
Action Executor
```

Never allow the LLM to bypass deterministic policies.

---

# 4. Target Architecture

Use a **modular monolith + asynchronous worker architecture**.

Do NOT build a large microservice architecture for the initial prototype.

Target architecture:

```text
                    ┌───────────────┐
                    │   Frontend    │
                    │   Next.js     │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    FastAPI    │
                    │    Backend    │
                    └───────┬───────┘
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
        PostgreSQL        Redis        ML Engine
             │              │              │
             │              ▼              │
             │        Background Worker    │
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                     AI Recovery Agent
                            │
                            ▼
                     Policy Engine
                            │
                            ▼
                     Action Executor
                            │
                            ▼
                     Outcome Tracker
                            │
                            ▼
                      Analytics
```

---

# 5. Technology Stack

## Backend

* Python
* FastAPI
* SQLAlchemy 2.x
* Pydantic
* Alembic

## Database

* PostgreSQL

## Async Processing

* Redis
* Background worker

Kafka is NOT required initially.

## Machine Learning

* XGBoost
* pandas
* NumPy
* scikit-learn for preprocessing/evaluation where appropriate

## LLM

Use a strong API-based LLM.

The exact provider/model can be selected during implementation based on availability, cost and hackathon constraints.

## Frontend

* Next.js
* React
* TypeScript

## Infrastructure

* Docker
* Docker Compose

## Testing

* pytest

---

# 6. Architecture Principles

## Modular Monolith

Organize code into clear domain modules.

For example:

```text
backend/app/
├── api/
├── core/
├── models/
├── schemas/
├── services/
├── workers/
├── policies/
└── agents/
```

Do not create microservices unless there is a demonstrated reason.

---

## Async Processing

Payment recovery actions should eventually be processed asynchronously.

Example:

```text
Payment Failed
      ↓
Create Recovery Job
      ↓
Redis
      ↓
Worker
      ↓
Agent / Policy
      ↓
Recovery Action
```

The API should not unnecessarily block while long-running recovery workflows execute.

---

## Idempotency

Financial operations must be idempotent.

If the same payment event arrives twice:

```text
EVENT #123
EVENT #123
```

the system must not execute two recovery actions.

Expected behavior:

```text
EVENT #123
      ↓
First processing → execute
Second processing → detect duplicate → skip
```

---

## Retry Handling

Transient failures should be retried safely.

However, retries must have:

* maximum retry count
* backoff
* clear terminal state
* audit trail

Never create infinite retry loops.

---

## Race Conditions

The system must account for cases such as:

```text
Worker A → recovery action
Worker B → same recovery action
```

Only one should successfully perform the operation.

Similarly:

```text
Payment succeeds
        ↓
Recovery worker wakes up
        ↓
Must detect payment is already successful
        ↓
Do NOT perform another recovery
```

---

## Auditability

Every important AI/recovery decision should be traceable.

Record:

* transaction
* decision
* reason
* model prediction
* selected action
* policy result
* execution status
* timestamp
* outcome

Financial actions must never be opaque.

---

# 7. Data Model

The eventual system should have domain entities similar to:

```text
Merchant
Customer
Transaction
PaymentAttempt
FailureEvent
RecoveryAction
RecoveryOutcome
AgentDecision
Policy
AuditLog
```

Do not prematurely implement every model.

Create models when their corresponding milestone requires them.

---

# 8. Synthetic Data

We do not have access to real customer/payment data.

Create realistic synthetic data.

Target eventually:

**50,000–100,000 transactions**

Include useful features such as:

```text
transaction_id
merchant_id
customer_id
amount
payment_method
bank
timestamp
location
device
failure_reason
retry_count
customer_success_rate
merchant_failure_rate
bank_failure_rate
```

The synthetic generator should contain realistic probabilistic patterns.

Do NOT create deterministic fake rules such as:

```text
timeout → always succeeds after delayed retry
```

Instead use probabilistic relationships.

Example:

```text
Temporary bank timeout
+
historically reliable customer
+
low retry count
+
currently elevated bank failure rate

→ delayed retry has a HIGHER probability of success
```

but never 100%.

---

# 9. Machine Learning Strategy

The ML problem is action-specific recovery prediction.

Input:

```text
Transaction features
+
Customer features
+
Merchant features
+
Failure context
+
Candidate recovery action
```

Output:

```text
Probability of successful recovery
```

Conceptually:

```text
X = transaction/context/action features
Y = recovery_success (0 or 1)
```

Train an XGBoost classifier.

Evaluate using appropriate metrics such as:

* ROC-AUC
* Precision
* Recall
* F1
* Log Loss
* calibration where appropriate

Use a proper train/test split.

Avoid data leakage.

The evaluation dataset must not be used to train the model.

---

# 10. Baseline Comparison

The project must compare the AI strategy against a simple baseline.

Example baseline:

```text
Every failed payment
        ↓
Retry once
```

AI strategy:

```text
Failed payment
      ↓
Root cause/context
      ↓
XGBoost recovery probabilities
      ↓
Agent decision
      ↓
Policy check
      ↓
Recovery action
```

Compare:

* recovery rate
* revenue recovered
* unnecessary interventions
* failed interventions
* human escalations
* recovery cost if modeled

The goal is to demonstrate measurable improvement.

Do NOT fabricate real-world performance claims.

Clearly label synthetic-data results as experimental/simulated results.

---

# 11. Root Cause Intelligence

PayResQ should detect patterns in failures.

Example:

```text
Overall failure rate:
4.2% → 11.8%
```

Break down by:

* bank
* payment method
* merchant
* time
* geography
* failure reason

Example:

```text
ICICI + Cards + 11PM–12AM

Failure rate:
4% → 18%
```

The system should identify this as a likely contributor to the anomaly.

Root-cause analysis should use data-driven evidence rather than simply asking the LLM to invent an explanation.

---

# 12. Recovery Actions

Candidate actions may include:

```text
retry_now
retry_after_delay
send_payment_link
request_payment_method_change
notify_customer
escalate_to_human
stop_recovery
```

The final action must always pass the policy layer.

---

# 13. Agent Tools

The eventual AI agent should have bounded tools such as:

```text
get_transaction()
get_customer_history()
get_failure_context()
get_recovery_predictions()
get_merchant_context()

schedule_retry()
send_payment_link()
notify_customer()
escalate_case()
```

Tools must have explicit schemas.

The agent should not have unrestricted database or infrastructure access.

---

# 14. Safety / Guardrails

Examples:

### Retry limit

```text
retry_count >= 3
→ STOP
```

### High-value transaction

```text
amount > configured_threshold
→ require human approval
```

### High-risk transaction

```text
risk_score >= threshold
→ do not automatically recover
```

### Already successful

```text
payment_status == SUCCESS
→ no recovery action
```

### Duplicate event

```text
same event_id
→ idempotency check
→ do not duplicate action
```

---

# 15. Dashboard Requirements

The eventual frontend should show:

```text
Revenue At Risk
Revenue Recovered
Recovery Rate
Successful Recovery Actions
Human Escalations
Failure Rate
```

It should also provide transaction-level investigation.

Example:

```text
Transaction #83921

Amount:
₹7,500

Status:
FAILED

Root Cause:
Temporary bank degradation

Confidence:
91%

Recovery Predictions:

Retry now              21%
Retry after 20 min     67%
Payment link            43%
Change method           51%

Policy:
APPROVED

Action:
Retry after 20 minutes
```

The demo should show the complete flow:

```text
FAILED
  ↓
INVESTIGATING
  ↓
DECISION
  ↓
POLICY CHECK
  ↓
ACTION
  ↓
SUCCESS
  ↓
₹7,500 RECOVERED
```

---

# 16. Four-to-Five-Day Development Scope

We have a strict deadline.

Prioritize working functionality.

## Milestone 1 — Foundation

* FastAPI
* PostgreSQL
* Redis
* Docker Compose
* SQLAlchemy
* Alembic
* testing setup

## Milestone 2 — Payment Domain

* transaction model
* payment attempts
* failure events
* recovery actions
* synthetic data generator
* basic APIs

## Milestone 3 — Intelligence

* feature engineering
* XGBoost
* recovery probability
* root-cause analysis
* baseline comparison

## Milestone 4 — Agent

* LLM integration
* bounded tools
* policy engine
* guardrails
* audit logging
* asynchronous recovery worker
* idempotency

## Milestone 5 — Product

* dashboard
* transaction investigation
* recovery simulation
* metrics
* evaluation
* README
* architecture diagram
* demo/pitch

Do not automatically jump to the next milestone.

Complete and verify the current milestone first.

---

# 17. What NOT to Build Unless Clearly Necessary

Avoid unnecessary infrastructure complexity.

Do NOT introduce:

* Kubernetes
* Kafka
* large microservice architecture
* GraphQL
* event sourcing
* CQRS
* vector databases
* unnecessary distributed systems
* unnecessary design patterns

These technologies are not forbidden forever.

They should only be introduced if a concrete requirement appears and the benefit justifies the time/complexity.

For the 4–5 day prototype, simplicity and reliability are more valuable.

---

# 18. What SHOULD Be Technically Strong

Prioritize:

* asynchronous processing
* idempotency
* concurrency safety
* retry handling
* deterministic policy enforcement
* audit logs
* ML evaluation
* measurable recovery outcomes
* clean API design
* database design
* failure handling
* observability
* clear separation between LLM reasoning and deterministic execution

---

# 19. Coding Standards

Prefer:

* readable Python
* type hints
* small focused functions
* clear module boundaries
* meaningful variable names
* explicit error handling
* environment-based configuration
* testable business logic

Avoid:

* huge files
* duplicated logic
* magic constants
* hardcoded secrets
* unnecessary abstractions
* premature optimization
* generated code that nobody can explain

Do not add dependencies without a reason.

---

# 20. Security

Never commit:

* API keys
* passwords
* tokens
* private credentials
* `.env`

Use `.env.example` for configuration examples.

Financial actions should be treated as sensitive operations.

The LLM must never bypass:

* policy checks
* authorization
* amount limits
* retry limits
* idempotency checks

---

# 21. AI Coding Agent Rules

AI coding agents are being used heavily to accelerate development.

However:

**Do not blindly generate the entire project in one step.**

Work milestone-by-milestone.

Before changing architecture:

1. inspect the existing code,
2. understand current dependencies,
3. preserve working functionality,
4. make the smallest reasonable change,
5. run tests,
6. verify the result.

Do not rewrite functioning modules unnecessarily.

When adding a feature:

```text
Understand
→ Implement
→ Test
→ Verify
→ Report
```

Do not proceed to the next milestone without confirmation.

---

# 22. Current Status

The repository is currently being initialized.

The first task is:

**Milestone 1 — Project Foundation**

Implement only:

* FastAPI
* PostgreSQL
* Redis
* Docker Compose
* SQLAlchemy
* Alembic
* environment configuration
* health checks
* pytest setup
* basic README

Then stop.

---

# 23. Definition of Done

A milestone is complete only when:

* implementation exists,
* application runs,
* relevant services start,
* tests pass,
* integration has been verified,
* no obvious configuration errors remain,
* changes are understandable,
* the result is reported clearly.

Never claim something works without actually testing it.

---

# 24. Core Philosophy

PayResQ should demonstrate:

> **AI that acts, not AI that merely chats.**

The central loop is:

```text
DETECT
  ↓
UNDERSTAND
  ↓
PREDICT
  ↓
DECIDE
  ↓
CHECK
  ↓
ACT
  ↓
MEASURE
```

The final project should demonstrate that this loop can recover revenue safely and measurably.
