"""Tests for core models."""

from datetime import datetime, timedelta

import pytest

from ccm.models import CheckStatus, Control, ControlCatalog, Evidence, Exception, Severity


def test_control_creation():
    """Test control model creation."""
    control = Control(
        id="TEST-001",
        title="Test Control",
        description="A test control",
        category="Testing",
        severity=Severity.HIGH,
        intent="Test intent",
        test_procedure="Test procedure",
        evidence_expected="Test evidence",
        frameworks=[],
    )

    assert control.id == "TEST-001"
    assert control.severity == Severity.HIGH


def test_evidence_creation():
    """Test evidence model creation."""
    evidence = Evidence(
        control_id="TEST-001",
        status=CheckStatus.PASS,
        collector="test_collector",
        message="Test passed",
        details={"key": "value"},
    )

    assert evidence.control_id == "TEST-001"
    assert evidence.status == CheckStatus.PASS
    assert evidence.details["key"] == "value"


def test_exception_validation():
    """Test exception expiry logic."""
    future_date = datetime.utcnow() + timedelta(days=30)
    past_date = datetime.utcnow() - timedelta(days=1)

    valid_exception = Exception(
        id="exc-001",
        control_id="TEST-001",
        reason="Testing",
        compensating_control="Alternative control",
        expiry_date=future_date,
        approver="Test Approver",
    )

    expired_exception = Exception(
        id="exc-002",
        control_id="TEST-002",
        reason="Testing",
        compensating_control="Alternative control",
        expiry_date=past_date,
        approver="Test Approver",
    )

    assert valid_exception.is_valid() is True
    assert expired_exception.is_valid() is False
    assert expired_exception.is_expired() is True


def test_exception_inactive():
    """Test inactive exception."""
    future_date = datetime.utcnow() + timedelta(days=30)

    exception = Exception(
        id="exc-003",
        control_id="TEST-003",
        reason="Testing",
        compensating_control="Alternative control",
        expiry_date=future_date,
        approver="Test Approver",
        is_active=False,
    )

    assert exception.is_valid() is False
