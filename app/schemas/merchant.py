from datetime import datetime
from pydantic import BaseModel


class MerchantCreate(BaseModel):
    name: str
    is_active: bool = True


class MerchantResponse(BaseModel):
    id: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
