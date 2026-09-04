# PayResQ — System Architecture & Design

PayResQ is built using a **modular monolith + asynchronous background worker** architecture. This design maximizes engineering simplicity, transactional consistency, and execution safety without incurring the operational overhead of microservices.

---

## 1. High-Level System Architecture

```mermaid
graph TD
    Client[React / Vite Frontend] -->|REST API| API[FastAPI Application]
    
    subgraph Core Monolith
        API --> DomainServices[Domain Services]
        DomainServices --> DB[(PostgreSQL / SQLite)]
        DomainServices --> RCA[Root Cause Analyzer]
        DomainServices --> MLEngine[XGBoost ML Inference Engine]
        DomainServices --> LLMAgent[LLM Recovery Agent]
        DomainServices --> PolicyEngine[Deterministic Policy Engine]
    end
    
    PolicyEngine -->|Enqueue Job (ALLOW)| Redis[(Redis Queue)]
    
    subgraph Asynchronous Worker Layer
        WorkerProcess[Python Background Worker] -->|Poll Jobs| Redis
        WorkerProcess -->|Re-check TX Status| DB
        WorkerProcess --> Simulator[Payment Gateway Simulator]
        Simulator -->|Record Outcome & Audit| DB
    end
```

---

## 2. Component Breakdown

### A. Frontend Layer (`frontend/`)
- **Technology:** React 18, TypeScript, Vite, TailwindCSS, Recharts.
- **Role:** Provides merchant operations dashboards, recovery analytics, transaction detail inspection, audit logging streams, and an interactive end-to-end recovery demo runner.

### B. FastAPI REST Core (`app/api/v1/`)
- **Technology:** Python 3.13, FastAPI, Pydantic v2, AsyncIO.
- **Role:** Exposes modular REST endpoints for merchants, customers, transactions, ML intelligence, AI agent analysis, policy checks, recovery execution, and dashboard metrics.

### C. Domain Services & Persistence (`app/services/`, `app/models/`)
- **Technology:** SQLAlchemy 2.x Async, AsyncPG / aiosqlite, Alembic.
- **Role:** Manages relational entities (`Merchant`, `Customer`, `Transaction`, `PaymentAttempt`, `FailureEvent`, `RecoveryAction`, `RecoveryOutcome`, `AuditLog`) with ACID safety and async connection pooling.

### D. Intelligence Layer (`ml/`)
- **RCA Module:** Data-driven statistical failure anomaly detector comparing baseline rates to recent window rates.
- **XGBoost Inference Engine:** Action-specific probability model predicting $P(\text{Success} \mid \text{Context}, \text{Action})$.

### E. AI Recovery Agent (`app/agents/`)
- **Technology:** Provider abstraction (`FakeLLMProvider`, `OpenAIProvider`, `GeminiProvider`).
- **Role:** Reads context and ML scores to generate structured, human-explainable recovery action recommendations.

### F. Policy Engine (`app/policies/`)
- **Technology:** Deterministic Python rule set.
- **Role:** Authoritative safety execution boundary. Evaluates recommendations against retry limits, transaction amount limits, and risk thresholds.

### G. Asynchronous Job Queue & Worker (`worker/`, `app/recovery/`)
- **Technology:** Redis (`redis.asyncio`), Python worker process.
- **Role:** Decouples API response from long-running execution workflows. Re-verifies payment state before invoking the payment simulator.

---

## 3. Data Flow & Transaction Lifecycle

1. **Failure Ingestion:** Transaction payment attempt fails and is recorded in DB with failure metadata (`BANK_TIMEOUT`, `GATEWAY_ERROR`).
2. **Analysis Trigger:** Recovery process is initiated. RCA extracts degradation evidence.
3. **ML Scoring:** XGBoost evaluates candidate actions (`RETRY_NOW`, `RETRY_AFTER_DELAY`, `SEND_PAYMENT_LINK`, `CHANGE_PAYMENT_METHOD`).
4. **Agent Contextualization:** LLM agent parses context and outputs structured recommendation.
5. **Policy Gatekeeping:** Policy engine validates request $\rightarrow$ returns `ALLOW`, `HUMAN_APPROVAL`, or `BLOCK`.
6. **Queueing & Worker Execution:** If `ALLOW`, `RecoveryAction` is created (`APPROVED`) and enqueued in Redis. Background worker dequeues job, re-checks payment status, runs simulator, records `RecoveryOutcome`, and writes audit log.
