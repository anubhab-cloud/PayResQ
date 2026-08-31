"""
app/agents/schemas.py
======================
Pydantic schemas for the AI recovery agent's structured output.

The LLM MUST return a JSON object that conforms to AgentDecision.
Any deviation is caught at validation time and handled as a safe fallback.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.models.enums import RecoveryActionType


class AgentDecision(BaseModel):
    """Structured decision produced by the LLM recovery agent."""

    action: RecoveryActionType = Field(
        ..., description="The recommended recovery action."
    )
    delay_minutes: Optional[int] = Field(
        default=None,
        ge=1,
        le=480,
        description="Required for RETRY_AFTER_DELAY. Minutes to wait before retrying.",
    )
    reason: str = Field(
        ..., min_length=10, description="Human-readable explanation of the decision."
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Agent confidence in this decision (0–1)."
    )
    # Optional enrichment fields
    transaction_id: Optional[str] = None
    selected_probability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    root_cause: Optional[str] = None
    model_version: Optional[str] = None

    @field_validator("delay_minutes")
    @classmethod
    def delay_required_for_delayed_retry(
        cls, v: Optional[int], info
    ) -> Optional[int]:
        action = info.data.get("action")
        if action == RecoveryActionType.RETRY_AFTER_DELAY and (v is None or v < 1):
            raise ValueError(
                "delay_minutes must be >= 1 when action is RETRY_AFTER_DELAY"
            )
        return v


class AgentDecisionWithPolicy(AgentDecision):
    """Extended decision that includes a policy pre-check result (for API responses)."""
    policy_outcome: Optional[str] = None
    policy_reason: Optional[str] = None
