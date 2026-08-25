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
        exceptions_path = f.name

    yield exceptions_path

    if Path(exceptions_path).exists():
        Path(exceptions_path).unlink()


def test_add_exception(temp_exceptions_file):
    """Test adding an exception."""
    manager = ExceptionManager(temp_exceptions_file)
    future_date = datetime.utcnow() + timedelta(days=30)

    exception = manager.add_exception(
        control_id="TEST-001",
        reason="Testing exception",
        compensating_control="Manual review",
        expiry_date=future_date,
        approver="Test Manager",
    )

    assert exception.control_id == "TEST-001"
    assert exception.is_valid()


def test_get_exception_for_control(temp_exceptions_file):
    """Test retrieving exception for a control."""
    manager = ExceptionManager(temp_exceptions_file)
    future_date = datetime.utcnow() + timedelta(days=30)

    manager.add_exception(
        control_id="TEST-001",
        reason="Testing",
        compensating_control="Manual review",
        expiry_date=future_date,
        approver="Test Manager",
    )

    exception = manager.get_exception_for_control("TEST-001")
    assert exception is not None
    assert exception.control_id == "TEST-001"

    no_exception = manager.get_exception_for_control("TEST-999")
    assert no_exception is None


def test_expired_exception(temp_exceptions_file):
    """Test expired exception is not returned."""
    manager = ExceptionManager(temp_exceptions_file)
    past_date = datetime.utcnow() - timedelta(days=1)

    manager.add_exception(
        control_id="TEST-001",
        reason="Testing",
        compensating_control="Manual review",
        expiry_date=past_date,
        approver="Test Manager",
    )

    exception = manager.get_exception_for_control("TEST-001")
    assert exception is None


def test_list_exceptions(temp_exceptions_file):
    """Test listing exceptions."""
    manager = ExceptionManager(temp_exceptions_file)
    future_date = datetime.utcnow() + timedelta(days=30)

    manager.add_exception(
        control_id="TEST-001",
        reason="Testing 1",
        compensating_control="Manual review",
        expiry_date=future_date,
        approver="Manager 1",
    )

    manager.add_exception(
        control_id="TEST-002",
        reason="Testing 2",
        compensating_control="Alternative control",
        expiry_date=future_date,
        approver="Manager 2",
    )

    all_exceptions = manager.list_exceptions()
    assert len(all_exceptions) == 2

    filtered = manager.list_exceptions(control_id="TEST-001")
    assert len(filtered) == 1
    assert filtered[0].control_id == "TEST-001"


def test_deactivate_exception(temp_exceptions_file):
    """Test deactivating an exception."""
    manager = ExceptionManager(temp_exceptions_file)
    future_date = datetime.utcnow() + timedelta(days=30)

    exception = manager.add_exception(
        control_id="TEST-001",
        reason="Testing",
        compensating_control="Manual review",
        expiry_date=future_date,
        approver="Test Manager",
    )

    result = manager.deactivate_exception(exception.id)
    assert result is True

    active_exception = manager.get_exception_for_control("TEST-001")
    assert active_exception is None
