"""Tests for CLI."""

import json
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from ccm.cli import app

runner = CliRunner()


def test_cli_scan_all():
    """Test CLI scan all controls."""
    result = runner.invoke(app, ["scan", "--output", "console", "--no-exit-on-fail"])
    
    assert result.exit_code == 0
    assert "Summary" in result.stdout or "summary" in result.stdout.lower()


def test_cli_scan_framework():
    """Test CLI scan by framework."""
    result = runner.invoke(
        app, ["scan", "--framework", "SOC2", "--output", "console", "--no-exit-on-fail"]
    )
    
    assert result.exit_code == 0


def test_cli_scan_control():
    """Test CLI scan specific control."""
    result = runner.invoke(
        app, ["scan", "--control", "CCM-001", "--output", "console", "--no-exit-on-fail"]
    )
    
    assert result.exit_code == 0
    assert "CCM-001" in result.stdout


def test_cli_scan_json_output():
    """Test CLI scan with JSON output."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        output_path = f.name
    
    try:
        result = runner.invoke(
            app,
            [
                "scan",
                "--control",
                "CCM-001",
                "--output",
                "json",
                "--output-file",
                output_path,
                "--no-exit-on-fail",
            ],
        )
        
        assert result.exit_code == 0
        assert Path(output_path).exists()
        
        with open(output_path, "r") as f:
            data = json.load(f)
        assert "checks" in data
    finally:
        if Path(output_path).exists():
            Path(output_path).unlink()


def test_cli_scan_html_output():
    """Test CLI scan with HTML output."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        output_path = f.name
    
    try:
        result = runner.invoke(
            app,
            [
                "scan",
                "--control",
                "CCM-001",
                "--output",
                "html",
                "--output-file",
                output_path,
                "--no-exit-on-fail",
            ],
        )
        
        assert result.exit_code == 0
        assert Path(output_path).exists()
    finally:
        if Path(output_path).exists():
            Path(output_path).unlink()


def test_cli_list_controls():
    """Test CLI list controls."""
    result = runner.invoke(app, ["list-controls"])
    
    assert result.exit_code == 0
    assert "CCM-001" in result.stdout


def test_cli_list_controls_by_framework():
    """Test CLI list controls filtered by framework."""
    result = runner.invoke(app, ["list-controls", "--framework", "SOC2"])
    
    assert result.exit_code == 0
    assert "SOC2" in result.stdout or "SOC 2" in result.stdout


def test_cli_exception_list():
    """Test CLI exception list."""
    result = runner.invoke(app, ["exception", "list"])
    
    assert result.exit_code == 0


def test_cli_export_evidence():
    """Test CLI export evidence."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        output_path = f.name
    
    try:
        result = runner.invoke(
            app,
            ["export-evidence-cmd", "--control", "CCM-001", "--output", output_path],
        )
        
        assert result.exit_code == 0
        assert Path(output_path).exists()
    finally:
        if Path(output_path).exists():
            Path(output_path).unlink()
