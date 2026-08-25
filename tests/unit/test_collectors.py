"""Tests for collector base classes."""

from ccm.collectors.base import Collector, CollectorRegistry
from ccm.models import CheckStatus, Evidence


class TestCollector(Collector):
    """Test collector implementation."""

    @property
    def control_id(self) -> str:
        return "TEST-001"

    @property
    def name(self) -> str:
        return "test_collector"

    def collect(self) -> Evidence:
        return self._create_evidence(
            status=CheckStatus.PASS,
            message="Test passed",
            details={"test": "data"},
        )


class FailingTestCollector(Collector):
    """Test collector that fails."""

    @property
    def control_id(self) -> str:
        return "TEST-002"

    @property
    def name(self) -> str:
        return "failing_test_collector"

    def collect(self) -> Evidence:
        return self._create_evidence(
            status=CheckStatus.FAIL,
            message="Test failed",
            details={"reason": "intentional failure"},
        )


def test_collector_creation():
    """Test collector instantiation."""
    collector = TestCollector()
    assert collector.control_id == "TEST-001"
    assert collector.name == "test_collector"


def test_collector_collect():
    """Test collector execution."""
    collector = TestCollector()
    evidence = collector.collect()

    assert evidence.control_id == "TEST-001"
    assert evidence.status == CheckStatus.PASS
    assert evidence.collector == "test_collector"


def test_failing_collector():
    """Test collector that fails."""
    collector = FailingTestCollector()
    evidence = collector.collect()

    assert evidence.status == CheckStatus.FAIL
    assert "failed" in evidence.message.lower()


def test_registry():
    """Test collector registry."""
    registry = CollectorRegistry()
    registry.register(TestCollector)
    registry.register(FailingTestCollector)

    assert "TEST-001" in registry.list_control_ids()
    assert "TEST-002" in registry.list_control_ids()

    collector = registry.get_collector("TEST-001")
    assert isinstance(collector, TestCollector)


def test_registry_get_all():
    """Test getting all collectors from registry."""
    registry = CollectorRegistry()
    registry.register(TestCollector)
    registry.register(FailingTestCollector)

    collectors = registry.get_all_collectors()
    assert len(collectors) == 2
