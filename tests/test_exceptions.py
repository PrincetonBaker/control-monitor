"""Tests for exception management."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from ccm.exceptions import ExceptionManager


@pytest.fixture
def temp_exceptions_file():
    """Create a temporary exceptions file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    yield temp_path
    
    if temp_path.exists():
        temp_path.unlink()


def test_add_exception(temp_exceptions_file):
    """Test adding a risk exception."""
    manager = ExceptionManager(temp_exceptions_file)
    
    expiry = datetime.utcnow() + timedelta(days=30)
    exception = manager.add_exception(
        control_id="CCM-001",
        reason="Temporary exemption during migration",
        compensating_control="Manual review process in place",
        expiry_date=expiry,
        approver="Security Manager",
    )
    
    assert exception.id
    assert exception.control_id == "CCM-001"
    assert exception.reason == "Temporary exemption during migration"
    assert exception.is_valid()


def test_exception_persistence(temp_exceptions_file):
    """Test that exceptions are persisted to file."""
    manager1 = ExceptionManager(temp_exceptions_file)
    
    expiry = datetime.utcnow() + timedelta(days=30)
    exception = manager1.add_exception(
        control_id="CCM-002",
        reason="Legacy system",
        compensating_control="Network segmentation",
        expiry_date=expiry,
        approver="CTO",
    )
    
    manager2 = ExceptionManager(temp_exceptions_file)
    loaded_exception = manager2.get_exception(exception.id)
    
    assert loaded_exception is not None
    assert loaded_exception.control_id == "CCM-002"


def test_get_exceptions_for_control(temp_exceptions_file):
    """Test getting exceptions for a specific control."""
    manager = ExceptionManager(temp_exceptions_file)
    
    expiry = datetime.utcnow() + timedelta(days=30)
    manager.add_exception(
        control_id="CCM-003",
        reason="Reason 1",
        compensating_control="Comp 1",
        expiry_date=expiry,
        approver="Approver 1",
    )
    manager.add_exception(
        control_id="CCM-003",
        reason="Reason 2",
        compensating_control="Comp 2",
        expiry_date=expiry,
        approver="Approver 2",
    )
    
    exceptions = manager.get_exceptions_for_control("CCM-003")
    
    assert len(exceptions) == 2


def test_valid_exception_for_control(temp_exceptions_file):
    """Test getting valid exception for a control."""
    manager = ExceptionManager(temp_exceptions_file)
    
    valid_expiry = datetime.utcnow() + timedelta(days=30)
    expired_expiry = datetime.utcnow() - timedelta(days=1)
    
    manager.add_exception(
        control_id="CCM-004",
        reason="Expired",
        compensating_control="None",
        expiry_date=expired_expiry,
        approver="Someone",
    )
    
    valid_exception = manager.add_exception(
        control_id="CCM-004",
        reason="Valid",
        compensating_control="Active",
        expiry_date=valid_expiry,
        approver="Someone",
    )
    
    result = manager.get_valid_exception_for_control("CCM-004")
    
    assert result is not None
    assert result.id == valid_exception.id
    assert result.reason == "Valid"


def test_list_expired_exceptions(temp_exceptions_file):
    """Test listing expired exceptions."""
    manager = ExceptionManager(temp_exceptions_file)
    
    expired_expiry = datetime.utcnow() - timedelta(days=1)
    manager.add_exception(
        control_id="CCM-005",
        reason="Expired",
        compensating_control="None",
        expiry_date=expired_expiry,
        approver="Someone",
    )
    
    expired = manager.list_expired()
    
    assert len(expired) == 1
    assert expired[0].is_expired()


def test_list_valid_exceptions(temp_exceptions_file):
    """Test listing valid exceptions."""
    manager = ExceptionManager(temp_exceptions_file)
    
    valid_expiry = datetime.utcnow() + timedelta(days=30)
    manager.add_exception(
        control_id="CCM-006",
        reason="Valid",
        compensating_control="Active",
        expiry_date=valid_expiry,
        approver="Someone",
    )
    
    valid = manager.list_valid()
    
    assert len(valid) == 1
    assert valid[0].is_valid()


def test_exception_expiry():
    """Test exception expiry logic."""
    from ccm.models import RiskException
    
    expired = RiskException(
        id="test1",
        control_id="CCM-007",
        reason="Test",
        compensating_control="Test",
        expiry_date=datetime.utcnow() - timedelta(days=1),
        approver="Test",
    )
    
    valid = RiskException(
        id="test2",
        control_id="CCM-007",
        reason="Test",
        compensating_control="Test",
        expiry_date=datetime.utcnow() + timedelta(days=1),
        approver="Test",
    )
    
    assert expired.is_expired()
    assert not expired.is_valid()
    assert not valid.is_expired()
    assert valid.is_valid()
