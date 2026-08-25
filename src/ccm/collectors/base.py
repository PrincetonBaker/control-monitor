"""Base collector interface."""

from abc import ABC, abstractmethod
from typing import Any

from ccm.models import CheckResult, Control


class Collector(ABC):
    """Base class for control evidence collectors."""

    def __init__(self, use_fixtures: bool = True):
        """Initialize collector.
        
        Args:
            use_fixtures: If True, use fixture data. If False, use live API
        """
        self.use_fixtures = use_fixtures

    @abstractmethod
    def collect(self, control: Control) -> CheckResult:
        """Collect evidence for a control.
        
        Args:
            control: Control to check
            
        Returns:
            Check result with evidence
        """
        pass

    def supports_control(self, control: Control) -> bool:
        """Check if this collector supports a control.
        
        Args:
            control: Control to check
            
        Returns:
            True if collector can check this control
        """
        return control.id in self.get_supported_controls()

    @abstractmethod
    def get_supported_controls(self) -> list[str]:
        """Get list of control IDs this collector supports.
        
        Returns:
            List of control IDs
        """
        pass
