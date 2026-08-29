from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.schemas.customer import CustomerCreate, CustomerResponse
from app.services import customer_service, merchant_service

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
) -> CustomerResponse:
    merchant = await merchant_service.get_merchant_by_id(db, data.merchant_id)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant {data.merchant_id} not found",
        )
    customer = await customer_service.create_customer(db, data)
    return CustomerResponse.model_validate(customer)
