from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class CustomerCreate(BaseModel):
    merchant_id: str
    external_customer_id: str
    name: str
    email: Optional[str] = None


class CustomerResponse(BaseModel):
    id: str
    merchant_id: str
    external_customer_id: str
    name: str
    email: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
