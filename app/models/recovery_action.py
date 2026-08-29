import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, ForeignKey, Float, CheckConstraint, Text, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base
from app.models.enums import RecoveryActionType, RecoveryActionStatus


class RecoveryAction(Base):
    __tablename__ = "recovery_actions"
    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_recovery_action_confidence_range"),
        Index("ix_recovery_actions_transaction_status", "transaction_id", "status"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    transaction_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("transactions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    action_type: Mapped[RecoveryActionType] = mapped_column(String(30), nullable=False)
    status: Mapped[RecoveryActionStatus] = mapped_column(
        String(20),
        nullable=False,
        default=RecoveryActionStatus.PENDING,
        server_default=RecoveryActionStatus.PENDING.value,
        index=True,
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    # Relationships
    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="recovery_actions")
    outcome: Mapped[Optional["RecoveryOutcome"]] = relationship(
        "RecoveryOutcome", back_populates="recovery_action", uselist=False, cascade="save-update, merge"
    )
