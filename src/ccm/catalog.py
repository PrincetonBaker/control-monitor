"""Control catalog management."""

from pathlib import Path

import yaml

from ccm.models import Control, ControlCatalog


class CatalogManager:
    """Manage control catalog loading and querying."""

    def __init__(self, catalog_path: str = "controls.yaml"):
        self.catalog_path = Path(catalog_path)
        self.catalog: ControlCatalog | None = None

    def load_catalog(self) -> ControlCatalog:
        """Load control catalog from YAML."""
        with open(self.catalog_path) as f:
            data = yaml.safe_load(f)

        self.catalog = ControlCatalog(**data)
        return self.catalog

    def get_control(self, control_id: str) -> Control | None:
        """Get a specific control by ID."""
        if not self.catalog:
            self.load_catalog()

        for control in self.catalog.controls:
            if control.id == control_id:
                return control
        return None

    def get_controls_by_framework(self, framework: str) -> list[Control]:
        """Get all controls mapped to a framework."""
        if not self.catalog:
            self.load_catalog()

        results = []
        for control in self.catalog.controls:
            if any(fm.name.lower() == framework.lower() for fm in control.frameworks):
                results.append(control)

        return results

    def get_controls_by_category(self, category: str) -> list[Control]:
        """Get all controls in a category."""
        if not self.catalog:
            self.load_catalog()

        return [c for c in self.catalog.controls if c.category.lower() == category.lower()]

    def list_all_controls(self) -> list[Control]:
        """Get all controls."""
        if not self.catalog:
            self.load_catalog()

        return self.catalog.controls

    def list_frameworks(self) -> list[str]:
        """List all frameworks in the catalog."""
        if not self.catalog:
            self.load_catalog()

        frameworks = set()
        for control in self.catalog.controls:
            for fm in control.frameworks:
                frameworks.add(fm.name)

        return sorted(frameworks)
