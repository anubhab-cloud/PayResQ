import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, ForeignKey, Boolean, Numeric, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base


class RecoveryOutcome(Base):
    __tablename__ = "recovery_outcomes"
    __table_args__ = (
        CheckConstraint("recovered_amount >= 0", name="ck_recovery_outcome_amount_non_negative"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    recovery_action_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("recovery_actions.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    recovered_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    # Relationships
    recovery_action: Mapped["RecoveryAction"] = relationship(
        "RecoveryAction", back_populates="outcome"
    )
