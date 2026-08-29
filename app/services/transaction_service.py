from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.transaction import Transaction
from app.models.payment_attempt import PaymentAttempt
from app.models.recovery_action import RecoveryAction
from app.schemas.transaction import TransactionCreate


async def create_transaction(db: AsyncSession, data: TransactionCreate) -> Transaction:
    transaction = Transaction(
        merchant_id=data.merchant_id,
        customer_id=data.customer_id,
        external_transaction_id=data.external_transaction_id,
        amount=data.amount,
        currency=data.currency,
    )
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    return transaction


async def get_transaction_by_id(db: AsyncSession, transaction_id: str) -> Optional[Transaction]:
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id)
    )
    return result.scalar_one_or_none()


async def get_payment_attempts(db: AsyncSession, transaction_id: str) -> list[PaymentAttempt]:
    result = await db.execute(
        select(PaymentAttempt)
        .where(PaymentAttempt.transaction_id == transaction_id)
        .order_by(PaymentAttempt.attempt_number)
    )
    return list(result.scalars().all())


async def get_recovery_actions(db: AsyncSession, transaction_id: str) -> list[RecoveryAction]:
    result = await db.execute(
        select(RecoveryAction)
        .where(RecoveryAction.transaction_id == transaction_id)
        .order_by(RecoveryAction.created_at)
    )
    return list(result.scalars().all())
