"""Control scanning engine."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from ccm.catalog import filter_by_framework, get_control_by_id, load_catalog
from ccm.collectors import (
    AWSCollector,
    Collector,
    EndpointCollector,
    GitHubCollector,
    OktaCollector,
)
from ccm.exceptions import ExceptionManager
from ccm.models import CheckResult, Control, ControlCatalog, ScanResult


class Scanner:
    """Control scanning engine."""

    def __init__(
        self,
        catalog: Optional[ControlCatalog] = None,
        exceptions_file: Optional[Path] = None,
        use_fixtures: bool = True,
    ):
        """Initialize scanner.
        
        Args:
            catalog: Control catalog. If None, loads default
            exceptions_file: Path to exceptions file
            use_fixtures: If True, use fixture data
        """
        self.catalog = catalog or load_catalog()
        self.use_fixtures = use_fixtures
        
        if exceptions_file is None:
            exceptions_file = Path.cwd() / "exceptions.json"
        self.exception_manager = ExceptionManager(exceptions_file)
        
        self.collectors: list[Collector] = [
            AWSCollector(use_fixtures=use_fixtures),
            OktaCollector(use_fixtures=use_fixtures),
            GitHubCollector(use_fixtures=use_fixtures),
            EndpointCollector(use_fixtures=use_fixtures),
        ]

    def scan_all(self) -> ScanResult:
        """Scan all controls.
        
        Returns:
            Scan results
        """
        return self._scan_controls(self.catalog.controls)

    def scan_by_framework(self, framework: str) -> ScanResult:
        """Scan controls for a specific framework.
        
        Args:
            framework: Framework name (e.g., 'SOC2', 'ISO27001')
            
        Returns:
            Scan results
        """
        controls = filter_by_framework(self.catalog, framework)
        return self._scan_controls(controls)

    def scan_control(self, control_id: str) -> ScanResult:
        """Scan a specific control.
        
        Args:
            control_id: Control identifier
            
        Returns:
            Scan results
        """
        control = get_control_by_id(self.catalog, control_id)
        if control is None:
            check = CheckResult(
                control_id=control_id,
                status="error",
                details=f"Control {control_id} not found",
            )
            result = ScanResult(checks=[check])
            result.calculate_summary()
            return result
        
        return self._scan_controls([control])

    def _scan_controls(self, controls: list[Control]) -> ScanResult:
        """Scan a list of controls.
        
        Args:
            controls: List of controls to scan
            
        Returns:
            Scan results
        """
        checks = []
        
        for control in controls:
            check = self._check_control(control)
            checks.append(check)
        
        result = ScanResult(checks=checks)
        result.calculate_summary()
        return result

    def _check_control(self, control: Control) -> CheckResult:
        """Check a single control.
        
        Args:
            control: Control to check
            
        Returns:
            Check result
        """
        collector = self._find_collector(control)
        
        if collector is None:
            return CheckResult(
                control_id=control.id,
                status="error",
                details=f"No collector supports control {control.id}",
            )
        
        try:
            check = collector.collect(control)
            
            if check.status == "fail":
                exception = self.exception_manager.get_valid_exception_for_control(
                    control.id
                )
                if exception:
                    check.status = "excepted"
                    check.exception_id = exception.id
                    check.details += f" (Exception: {exception.reason})"
            
            return check
        except Exception as e:
            return CheckResult(
                control_id=control.id,
                status="error",
                details=f"Error checking control: {str(e)}",
            )

    def _find_collector(self, control: Control) -> Optional[Collector]:
        """Find collector that supports a control.
        
        Args:
            control: Control to find collector for
            
        Returns:
            Collector if found, None otherwise
        """
        for collector in self.collectors:
            if collector.supports_control(control):
                return collector
        return None
