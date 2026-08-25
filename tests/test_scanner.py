"""Tests for scanner."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from ccm.catalog import load_catalog
from ccm.exceptions import ExceptionManager
from ccm.scanner import Scanner


@pytest.fixture
def temp_exceptions_file():
    """Create a temporary exceptions file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    yield temp_path
    
    if temp_path.exists():
        temp_path.unlink()


def test_scan_all():
    """Test scanning all controls."""
    scanner = Scanner(use_fixtures=True)
    result = scanner.scan_all()
    
    assert len(result.checks) > 0
    assert result.summary["total"] > 0
    result.calculate_summary()
    assert result.summary["total"] == len(result.checks)


def test_scan_by_framework():
    """Test scanning by framework."""
    scanner = Scanner(use_fixtures=True)
    result = scanner.scan_by_framework("SOC2")
    
    assert len(result.checks) > 0
    catalog = load_catalog()
    
    for check in result.checks:
        control = next(c for c in catalog.controls if c.id == check.control_id)
        assert any(fm.framework.upper() == "SOC2" for fm in control.frameworks)


def test_scan_control():
    """Test scanning a specific control."""
    scanner = Scanner(use_fixtures=True)
    result = scanner.scan_control("CCM-001")
    
    assert len(result.checks) == 1
    assert result.checks[0].control_id == "CCM-001"


def test_scan_nonexistent_control():
    """Test scanning a non-existent control."""
    scanner = Scanner(use_fixtures=True)
    result = scanner.scan_control("CCM-999")
    
    assert len(result.checks) == 1
    assert result.checks[0].status == "error"


def test_scan_with_exception(temp_exceptions_file):
    """Test that exceptions are applied to failing controls."""
    catalog = load_catalog()
    scanner = Scanner(
        catalog=catalog, exceptions_file=temp_exceptions_file, use_fixtures=True
    )
    
    expiry = datetime.utcnow() + timedelta(days=30)
    scanner.exception_manager.add_exception(
        control_id="CCM-002",
        reason="Migration in progress",
        compensating_control="Manual monitoring",
        expiry_date=expiry,
        approver="CISO",
    )
    
    result = scanner.scan_control("CCM-002")
    
    check = result.checks[0]
    if check.status in ("fail", "excepted"):
        assert check.status == "excepted"
        assert check.exception_id is not None


def test_scan_result_summary():
    """Test scan result summary calculation."""
    scanner = Scanner(use_fixtures=True)
    result = scanner.scan_all()
    
    result.calculate_summary()
    
    assert "total" in result.summary
    assert "pass" in result.summary
    assert "fail" in result.summary
    assert "error" in result.summary
    assert "excepted" in result.summary
    
    assert (
        result.summary["pass"]
        + result.summary["fail"]
        + result.summary["error"]
        + result.summary["excepted"]
        == result.summary["total"]
    )


def test_has_failures():
    """Test failure detection."""
    scanner = Scanner(use_fixtures=True)
    result = scanner.scan_all()
    
    has_any_fails = any(c.status == "fail" for c in result.checks)
    
    assert result.has_failures(include_excepted=False) == has_any_fails


def test_has_critical_or_high_failures():
    """Test critical/high failure detection."""
    catalog = load_catalog()
    scanner = Scanner(catalog=catalog, use_fixtures=True)
    result = scanner.scan_all()
    
    control_map = {c.id: c for c in catalog.controls}
    has_critical_high = any(
        c.status == "fail"
        and control_map[c.control_id].severity.value in ("critical", "high")
        for c in result.checks
        if c.control_id in control_map
    )
    
    assert result.has_critical_or_high_failures(catalog) == has_critical_high


def test_evidence_collection():
    """Test that evidence is collected."""
    scanner = Scanner(use_fixtures=True)
    result = scanner.scan_control("CCM-001")
    
    check = result.checks[0]
    assert check.evidence is not None
    assert isinstance(check.evidence, dict)
    assert len(check.evidence) > 0
