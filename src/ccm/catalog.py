"""Control catalog management."""

import yaml
from pathlib import Path
from typing import Optional

from ccm.models import Control, ControlCatalog


def load_catalog(catalog_path: Optional[Path] = None) -> ControlCatalog:
    """Load control catalog from YAML file.
    
    Args:
        catalog_path: Path to catalog YAML. If None, uses default controls.yaml
        
    Returns:
        Loaded control catalog
    """
    if catalog_path is None:
        catalog_path = Path(__file__).parent.parent.parent / "controls.yaml"
    
    with open(catalog_path, "r") as f:
        data = yaml.safe_load(f)
    
    return ControlCatalog(**data)


def filter_by_framework(catalog: ControlCatalog, framework: str) -> list[Control]:
    """Filter controls by framework.
    
    Args:
        catalog: Control catalog
        framework: Framework name (e.g., 'SOC2', 'ISO27001')
        
    Returns:
        List of controls that map to the specified framework
    """
    filtered = []
    for control in catalog.controls:
        for mapping in control.frameworks:
            if mapping.framework.upper() == framework.upper():
                filtered.append(control)
                break
    return filtered


def get_control_by_id(catalog: ControlCatalog, control_id: str) -> Optional[Control]:
    """Get a specific control by ID.
    
    Args:
        catalog: Control catalog
        control_id: Control identifier
        
    Returns:
        Control if found, None otherwise
    """
    for control in catalog.controls:
        if control.id == control_id:
            return control
    return None
