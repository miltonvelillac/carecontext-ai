from enum import StrEnum

from pydantic import BaseModel, Field


class SafetyRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRISIS = "crisis"


class SafetyAction(StrEnum):
    ALLOW = "allow"
    CAVEAT = "caveat"
    REDIRECT = "redirect"


class SafetyAssessment(BaseModel):
    risk_level: SafetyRiskLevel = SafetyRiskLevel.LOW
    action: SafetyAction = SafetyAction.ALLOW
    disclaimer: str = "Educational information only. Not medical advice."
    reasons: list[str] = Field(default_factory=list)
    escalation_message: str | None = None

