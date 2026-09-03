from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.schemas.payment_attempt import PaymentAttemptResponse
from app.schemas.recovery_action import RecoveryActionResponse
from app.services import transaction_service, merchant_service, customer_service

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[TransactionResponse]:
    transactions = await transaction_service.list_transactions(
        db, limit=limit, offset=offset, status=status
    )
    return [TransactionResponse.model_validate(t) for t in transactions]


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
) -> TransactionResponse:
    merchant = await merchant_service.get_merchant_by_id(db, data.merchant_id)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant {data.merchant_id} not found",
        )
    customer = await customer_service.get_customer_by_id(db, data.customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {data.customer_id} not found",
        )
    transaction = await transaction_service.create_transaction(db, data)
    return TransactionResponse.model_validate(transaction)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
) -> TransactionResponse:
    transaction = await transaction_service.get_transaction_by_id(db, transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found",
        )
    return TransactionResponse.model_validate(transaction)


@router.get("/{transaction_id}/attempts", response_model=list[PaymentAttemptResponse])
async def get_transaction_attempts(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[PaymentAttemptResponse]:
    transaction = await transaction_service.get_transaction_by_id(db, transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found",
        )
    attempts = await transaction_service.get_payment_attempts(db, transaction_id)
    return [PaymentAttemptResponse.model_validate(a) for a in attempts]


@router.get("/{transaction_id}/recovery-actions", response_model=list[RecoveryActionResponse])
async def get_recovery_actions(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[RecoveryActionResponse]:
    transaction = await transaction_service.get_transaction_by_id(db, transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found",
        )
    actions = await transaction_service.get_recovery_actions(db, transaction_id)
    return [RecoveryActionResponse.model_validate(a) for a in actions]
