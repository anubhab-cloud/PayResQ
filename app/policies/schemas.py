"""
app/policies/schemas.py
========================
Pydantic schemas for policy engine inputs and outputs.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class PolicyOutcome(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


class PolicyDecision(BaseModel):
    outcome: PolicyOutcome
    reason: str
    policy_version: str = "v1"
    rule_triggered: Optional[str] = None   # name of the rule that made the decision
