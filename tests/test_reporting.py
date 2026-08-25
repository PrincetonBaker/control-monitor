"""Tests for reporting."""

import json
import tempfile
from pathlib import Path

import pytest

from ccm.catalog import load_catalog
from ccm.reporting import export_evidence, generate_html_report, generate_markdown_report
from ccm.scanner import Scanner


def test_generate_markdown_report():
    """Test generating markdown report."""
    catalog = load_catalog()
    scanner = Scanner(catalog=catalog, use_fixtures=True)
    result = scanner.scan_control("CCM-001")
    
    report = generate_markdown_report(result, catalog)
    
    assert "Continuous Control Monitoring Report" in report
    assert "CCM-001" in report
    assert "Summary" in report


def test_generate_markdown_report_to_file():
    """Test generating markdown report to file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        output_path = Path(f.name)
    
    try:
        catalog = load_catalog()
        scanner = Scanner(catalog=catalog, use_fixtures=True)
        result = scanner.scan_control("CCM-001")
        
        generate_markdown_report(result, catalog, output_path)
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "Continuous Control Monitoring Report" in content
    finally:
        if output_path.exists():
            output_path.unlink()


def test_generate_html_report():
    """Test generating HTML report."""
    catalog = load_catalog()
    scanner = Scanner(catalog=catalog, use_fixtures=True)
    result = scanner.scan_control("CCM-001")
    
    html = generate_html_report(result, catalog)
    
    assert "<!DOCTYPE html>" in html
    assert "CCM-001" in html
    assert "Continuous Control Monitoring Report" in html


def test_generate_html_report_to_file():
    """Test generating HTML report to file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        output_path = Path(f.name)
    
    try:
        catalog = load_catalog()
        scanner = Scanner(catalog=catalog, use_fixtures=True)
        result = scanner.scan_control("CCM-001")
        
        generate_html_report(result, catalog, output_path)
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "<!DOCTYPE html>" in content
    finally:
        if output_path.exists():
            output_path.unlink()


def test_export_evidence():
    """Test exporting evidence to JSON."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        output_path = Path(f.name)
    
    try:
        scanner = Scanner(use_fixtures=True)
        result = scanner.scan_control("CCM-001")
        
        export_evidence(result, output_path)
        
        assert output_path.exists()
        
        with open(output_path, "r") as f:
            data = json.load(f)
        
        assert "checks" in data
        assert "summary" in data
        assert "timestamp" in data
    finally:
        if output_path.exists():
            output_path.unlink()


def test_report_includes_all_statuses():
    """Test that reports include all control statuses."""
    catalog = load_catalog()
    scanner = Scanner(catalog=catalog, use_fixtures=True)
    result = scanner.scan_all()
    
    html = generate_html_report(result, catalog)
    markdown = generate_markdown_report(result, catalog)
    
    for report in [html, markdown]:
        assert "pass" in report.lower() or "✅" in report
        if any(c.status == "fail" for c in result.checks):
            assert "fail" in report.lower() or "❌" in report


def test_report_includes_frameworks():
    """Test that reports include framework mappings."""
    catalog = load_catalog()
    scanner = Scanner(catalog=catalog, use_fixtures=True)
    result = scanner.scan_control("CCM-001")
    
    markdown = generate_markdown_report(result, catalog)
    html = generate_html_report(result, catalog)
    
    assert "SOC2" in markdown or "SOC 2" in markdown
    assert "SOC2" in html or "SOC 2" in html
