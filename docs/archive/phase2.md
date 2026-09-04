We are starting Milestone 2 of PayResQ.

Read AGENTS.md first and inspect the existing implementation. Do not rewrite working Milestone 1 infrastructure.

Milestone 1 is complete and verified.

# MILESTONE 2 — PAYMENT DOMAIN + SYNTHETIC DATA

The goal of this milestone is to build the core payment domain and a realistic synthetic dataset that will later be used by our XGBoost recovery model.

Do NOT implement XGBoost, LLM agents, recovery execution, frontend, or advanced analytics yet.

---

## 1. DOMAIN MODEL

Implement these entities using SQLAlchemy 2.x:

### Merchant

Represents a business using PayResQ.

Suggested fields:

- id
- name
- created_at
- updated_at
- is_active

---

### Customer

Represents a customer belonging to a merchant.

Suggested fields:

- id
- merchant_id
- external_customer_id
- name
- email
- created_at
- updated_at

A merchant can have many customers.

A customer belongs to one merchant.

---

### Transaction

Represents the original payment intent.

Suggested fields:

- id
- merchant_id
- customer_id
- external_transaction_id
- amount
- currency
- status
- created_at
- updated_at

Transaction status should support states such as:

- CREATED
- PENDING
- SUCCESS
- FAILED
- CANCELLED

A transaction belongs to one merchant and one customer.

A merchant/customer can have many transactions.

---

### PaymentAttempt

Represents an individual attempt to complete a transaction.

Suggested fields:

- id
- transaction_id
- attempt_number
- payment_method
- bank
- status
- failure_reason
- attempted_at

A transaction can have multiple payment attempts.

Attempt number should be unique per transaction.

---

### FailureEvent

Represents information about why a payment attempt failed.

Suggested fields:

- id
- payment_attempt_id
- event_type
- failure_code
- metadata
- occurred_at

A payment attempt can have one or more failure events if appropriate.

Store structured metadata as PostgreSQL JSON/JSONB if appropriate.

---

### RecoveryAction

Represents an intervention proposed or executed by PayResQ.

Suggested fields:

- id
- transaction_id
- action_type
- status
- reason
- confidence
- scheduled_for
- executed_at
- created_at

Action types should support:

- RETRY_NOW
- RETRY_AFTER_DELAY
- SEND_PAYMENT_LINK
- CHANGE_PAYMENT_METHOD
- NOTIFY_CUSTOMER
- ESCALATE
- STOP

Do not implement actual execution yet.

This table is only the domain representation for now.

---

### RecoveryOutcome

Represents the result of a recovery action.

Suggested fields:

- id
- recovery_action_id
- success
- recovered_amount
- failure_reason
- completed_at

This allows us to measure recovered revenue later.

---

### AuditLog

Represents an auditable record of important system decisions/actions.

Suggested fields:

- id
- transaction_id
- event_type
- actor_type
- action
- reason
- metadata
- created_at

Keep this generic enough for future AI/policy audit information.

---

# 2. RELATIONSHIPS

Implement proper SQLAlchemy relationships and foreign keys.

Expected high-level structure:

Merchant
  └── Customers
        └── Transactions
              ├── PaymentAttempts
              │      └── FailureEvents
              └── RecoveryActions
                     └── RecoveryOutcomes

Transactions should also be associated with AuditLogs.

Use proper cascading behavior where appropriate, but do not blindly cascade destructive deletes in a way that could remove important financial history.

---

# 3. DATABASE CONSTRAINTS

Implement sensible constraints.

Examples:

- amount must be positive
- currency should have a sensible default such as INR
- attempt_number must be positive
- attempt_number should be unique per transaction
- confidence should be between 0 and 1 when present
- recovered_amount should not be negative
- required foreign keys should not be nullable
- external IDs should have appropriate uniqueness constraints where appropriate

Think about financial-data integrity.

Do not over-engineer constraints that don't have a clear purpose.

---

# 4. INDEXES

Add indexes based on expected access patterns.

At minimum consider indexes on:

- transactions.merchant_id
- transactions.customer_id
- transactions.status
- transactions.created_at
- payment_attempts.transaction_id
- payment_attempts.status
- failure_events.payment_attempt_id
- failure_events.occurred_at
- recovery_actions.transaction_id
- recovery_actions.status
- audit_logs.transaction_id
- audit_logs.created_at

Use composite indexes where they provide a clear benefit.

Do not blindly index every column.

Document important indexing decisions briefly.

---

# 5. ENUMS

Use appropriate enums for fields such as:

- transaction status
- payment attempt status
- payment method
- recovery action type
- recovery action status
- actor type

Keep the design maintainable.

---

# 6. ALEMBIC

Create the first proper migration for the payment domain.

Verify that:

- migration runs on a clean database
- tables are created correctly
- foreign keys exist
- indexes exist
- constraints work

Do not manually modify the database outside migrations.

---

# 7. PYDANTIC SCHEMAS

Create request/response schemas for the APIs we actually need at this stage.

Keep schemas separate from SQLAlchemy models.

For example:

- MerchantCreate / MerchantResponse
- CustomerCreate / CustomerResponse
- TransactionCreate / TransactionResponse
- PaymentAttemptResponse
- RecoveryActionResponse

