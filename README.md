# PayResQ — Autonomous Payment Revenue Recovery System

PayResQ is an AI-powered payment revenue recovery platform designed to diagnose failed transactions, predict optimal recovery actions, enforce risk and business safety policies, and autonomously execute actions to recover lost payment revenue.

---

## 🏗️ Tech Stack

- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL (SQLAlchemy 2.x + AsyncPG + Alembic)
- **Cache & Async Storage**: Redis
- **Containerization**: Docker & Docker Compose
- **Testing**: Pytest & HTTPX Async Client

---

## 📁 Project Structure

```text
.
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── health.py       # Health check API endpoint
│   ├── core/
│   │   ├── config.py           # Application settings & environment parsing
│   │   ├── db.py               # SQLAlchemy 2.x async database engine & sessions
│   │   └── redis.py            # Async Redis connection manager
│   └── main.py                 # FastAPI app entry point & middleware
├── alembic/                    # Database migration environment
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── tests/                      # Automated test suite
│   ├── conftest.py             # Pytest fixtures & async test client
│   └── test_health.py          # Health check unit & integration tests
├── .env.example                # Sample environment configuration
├── docker-compose.yml          # Docker service orchestration (API, PostgreSQL, Redis)
├── Dockerfile                  # Multi-stage Python container build
├── pyproject.toml              # Project dependencies & configurations
├── requirements.txt            # Python dependencies
└── README.md
```

---

## 🚀 Quickstart

### Option 1: Running with Docker Compose (Recommended)

1. **Start all services (FastAPI, PostgreSQL, Redis):**
   ```bash
   docker-compose up --build
   ```

2. **Access API Services:**
   - Swagger Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Health Check: [http://localhost:8000/health](http://localhost:8000/health)

---

### Option 2: Running Locally

1. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

4. **Start PostgreSQL and Redis locally** (or via Docker):
   ```bash
   docker-compose up db redis -d
   ```

5. **Run the FastAPI server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

---

## 🧪 Running Tests

Run the Pytest suite:
```bash
pytest -v
```

---

## 🗄️ Database Migrations

Manage database schemas using Alembic:

- **Generate a new migration:**
  ```bash
  alembic revision --autogenerate -m "Migration description"
  ```
- **Apply migrations:**
  ```bash
  alembic upgrade head
  ```
