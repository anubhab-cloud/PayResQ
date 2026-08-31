from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "PayResQ"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # PostgreSQL
    POSTGRES_USER: str = "payresq"
    POSTGRES_PASSWORD: str = "payresq_pass"
    POSTGRES_DB: str = "payresq_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: Optional[str] = None

    # LLM Provider
    LLM_PROVIDER: str = "fake"           # "fake" | "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_API_KEY: Optional[str] = None
    LLM_TIMEOUT_SECONDS: int = 30

    # Agent / Policy
    AGENT_CONFIDENCE_THRESHOLD: float = 0.6
    MAX_AUTOMATIC_RETRIES: int = 3
    MAX_AUTOMATIC_RECOVERY_AMOUNT: float = 50000.0

    # Recovery Worker
    RECOVERY_QUEUE_NAME: str = "recovery:jobs"
    RECOVERY_DEAD_LETTER_KEY: str = "recovery:dead"
    RECOVERY_WORKER_POLL_INTERVAL: int = 5    # seconds
    RECOVERY_MAX_JOB_RETRIES: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def async_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def async_redis_url(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"


settings = Settings()
