"""Tests for catalog management."""

from pathlib import Path

import pytest

from ccm.catalog import filter_by_framework, get_control_by_id, load_catalog
from ccm.models import ControlCatalog


def test_load_catalog():
    """Test loading the control catalog."""
    catalog = load_catalog()
    
    assert isinstance(catalog, ControlCatalog)
    assert len(catalog.controls) > 0
    assert all(c.id.startswith("CCM-") for c in catalog.controls)


def test_catalog_has_required_fields():
    """Test that controls have all required fields."""
    catalog = load_catalog()
    
    for control in catalog.controls:
        assert control.id
        assert control.title
        assert control.intent
        assert control.test_procedure
        assert control.evidence_expected
        assert control.severity
        assert control.category
        assert len(control.frameworks) > 0


def test_filter_by_framework_soc2():
    """Test filtering controls by SOC2 framework."""
    catalog = load_catalog()
    soc2_controls = filter_by_framework(catalog, "SOC2")
    
    assert len(soc2_controls) > 0
    for control in soc2_controls:
        assert any(fm.framework.upper() == "SOC2" for fm in control.frameworks)


def test_filter_by_framework_iso27001():
    """Test filtering controls by ISO27001 framework."""
    catalog = load_catalog()
    iso_controls = filter_by_framework(catalog, "ISO27001")
    
    assert len(iso_controls) > 0
    for control in iso_controls:
        assert any(fm.framework.upper() == "ISO27001" for fm in control.frameworks)


def test_filter_by_framework_case_insensitive():
    """Test that framework filtering is case insensitive."""
    catalog = load_catalog()
    
    upper = filter_by_framework(catalog, "SOC2")
    lower = filter_by_framework(catalog, "soc2")
    
    assert len(upper) == len(lower)


def test_get_control_by_id():
    """Test getting a specific control by ID."""
    catalog = load_catalog()
    control = get_control_by_id(catalog, "CCM-001")
    
    assert control is not None
    assert control.id == "CCM-001"


def test_get_control_by_id_not_found():
    """Test getting a non-existent control."""
    catalog = load_catalog()
    control = get_control_by_id(catalog, "CCM-999")
    
    assert control is None


def test_framework_mappings():
    """Test that controls map to multiple frameworks."""
    catalog = load_catalog()
    
    multi_framework_controls = [
        c for c in catalog.controls if len(c.frameworks) > 1
    ]
    
    assert len(multi_framework_controls) > 0
