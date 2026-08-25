"""Control scanning engine."""

from typing import Optional

from ccm.catalog import CatalogManager
from ccm.collectors import registry
from ccm.evidence import EvidenceStore
from ccm.exceptions import ExceptionManager
from ccm.models import CheckStatus, Evidence, ScanResult


class Scanner:
    """Execute control checks and manage results."""

    def __init__(
        self,
        catalog_path: str = "controls.yaml",
        evidence_dir: str = "evidence",
        exceptions_file: str = "exceptions.json",
        config: dict | None = None,
    ):
        self.catalog_manager = CatalogManager(catalog_path)
        self.evidence_store = EvidenceStore(evidence_dir)
        self.exception_manager = ExceptionManager(exceptions_file)
        self.config = config or {}

    def scan_all(self) -> ScanResult:
        """Scan all registered controls."""
        self.catalog_manager.load_catalog()
        control_ids = registry.list_control_ids()
        return self._execute_scan(control_ids)

    def scan_control(self, control_id: str) -> ScanResult:
        """Scan a specific control."""
        return self._execute_scan([control_id])

    def scan_framework(self, framework: str) -> ScanResult:
        """Scan all controls for a framework."""
        controls = self.catalog_manager.get_controls_by_framework(framework)
        control_ids = [c.id for c in controls]
        return self._execute_scan(control_ids)

    def scan_category(self, category: str) -> ScanResult:
        """Scan all controls in a category."""
        controls = self.catalog_manager.get_controls_by_category(category)
        control_ids = [c.id for c in controls]
        return self._execute_scan(control_ids)

    def _execute_scan(self, control_ids: list[str]) -> ScanResult:
        """Execute scan for specified controls."""
        evidence_list = []
        exceptions_applied = []

        for control_id in control_ids:
            try:
                collector = registry.get_collector(control_id, self.config)
                evidence = collector.collect()

                exception = self.exception_manager.get_exception_for_control(control_id)
                if exception and evidence.status == CheckStatus.FAIL:
                    evidence.status = CheckStatus.ACCEPTED
                    evidence.message += f" (Exception {exception.id}: {exception.reason})"
                    evidence.details["exception_id"] = exception.id
                    evidence.details["compensating_control"] = exception.compensating_control
                    exceptions_applied.append(exception.id)

                evidence_list.append(evidence)
                self.evidence_store.store_evidence(evidence)

            except ValueError:
                continue

        summary = self._compute_summary(evidence_list)

        return ScanResult(
            evidence=evidence_list,
            exceptions_applied=exceptions_applied,
            summary=summary,
        )

    def _compute_summary(self, evidence_list: list[Evidence]) -> dict[str, int]:
        """Compute summary statistics from evidence."""
        summary = {
            "total": len(evidence_list),
            "pass": 0,
            "fail": 0,
            "error": 0,
            "accepted": 0,
        }

        for evidence in evidence_list:
            summary[evidence.status.value] += 1

        return summary

    def get_failing_controls(
        self, scan_result: ScanResult, include_accepted: bool = False
    ) -> list[Evidence]:
        """Get evidence for failing controls."""
        statuses = [CheckStatus.FAIL]
        if not include_accepted:
            return [e for e in scan_result.evidence if e.status in statuses]
        else:
            statuses.append(CheckStatus.ACCEPTED)
            return [e for e in scan_result.evidence if e.status in statuses]
