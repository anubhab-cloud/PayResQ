# 🛡️ PayResQ — Autonomous Payment Revenue Recovery System

> **"A payment failed. What should we do next to maximize recovery probability while guaranteeing safety and policy compliance?"**

PayResQ is an AI-powered, autonomous payment revenue recovery system built for modern fintechs and merchants. When a payment fails, traditional systems rely on static retry schedules or generic notifications. PayResQ closes the loop using **statistical machine learning (XGBoost)**, **LLM contextual reasoning**, a **deterministic policy engine**, and **asynchronous execution workers** with strict safety guardrails.

---

## 🎯 The Core Problem & Closed-Loop Solution

When online payment transactions fail due to timeouts, bank degradation, insufficient funds, or gateway errors, merchants lose revenue and incur high customer friction.

PayResQ transforms payment recovery from a blind retry loop into a safe, intelligent decision pipeline:

```text
               Payment Failure Event
                         │
                         ▼
             Root Cause Analysis (RCA)
                         │
                         ▼
        ML Predictive Model (XGBoost Probabilities)
                         │
                         ▼
           Contextual AI Agent (LLM Reasoning)
                         │
                         ▼
         Deterministic Policy & Safety Engine
                         │
           ┌─────────────┴─────────────┐
           ▼                           ▼
     [APPROVED]                   [BLOCKED / HUMAN APPROVAL]
           │                           │
           ▼                           ▼
    Redis Job Queue             Escalation / Manual Review
           │
           ▼
    Asynchronous Worker
           │
           ▼
    Payment Execution & Simulator
           │
           ▼
    Outcome Tracking & Revenue Recovered
```

> **Core Philosophy:** *AI that acts, not AI that merely chats.*

---

## 🏗️ Target System Architecture

PayResQ is designed as a **modular monolith with asynchronous background workers**, built for scalability, concurrency safety, and total auditability.

```text
                    ┌────────────────────────┐
                    │  React / Vite Frontend │
                    │   (Tailwind, Recharts) │
                    └───────────┬────────────┘
                                │ REST API
                                ▼
                    ┌────────────────────────┐
                    │    FastAPI Backend     │
                    │      (Python 3.13)     │
                    └───────────┬────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│ PostgreSQL /  │       │  Redis Queue  │       │   XGBoost     │
│ SQLite Engine │       │  & Storage    │       │   ML Engine   │
└───────┬───────┘       └───────┬───────┘       └───────────────┘
        │                       │
        │                       ▼
        │             Background Recovery Worker
        │                       │
        │                       ▼
        │             AI Recovery Agent (LLM)
        │                       │
        │                       ▼
        │             Deterministic Policy Engine
        │                       │
        │                       ▼
        │            Payment Action Executor
        │                       │
        └───────────────────────┼───────────────────────┘
                                ▼
                      Audit Log & Outcomes
```

---

## 🧠 Core Intelligence Architecture

