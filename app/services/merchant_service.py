from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.merchant import Merchant
from app.schemas.merchant import MerchantCreate


async def create_merchant(db: AsyncSession, data: MerchantCreate) -> Merchant:
    merchant = Merchant(name=data.name, is_active=data.is_active)
    db.add(merchant)
    await db.commit()
    await db.refresh(merchant)
    return merchant


async def get_merchant_by_id(db: AsyncSession, merchant_id: str) -> Optional[Merchant]:
    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    return result.scalar_one_or_none()
