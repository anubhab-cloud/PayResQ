"""
generate_data.py — Synthetic Data Generation CLI Script

Usage:
    python ml/data/scripts/generate_data.py [options]

Options:
    --merchants   INT   Number of merchants (default: 5)
    --customers   INT   Number of customers (default: 100)
    --transactions INT  Number of transactions (default: 1000)
    --seed        INT   Random seed for reproducibility (default: 42)
    --database-url STR  SQLAlchemy async database URL (overrides .env)
"""
import sys
import os
import argparse
import asyncio

# Make sure the repo root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import insert, text

from app.core.config import settings
from ml.data.generators.payment_generator import PaymentDataGenerator

from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.models.payment_attempt import PaymentAttempt
from app.models.failure_event import FailureEvent
from app.models.recovery_action import RecoveryAction
from app.models.recovery_outcome import RecoveryOutcome
from app.models.audit_log import AuditLog
import app.models  # noqa: F401 — ensure metadata is populated


BATCH_SIZE = 500


async def bulk_insert(session: AsyncSession, model, rows: list[dict]) -> None:
    if not rows:
        return
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        await session.execute(insert(model), batch)


async def run(
    n_merchants: int,
    n_customers: int,
    n_transactions: int,
    seed: int,
    database_url: str,
) -> None:
    print(f"\n[PayResQ] Synthetic Data Generator")
    print(f"   Merchants:    {n_merchants}")
    print(f"   Customers:    {n_customers}")
    print(f"   Transactions: {n_transactions}")
    print(f"   Seed:         {seed}")
    print(f"   Database:     {database_url[:40]}...\n")

    generator = PaymentDataGenerator(seed=seed)
    data = generator.generate_all(
        n_merchants=n_merchants,
        n_customers=n_customers,
        n_transactions=n_transactions,
    )

    print(f"[OK] Generated in memory:")
    print(f"   Merchants:        {len(data['merchants'])}")
    print(f"   Customers:        {len(data['customers'])}")
    print(f"   Transactions:     {len(data['transactions'])}")
    print(f"   Payment Attempts: {len(data['payment_attempts'])}")
    print(f"   Failure Events:   {len(data['failure_events'])}")
    print(f"   Recovery Actions: {len(data['recovery_actions'])}")
    print(f"   Recovery Outcomes:{len(data['recovery_outcomes'])}")
    print(f"   Audit Logs:       {len(data['audit_logs'])}")
    print("")

    engine = create_async_engine(database_url, echo=False, future=True)

    # Create all tables if they don't exist (for SQLite dev usage)
    from app.core.db import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        async with session.begin():
            print(">> Inserting merchants...")
            await bulk_insert(session, Merchant, data["merchants"])
            print(">> Inserting customers...")
            await bulk_insert(session, Customer, data["customers"])
            print(">> Inserting transactions...")
            await bulk_insert(session, Transaction, data["transactions"])
            print(">> Inserting payment attempts...")
            await bulk_insert(session, PaymentAttempt, data["payment_attempts"])
            print(">> Inserting failure events...")
            await bulk_insert(session, FailureEvent, data["failure_events"])
            print(">> Inserting recovery actions...")
            await bulk_insert(session, RecoveryAction, data["recovery_actions"])
            print(">> Inserting recovery outcomes...")
            await bulk_insert(session, RecoveryOutcome, data["recovery_outcomes"])
            print(">> Inserting audit logs...")
            await bulk_insert(session, AuditLog, data["audit_logs"])

    await engine.dispose()
    print("\n[OK] All records inserted successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description="PayResQ Synthetic Data Generator")
    parser.add_argument("--merchants", type=int, default=5)
    parser.add_argument("--customers", type=int, default=100)
    parser.add_argument("--transactions", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--database-url", type=str, default=None)

    args = parser.parse_args()

    db_url = args.database_url or settings.async_database_url

    asyncio.run(
        run(
            n_merchants=args.merchants,
            n_customers=args.customers,
            n_transactions=args.transactions,
            seed=args.seed,
            database_url=db_url,
        )
    )


if __name__ == "__main__":
    main()