Do not create schemas that aren't currently needed.

---

# 8. BASIC APIs

Implement a minimal set of REST endpoints.

At minimum:

POST /api/v1/merchants

POST /api/v1/customers

POST /api/v1/transactions

GET /api/v1/transactions/{transaction_id}

GET /api/v1/transactions/{transaction_id}/attempts

GET /api/v1/transactions/{transaction_id}/recovery-actions

Do not build complex filtering/pagination yet unless it is trivial and useful.

Keep API routes thin and put business logic in services.

Expected architecture:

API Router
    ↓
Service
    ↓
SQLAlchemy
    ↓
PostgreSQL

Do not put database/business logic directly into route handlers.

---

# 9. SYNTHETIC DATA GENERATOR

Create a reproducible synthetic data generation script.

Initially support a small development dataset such as:

- 5–10 merchants
- 100–500 customers
- 1,000–5,000 transactions

The generator must be configurable so we can later generate 50,000–100,000+ transactions.

Use a deterministic random seed option.

Generate realistic relationships.

For example:

A customer should belong to a merchant.

A transaction should belong to the correct merchant/customer.

A transaction may have multiple payment attempts.

Failed attempts should have corresponding failure information.

---

# 10. IMPORTANT — REALISTIC DATA PATTERNS

Do NOT generate completely random independent values.

The dataset will eventually train an XGBoost recovery model, so relationships must contain meaningful probabilistic patterns.

Introduce realistic correlations.

Examples:

### Customer reliability

Customers with a high historical success rate should behave differently from customers with a poor payment history.

### Temporary bank degradation

During certain simulated time windows, a particular bank can have an elevated timeout/failure rate.

Example:

ICICI + CARD + specific time window
→ elevated probability of TIMEOUT

But this must be probabilistic, NOT deterministic.

Do NOT create rules like:

"ICICI always fails at 11 PM."

Instead use probabilities.

### Failure types

Different failure types should have different characteristics:

- TIMEOUT
- BANK_DECLINED
- INSUFFICIENT_FUNDS
- NETWORK_ERROR
- AUTHENTICATION_FAILED

### Payment methods

Include realistic methods such as:

- CARD
- UPI
- NETBANKING
- WALLET

### Recovery-related information

Generate enough historical data so that later we can determine whether different recovery actions were successful.

Do not make every action succeed.

---

# 11. DATA GENERATOR ARCHITECTURE

Keep generation code separate from the application domain logic.

Suggested structure:

ml/
  data/
    generators/
      __init__.py
      payment_generator.py
    scripts/
      generate_data.py

However, use a better structure if the existing repository has a clear convention.

The generator should support configurable values such as:

--merchants
--customers
--transactions
--seed

Do not hardcode 100,000 records.

---

# 12. TESTING

Add tests for:

### Database

- merchant creation
- customer belongs to merchant
- transaction belongs to merchant/customer
- payment attempt belongs to transaction
- foreign key integrity

### Constraints

- negative amount rejected
- invalid confidence rejected
- duplicate attempt number rejected

### API

- create merchant
- create customer
- create transaction
- retrieve transaction
- retrieve payment attempts

### Synthetic data

After generation verify:

- expected approximate record counts
- valid foreign-key relationships
- failed attempts have failure information
- multiple attempts exist for some transactions
- data generation is reproducible with the same seed

Tests should not require a huge 100k dataset.

Use a small test dataset.

---

# 13. PERFORMANCE

Do not insert synthetic data one row at a time through HTTP APIs.

The generator should use efficient database insertion/bulk techniques appropriate for the scale.

For development, verify that generating thousands of records is reasonably fast.

Later we will benchmark the larger dataset.

---

# 14. DO NOT IMPLEMENT YET

Do NOT implement:

- XGBoost
- feature engineering for the ML model
- LLM
- AI agent
- recovery execution
- Redis recovery jobs
- policy engine
- frontend
- authentication
- Kafka
- microservices
- Kubernetes
- GraphQL
- CQRS
- event sourcing
- vector database

Those belong to later milestones.

Redis infrastructure from Milestone 1 should remain intact but does not need to be used for recovery yet.

---

# 15. VALIDATION

After implementation:

1. Run Alembic migration on a clean database.
2. Start the application.
3. Run the complete pytest suite.
4. Generate a small synthetic dataset.
5. Verify database relationships.
6. Verify API endpoints.
7. Verify constraints.
8. Verify deterministic generation using the same seed.
9. Check for obvious SQLAlchemy/Alembic warnings or errors.

Do not claim success without actually running the checks.

---

# 16. STOP CONDITION

This is Milestone 2 only.

When complete, STOP.

Do not automatically begin Milestone 3.

Report:

1. Final directory structure
2. Database schema summary
3. Relationships
4. Important indexes
5. Constraints
6. APIs implemented
7. Synthetic dataset generator usage
8. Number of records generated during testing
9. Complete pytest results
10. Migration verification
11. Any architectural decisions or assumptions that should be reviewed

The goal is a clean, reliable payment domain that we can build the ML system on top of in Milestone 3.