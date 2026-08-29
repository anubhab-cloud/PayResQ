from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate


async def create_customer(db: AsyncSession, data: CustomerCreate) -> Customer:
    customer = Customer(
        merchant_id=data.merchant_id,
        external_customer_id=data.external_customer_id,
        name=data.name,
        email=data.email,
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


async def get_customer_by_id(db: AsyncSession, customer_id: str) -> Optional[Customer]:
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    return result.scalar_one_or_none()
