"""Tests for catalog management."""

import tempfile
from pathlib import Path

import pytest
import yaml

from ccm.catalog import CatalogManager
from ccm.models import Severity


@pytest.fixture
def test_catalog_file():
    """Create a temporary test catalog."""
    catalog_data = {
        "version": "1.0",
        "description": "Test catalog",
        "controls": [
            {
                "id": "TEST-001",
                "title": "Test Control 1",
                "description": "First test control",
                "category": "Testing",
                "severity": "high",
                "intent": "Test intent",
                "test_procedure": "Test procedure",
                "evidence_expected": "Test evidence",
                "frameworks": [
                    {"name": "SOC2", "controls": ["CC6.1"], "rationale": "Test rationale"}
                ],
            },
            {
                "id": "TEST-002",
                "title": "Test Control 2",
                "description": "Second test control",
                "category": "Security",
                "severity": "critical",
                "intent": "Test intent",
                "test_procedure": "Test procedure",
                "evidence_expected": "Test evidence",
                "frameworks": [
                    {"name": "ISO27001:2022", "controls": ["A.5.15"], "rationale": "Test rationale"}
                ],
            },
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(catalog_data, f)
        catalog_path = f.name

    yield catalog_path

    Path(catalog_path).unlink()


def test_catalog_loading(test_catalog_file):
    """Test catalog loading from YAML."""
    manager = CatalogManager(test_catalog_file)
    catalog = manager.load_catalog()

    assert catalog.version == "1.0"
    assert len(catalog.controls) == 2


def test_get_control(test_catalog_file):
    """Test retrieving a specific control."""
    manager = CatalogManager(test_catalog_file)
    manager.load_catalog()

    control = manager.get_control("TEST-001")
    assert control is not None
    assert control.title == "Test Control 1"

    missing = manager.get_control("NONEXISTENT")
    assert missing is None


def test_get_controls_by_framework(test_catalog_file):
    """Test filtering controls by framework."""
    manager = CatalogManager(test_catalog_file)
    manager.load_catalog()

    soc2_controls = manager.get_controls_by_framework("SOC2")
    assert len(soc2_controls) == 1
    assert soc2_controls[0].id == "TEST-001"


def test_get_controls_by_category(test_catalog_file):
    """Test filtering controls by category."""
    manager = CatalogManager(test_catalog_file)
    manager.load_catalog()

    testing_controls = manager.get_controls_by_category("Testing")
    assert len(testing_controls) == 1
    assert testing_controls[0].id == "TEST-001"


def test_list_frameworks(test_catalog_file):
    """Test listing all frameworks."""
    manager = CatalogManager(test_catalog_file)
    manager.load_catalog()

    frameworks = manager.list_frameworks()
    assert "SOC2" in frameworks
    assert "ISO27001:2022" in frameworks
