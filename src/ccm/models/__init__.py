"""Core data models for CCM."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Control severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class CheckStatus(str, Enum):
    """Control check result status."""

    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    ACCEPTED = "accepted"


class FrameworkMapping(BaseModel):
    """Framework-specific control mapping."""

    name: str
    controls: list[str]
    rationale: str


class Control(BaseModel):
    """A compliance control definition."""

    id: str
    title: str
    description: str
    category: str
    severity: Severity
    intent: str
    test_procedure: str
    evidence_expected: str
    frameworks: list[FrameworkMapping]


class ControlCatalog(BaseModel):
    """Collection of controls."""

    version: str
    description: str
    controls: list[Control]


class Evidence(BaseModel):
    """Evidence artifact from a control check."""

    control_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: CheckStatus
    collector: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class Exception(BaseModel):
    """Risk exception for a failing control."""

    id: str
    control_id: str
    reason: str
    compensating_control: str
    expiry_date: datetime
    approver: str
    created_date: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    def is_expired(self) -> bool:
        """Check if exception has expired."""
        return datetime.utcnow() > self.expiry_date

    def is_valid(self) -> bool:
        """Check if exception is valid and not expired."""
        return self.is_active and not self.is_expired()

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ScanResult(BaseModel):
    """Results from a control scan."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    evidence: list[Evidence]
    exceptions_applied: list[str] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
