from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, condecimal
from app.models.enums import TransactionStatus


class TransactionCreate(BaseModel):
    merchant_id: str
    customer_id: str
    external_transaction_id: str
    amount: Decimal
    currency: str = "INR"


class TransactionResponse(BaseModel):
    id: str
    merchant_id: str
    customer_id: str
    external_transaction_id: str
    amount: Decimal
    currency: str
    status: TransactionStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
