from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.health import router as health_router
from app.api.v1.merchants import router as merchants_router
from app.api.v1.customers import router as customers_router
from app.api.v1.transactions import router as transactions_router
from app.api.v1.intelligence import router as intelligence_router
from app.core.config import settings
from app.core.redis import close_redis

# Import all models so SQLAlchemy metadata is populated (required by Alembic autogenerate)
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    yield
    # Shutdown tasks
    await close_redis()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="PayResQ - Autonomous Payment Revenue Recovery System API",
    version="0.3.0",
    lifespan=lifespan,
)

# CORS Middleware Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(health_router)  # Also expose /health at root level for container checks
app.include_router(merchants_router, prefix="/api/v1")
app.include_router(customers_router, prefix="/api/v1")
app.include_router(transactions_router, prefix="/api/v1")
app.include_router(intelligence_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to PayResQ API",
        "docs": "/docs",
        "health": "/health",
    }
