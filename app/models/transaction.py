import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, ForeignKey, Numeric, CheckConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base
from app.models.enums import TransactionStatus


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transaction_amount_positive"),
        Index("ix_transactions_merchant_status", "merchant_id", "status"),
        Index("ix_transactions_customer_created", "customer_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    merchant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("merchants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    external_transaction_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR", server_default="INR")
    status: Mapped[TransactionStatus] = mapped_column(
        String(20),
        nullable=False,
        default=TransactionStatus.CREATED,
        server_default=TransactionStatus.CREATED.value,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="transactions")
    customer: Mapped["Customer"] = relationship("Customer", back_populates="transactions")
    payment_attempts: Mapped[list["PaymentAttempt"]] = relationship(
        "PaymentAttempt", back_populates="transaction", cascade="save-update, merge"
    )
    recovery_actions: Mapped[list["RecoveryAction"]] = relationship(
        "RecoveryAction", back_populates="transaction", cascade="save-update, merge"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="transaction", cascade="save-update, merge"
    )
