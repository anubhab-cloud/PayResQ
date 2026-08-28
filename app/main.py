from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.health import router as health_router
from app.core.config import settings
from app.core.redis import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    yield
    # Shutdown tasks
    await close_redis()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="PayResQ - Autonomous Payment Revenue Recovery System API",
    version="0.1.0",
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


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to PayResQ API",
        "docs": "/docs",
        "health": "/health",
    }