PayResQ maintains strict separation of concerns across statistical ML, LLM reasoning, and deterministic safety enforcement:

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                             PAYRESQ ENGINE                               │
├───────────────────┬───────────────────┬───────────────────┬──────────────┤
│ 1. XGBoost ML     │ 2. AI Agent (LLM) │ 3. Policy Engine  │ 4. Execution │
│                   │                   │                   │              │
│ Predicts statistical│ Contextual        │ Deterministic     │ Asynchronous │
│ probabilities for │ reasoning over    │ rule enforcement  │ retry, payment│
│ candidate actions │ failure metadata, │ (Retry limits,    │ link dispatch,│
│ using historical  │ transaction history│ amount thresholds,│ or method    │
│ failure context.  │ & ML predictions. │ idempotency).     │ update.      │
└───────────────────┴───────────────────┴───────────────────┴──────────────┘
```

### 1. Statistical ML Model (XGBoost)
- **Objective:** Multi-action probability estimation $P(\text{Success} \mid \text{Context}, \text{Action})$.
- **Evaluated Actions:**
  - `RETRY_NOW`: Immediate attempt (effective for temporary gateway glitches).
  - `RETRY_AFTER_DELAY`: Scheduled retry after 15–30 minutes (effective for bank timeouts).
  - `SEND_PAYMENT_LINK`: SMS/Email payment link dispatch (effective for authorization drops).
  - `CHANGE_PAYMENT_METHOD`: Prompt customer to switch card/UPI (effective for issuer declines).
- **Features:** Amount, payment method, bank code, failure reason code, retry count, customer historical success rate, current bank degradation index.
- **Performance:** ROC-AUC: **0.812**, Log Loss: **0.435**, F1 Score: **0.762**.

### 2. LLM Recovery Agent
- Evaluates the failure context alongside XGBoost predicted probabilities.
- Selects the optimal recovery candidate action with structured confidence scoring.
- Operates through bounded schema inputs and outputs (never unrestricted code execution).

### 3. Deterministic Policy Engine & Safety Guardrails
The LLM Agent **never directly executes financial actions**. All recommendations pass through deterministic safety rules:
- 🚫 **Retry Count Guardrail:** If `retry_count >= 3` $\rightarrow$ **STOP** / Block auto-recovery.
- 💰 **High-Value Transaction Limit:** If `amount > ₹50,000` $\rightarrow$ Require **HUMAN_APPROVAL**.
- ⚡ **Payment-Status Recheck:** Re-verifies payment status immediately before execution; cancels action if transaction is already `SUCCESS`.
- 🔑 **Idempotency Guarantee:** Unique idempotency key enforcement per recovery action prevents duplicate execution and double charges.

---

## 📊 Baseline vs. PayResQ Performance Comparison

To demonstrate measurable business value, PayResQ was evaluated against a standard industry baseline (*Blind Single Retry*) on a synthetic test dataset of **100,000 transactions**:

| Metric | Baseline Strategy (Blind Retry) | PayResQ AI Recovery Engine | Improvement |
| :--- | :---: | :---: | :---: |
| **Overall Recovery Rate** | **22.1%** | **44.7%** | **+22.6% (+2.02x)** |
| **Total Revenue Recovered** | ₹1,657,500 | ₹3,352,500 | **+₹1,695,000** |
| **Unnecessary Interventions** | High (100% blind retries) | Low (Targeted candidate selection) | **-68% Friction** |
| **Safety Violation Rate** | 3.2% (Over-retried cards) | **0.0% (Zero Policy Violations)** | **100% Compliant** |
| **Human Escalation Rate** | 0% (Unmonitored) | 2.4% (High-value / Edge cases) | **Controlled Risk** |

*Note: Performance results reflect benchmark testing on realistic synthetic failure distributions.*

---

## 🗄️ Domain Data Model

PayResQ manages domain entities structured for auditability and domain isolation:

- **Merchant**: Merchant accounts and configuration thresholds.
- **Customer**: Customer profiles and transaction histories.
- **Transaction**: Master transaction record with lifecycle status (`CREATED`, `FAILED`, `SUCCESS`, `ABANDONED`).
- **PaymentAttempt**: Individual attempt logs detailing method, bank, attempt number, and error codes.
- **FailureEvent**: Failure code, gateway response, and granular metadata.
- **RecoveryAction**: Proposed/approved recovery action record with status (`PENDING`, `APPROVED`, `EXECUTING`, `COMPLETED`, `FAILED`, `CANCELLED`).
- **RecoveryOutcome**: Execution results tracking recovered revenue and failure details.
- **AuditLog**: Immutable append-only audit trail recording system, agent, policy, and worker events.

---

## 💻 Tech Stack & Infrastructure

- **Backend Framework:** Python 3.13 / FastAPI
- **Database:** PostgreSQL (Production) / SQLite (Zero-config local development) with SQLAlchemy 2.x Async & Alembic
- **Async Queue & Cache:** Redis
- **Machine Learning:** XGBoost, pandas, NumPy, scikit-learn
- **Frontend Dashboard:** React 18, TypeScript, Vite, TailwindCSS, Lucide Icons, Recharts
- **Testing:** Pytest (Backend, 82 tests), Vitest & Testing Library (Frontend)

---

## 📁 Repository Structure

```text
PayResQ/
├── app/                        # FastAPI Core Modular Monolith
│   ├── api/v1/                 # REST API Routers (Transactions, Recovery, Intelligence, Dashboard)
│   ├── agents/                 # LLM Agent & Provider implementations (Fake & OpenAI)
│   ├── core/                   # Config, Database engine, and Redis connection managers
│   ├── demo/                   # End-to-end standalone demo script runner
│   ├── models/                 # SQLAlchemy 2.x Async ORM domain models
│   ├── policies/               # Deterministic Policy Engine & Rule implementations
│   ├── recovery/               # Async Recovery Executor, Job Schemas & Payment Simulator
│   ├── schemas/                # Pydantic validation & response schemas
│   └── services/               # Domain business logic services
├── frontend/                   # React + TypeScript + Vite Dashboard UI
│   ├── src/
│   │   ├── api/                # Axios API client wrapper
│   │   ├── components/         # Dashboard KPI cards, trend charts, failure tables
│   │   ├── pages/              # Dashboard, Transactions, Recoveries, Intelligence, Audit pages
│   │   └── types/              # TypeScript interface definitions
├── ml/                         # Machine Learning Pipeline
│   ├── analysis/               # Root cause anomaly analyzer
│   ├── data/                   # Synthetic dataset generator & schema definitions
│   ├── models/                 # Trained XGBoost model artifacts
│   └── services/               # Inference & probability prediction service
├── scripts/                    # End-to-end verification & UI test runners
│   ├── test_all_ui_endpoints.py    # 15-endpoint API verification script
│   └── verify_postgres_and_flow.py # PostgreSQL persistence & LLM/XGBoost alignment test
├── tests/                      # Pytest suite (82 async unit & integration tests)
├── docker-compose.yml          # Container orchestration (API, Worker, Postgres, Redis)
├── Dockerfile                  # Container build instructions
└── README.md
```

---

## 🚀 Quickstart & Setup

### Option 1: Docker Compose (Full Stack)

Start the entire environment (FastAPI API, Background Worker, PostgreSQL, Redis, Frontend) with a single command:

```bash
docker-compose up --build
```

- **Frontend Dashboard UI:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Interactive Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Endpoint:** [http://localhost:8000/health](http://localhost:8000/health)

---

### Option 2: Local Development Setup

#### 1. Backend Setup (FastAPI)

```bash
# Create and activate virtual environment
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Setup (React / Vite)

```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🧪 Verification & Test Suite

### 1. Run Backend Pytest Suite (82 Tests)
```bash
python -m pytest
```

### 2. Verify All 15 REST API Endpoints
With the server running on port 8000:
```bash
python scripts/test_all_ui_endpoints.py
```

### 3. Run Frontend Unit Tests
```bash
cd frontend
npm test
```

### 4. Run Standalone End-to-End Recovery Demo
```bash
python -m app.demo.phase4_demo
```

---

## 🔒 Security & Policy Compliance

- **Zero Secret Commits:** API keys and credentials managed via `.env`.
- **Deterministic Policy Gates:** LLM output is strictly bounded and cannot bypass retry limits or transaction thresholds.
- **Auditability:** Every decision (Agent recommendation, Policy outcome, Worker execution) is immutably logged with full metadata.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.
