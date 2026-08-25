"""Data models for CCM."""

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


class FrameworkMapping(BaseModel):
    """Framework control mapping."""

    framework: str
    controls: list[str]


class Control(BaseModel):
    """Control definition."""

    id: str
    title: str
    intent: str
    test_procedure: str
    evidence_expected: str
    severity: Severity
    category: str
    frameworks: list[FrameworkMapping]


class ControlCatalog(BaseModel):
    """Collection of controls."""

    controls: list[Control]


class CheckResult(BaseModel):
    """Result of a control check."""

    control_id: str
    status: str  # "pass", "fail", "error", "excepted"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: str = ""
    evidence: dict[str, Any] = Field(default_factory=dict)
    exception_id: Optional[str] = None


class RiskException(BaseModel):
    """Risk acceptance exception."""

    id: str
    control_id: str
    reason: str
    compensating_control: str
    expiry_date: datetime
    approver: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def is_expired(self) -> bool:
        """Check if exception has expired."""
        return datetime.utcnow() > self.expiry_date

    def is_valid(self) -> bool:
        """Check if exception is valid (not expired)."""
        return not self.is_expired()


class ScanResult(BaseModel):
    """Results from a scan."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: list[CheckResult]
    summary: dict[str, int] = Field(default_factory=dict)

    def calculate_summary(self) -> None:
        """Calculate summary statistics."""
        self.summary = {
            "total": len(self.checks),
            "pass": sum(1 for c in self.checks if c.status == "pass"),
            "fail": sum(1 for c in self.checks if c.status == "fail"),
            "error": sum(1 for c in self.checks if c.status == "error"),
            "excepted": sum(1 for c in self.checks if c.status == "excepted"),
        }

    def has_failures(self, include_excepted: bool = False) -> bool:
        """Check if there are any failures."""
        if include_excepted:
            return any(c.status in ("fail", "excepted") for c in self.checks)
        return any(c.status == "fail" for c in self.checks)

    def has_critical_or_high_failures(
        self, catalog: "ControlCatalog", include_excepted: bool = False
    ) -> bool:
        """Check if there are critical or high severity failures."""
        control_map = {c.id: c for c in catalog.controls}
        for check in self.checks:
            if check.status == "fail" or (include_excepted and check.status == "excepted"):
                control = control_map.get(check.control_id)
                if control and control.severity in (Severity.CRITICAL, Severity.HIGH):
                    if check.status == "fail":
                        return True
        return False
