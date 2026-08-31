"""
app/schemas/dashboard.py
=========================
Pydantic schemas for dashboard aggregation and demo endpoints.
"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class DashboardSummaryResponse(BaseModel):
    revenue_at_risk: float
    recovered_revenue: float
    recovery_rate: float            # percentage e.g. 44.5
    total_transactions: int
    failed_transactions: int
    successful_transactions: int
    pending_human_approvals: int
    active_interventions: int
    note: str = "Live metrics calculated from database"


class DailyTrendPoint(BaseModel):
    date: str
    failed_volume: float
    recovered_volume: float
    failed_count: int
    recovered_count: int


class DashboardTrendsResponse(BaseModel):
    timeframe_days: int
    trends: list[DailyTrendPoint]


class BankFailureStat(BaseModel):
    bank: str
    failed_count: int
    total_count: int
    failure_rate: float


class MethodFailureStat(BaseModel):
    payment_method: str
    failed_count: int
    total_count: int
    failure_rate: float


class DashboardFailureBreakdownResponse(BaseModel):
    by_bank: list[BankFailureStat]
    by_method: list[MethodFailureStat]


class DemoRunResponse(BaseModel):
    transaction_id: str
    amount: float
    bank: str
    payment_method: str
    failure_reason: str
    agent_action: str
    agent_confidence: float
    policy_outcome: str
    job_id: Optional[str] = None
    execution_success: Optional[bool] = None
    recovered_amount: Optional[float] = None
    status: str
