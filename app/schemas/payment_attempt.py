from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.enums import PaymentAttemptStatus, PaymentMethod, FailureReason


class PaymentAttemptResponse(BaseModel):
    id: str
    transaction_id: str
    attempt_number: int
    payment_method: PaymentMethod
    bank: str
    status: PaymentAttemptStatus
    failure_reason: Optional[FailureReason]
    attempted_at: datetime

    model_config = {"from_attributes": True}
