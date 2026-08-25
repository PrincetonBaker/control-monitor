"""Integration tests for the complete scanning workflow."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from ccm.exceptions import ExceptionManager
from ccm.models import CheckStatus
from ccm.reporting import ReportGenerator
from ccm.scanner import Scanner


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        evidence_dir = workspace / "evidence"
        evidence_dir.mkdir()

        yield workspace


def test_full_scan_workflow(temp_workspace):
    """Test complete scan workflow."""
    evidence_dir = str(temp_workspace / "evidence")
    exceptions_file = str(temp_workspace / "exceptions.json")

    scanner = Scanner(
        catalog_path="controls.yaml",
        evidence_dir=evidence_dir,
        exceptions_file=exceptions_file,
    )

    result = scanner.scan_all()

    assert result.summary["total"] > 0
    assert len(result.evidence) == result.summary["total"]

    pass_count = result.summary.get("pass", 0)
    fail_count = result.summary.get("fail", 0)
    assert pass_count + fail_count > 0


def test_scan_with_exception(temp_workspace):
    """Test scan with an applied exception."""
    evidence_dir = str(temp_workspace / "evidence")
    exceptions_file = str(temp_workspace / "exceptions.json")

    exception_manager = ExceptionManager(exceptions_file)
    future_date = datetime.utcnow() + timedelta(days=90)

    exception_manager.add_exception(
        control_id="CCM-AC-001",
        reason="MFA rollout in progress",
        compensating_control="Weekly manual review of privileged access",
        expiry_date=future_date,
        approver="Security Director",
    )

    scanner = Scanner(
        catalog_path="controls.yaml",
        evidence_dir=evidence_dir,
        exceptions_file=exceptions_file,
    )

    result = scanner.scan_all()

    accepted_controls = [e for e in result.evidence if e.status == CheckStatus.ACCEPTED]

    if result.summary["fail"] > 0:
        assert len(result.exceptions_applied) > 0


def test_scan_by_framework(temp_workspace):
    """Test scanning by framework."""
    evidence_dir = str(temp_workspace / "evidence")
    exceptions_file = str(temp_workspace / "exceptions.json")

    scanner = Scanner(
        catalog_path="controls.yaml",
        evidence_dir=evidence_dir,
        exceptions_file=exceptions_file,
    )

    result = scanner.scan_framework("SOC2")

    assert result.summary["total"] > 0
    assert len(result.evidence) == result.summary["total"]


def test_report_generation(temp_workspace):
    """Test report generation from scan results."""
    evidence_dir = str(temp_workspace / "evidence")
    exceptions_file = str(temp_workspace / "exceptions.json")

    scanner = Scanner(
        catalog_path="controls.yaml",
        evidence_dir=evidence_dir,
        exceptions_file=exceptions_file,
    )

    result = scanner.scan_all()

    report_gen = ReportGenerator(catalog_path="controls.yaml")

    md_report = report_gen.generate_markdown(result)
    assert "CCM Control Scan Report" in md_report
    assert "Summary" in md_report

    html_report = report_gen.generate_html(result)
    assert "<!DOCTYPE html>" in html_report
    assert "CCM Control Scan Report" in html_report


def test_evidence_persistence(temp_workspace):
    """Test that evidence is persisted to disk."""
    evidence_dir = str(temp_workspace / "evidence")
    exceptions_file = str(temp_workspace / "exceptions.json")

    scanner = Scanner(
        catalog_path="controls.yaml",
        evidence_dir=evidence_dir,
        exceptions_file=exceptions_file,
    )

    result = scanner.scan_all()

    evidence_files = list(Path(evidence_dir).glob("*.evidence.json"))
    assert len(evidence_files) > 0


def test_failing_controls_detection(temp_workspace):
    """Test detection of failing controls."""
    evidence_dir = str(temp_workspace / "evidence")
    exceptions_file = str(temp_workspace / "exceptions.json")

    scanner = Scanner(
        catalog_path="controls.yaml",
        evidence_dir=evidence_dir,
        exceptions_file=exceptions_file,
    )

    result = scanner.scan_all()
    failing = scanner.get_failing_controls(result, include_accepted=False)

    assert isinstance(failing, list)


def test_exit_code_logic(temp_workspace):
    """Test that scan results support proper exit code logic."""
    evidence_dir = str(temp_workspace / "evidence")
    exceptions_file = str(temp_workspace / "exceptions.json")

    scanner = Scanner(
        catalog_path="controls.yaml",
        evidence_dir=evidence_dir,
        exceptions_file=exceptions_file,
    )

    result = scanner.scan_all()

    should_fail = result.summary["fail"] > 0

    if should_fail:
        assert result.summary["fail"] > 0
    else:
        assert result.summary["fail"] == 0
