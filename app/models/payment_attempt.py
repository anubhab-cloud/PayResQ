import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, ForeignKey, Integer, UniqueConstraint, CheckConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base
from app.models.enums import PaymentAttemptStatus, PaymentMethod, FailureReason


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"
    __table_args__ = (
        UniqueConstraint("transaction_id", "attempt_number", name="uq_attempt_transaction_number"),
        CheckConstraint("attempt_number > 0", name="ck_attempt_number_positive"),
        Index("ix_payment_attempts_transaction_status", "transaction_id", "status"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    transaction_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("transactions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(String(20), nullable=False)
    bank: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[PaymentAttemptStatus] = mapped_column(
        String(20), nullable=False, default=PaymentAttemptStatus.PENDING, index=True
    )
    failure_reason: Mapped[Optional[FailureReason]] = mapped_column(String(50), nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    # Relationships
    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="payment_attempts")
    failure_events: Mapped[list["FailureEvent"]] = relationship(
        "FailureEvent", back_populates="payment_attempt", cascade="save-update, merge"
    )
