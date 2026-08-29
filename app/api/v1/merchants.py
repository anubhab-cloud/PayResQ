from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.schemas.merchant import MerchantCreate, MerchantResponse
from app.services import merchant_service

router = APIRouter(prefix="/merchants", tags=["Merchants"])


@router.post("", response_model=MerchantResponse, status_code=status.HTTP_201_CREATED)
async def create_merchant(
    data: MerchantCreate,
    db: AsyncSession = Depends(get_db),
) -> MerchantResponse:
    merchant = await merchant_service.create_merchant(db, data)
    return MerchantResponse.model_validate(merchant)
