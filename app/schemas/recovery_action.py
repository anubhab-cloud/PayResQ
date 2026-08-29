from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.enums import RecoveryActionType, RecoveryActionStatus


class RecoveryActionResponse(BaseModel):
    id: str
    transaction_id: str
    action_type: RecoveryActionType
    status: RecoveryActionStatus
    reason: Optional[str]
    confidence: Optional[float]
    scheduled_for: Optional[datetime]
    executed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}
