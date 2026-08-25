"""Base collector interface and registry."""

from abc import ABC, abstractmethod
from typing import Any

from ccm.models import CheckStatus, Evidence


class Collector(ABC):
    """Base class for all control collectors."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize collector with optional configuration."""
        self.config = config or {}

    @property
    @abstractmethod
    def control_id(self) -> str:
        """Return the control ID this collector checks."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return collector name for identification."""
        pass

    @abstractmethod
    def collect(self) -> Evidence:
        """Execute the control check and return evidence."""
        pass

    def _create_evidence(
        self,
        status: CheckStatus,
        message: str,
        details: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> Evidence:
        """Helper to create evidence with standard fields."""
        return Evidence(
            control_id=self.control_id,
            status=status,
            collector=self.name,
            message=message,
            details=details or {},
            error=error,
        )


class CollectorRegistry:
    """Registry for discovering and instantiating collectors."""

    def __init__(self):
        self._collectors: dict[str, type[Collector]] = {}

    def register(self, collector_class: type[Collector]) -> None:
        """Register a collector class."""
        instance = collector_class()
        self._collectors[instance.control_id] = collector_class

    def get_collector(self, control_id: str, config: dict[str, Any] | None = None) -> Collector:
        """Get an instantiated collector for a control."""
        if control_id not in self._collectors:
            raise ValueError(f"No collector registered for control {control_id}")
        return self._collectors[control_id](config)

    def get_all_collectors(self, config: dict[str, Any] | None = None) -> list[Collector]:
        """Get all registered collectors."""
        return [cls(config) for cls in self._collectors.values()]

    def list_control_ids(self) -> list[str]:
        """List all registered control IDs."""
        return list(self._collectors.keys())


registry = CollectorRegistry()
