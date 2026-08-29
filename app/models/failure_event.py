import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import String, ForeignKey, JSON, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base


class FailureEvent(Base):
    __tablename__ = "failure_events"
    __table_args__ = (
        Index("ix_failure_events_attempt_occurred", "payment_attempt_id", "occurred_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    payment_attempt_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("payment_attempts.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    failure_code: Mapped[str] = mapped_column(String(100), nullable=False)
    metadata_: Mapped[Any] = mapped_column("metadata", JSON, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        index=True,
    )

    # Relationships
    payment_attempt: Mapped["PaymentAttempt"] = relationship(
        "PaymentAttempt", back_populates="failure_events"
    )
