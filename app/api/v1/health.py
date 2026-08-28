from fastapi import APIRouter, status
from pydantic import BaseModel
from app.core.config import settings
from app.core.db import check_db_health
from app.core.redis import check_redis_health

router = APIRouter(tags=["Health"])


class ServicesHealth(BaseModel):
    database: bool
    redis: bool


class HealthResponse(BaseModel):
    status: str
    environment: str
    services: ServicesHealth


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
    description="Check the operational status of the API, Database, and Redis services.",
)
async def health_check() -> HealthResponse:
    db_ok = await check_db_health()
    redis_ok = await check_redis_health()

    overall_status = "ok" if (db_ok and redis_ok) else "degraded"

    return HealthResponse(
        status=overall_status,
        environment=settings.ENVIRONMENT,
        services=ServicesHealth(
            database=db_ok,
            redis=redis_ok,
        ),
    )
