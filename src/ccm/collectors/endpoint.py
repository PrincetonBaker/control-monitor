"""Endpoint control collectors."""

import json
from pathlib import Path

from ccm.collectors.base import Collector
from ccm.models import CheckResult, Control


class EndpointCollector(Collector):
    """Collector for endpoint controls."""

    def get_supported_controls(self) -> list[str]:
        """Get supported control IDs."""
        return ["CCM-010", "CCM-011"]

    def collect(self, control: Control) -> CheckResult:
        """Collect evidence for endpoint control."""
        if control.id == "CCM-010":
            return self._check_disk_encryption()
        elif control.id == "CCM-011":
            return self._check_screen_lock()
        else:
            return CheckResult(
                control_id=control.id,
                status="error",
                details=f"Control {control.id} not supported by Endpoint collector",
            )

    def _check_disk_encryption(self) -> CheckResult:
        """Check endpoint disk encryption."""
        if self.use_fixtures:
            data = self._load_fixture("endpoints.json")
        else:
            data = self._fetch_live_endpoints()

        endpoints = data["endpoints"]
        unencrypted = [e for e in endpoints if not e.get("disk_encrypted", False)]

        status = "pass" if not unencrypted else "fail"
        details = (
            f"Found {len(endpoints)} endpoints, "
            f"{len(unencrypted)} without disk encryption"
        )

        return CheckResult(
            control_id="CCM-010",
            status=status,
            details=details,
            evidence={
                "endpoints": endpoints,
                "unencrypted_endpoints": unencrypted,
            },
        )

    def _check_screen_lock(self) -> CheckResult:
        """Check endpoint screen lock configuration."""
        if self.use_fixtures:
            data = self._load_fixture("endpoints.json")
        else:
            data = self._fetch_live_endpoints()

        endpoints = data["endpoints"]
        non_compliant = []

        for endpoint in endpoints:
            screen_lock_timeout = endpoint.get("screen_lock_timeout_minutes")
            if screen_lock_timeout is None or screen_lock_timeout > 15:
                non_compliant.append(endpoint)

        status = "pass" if not non_compliant else "fail"
        details = (
            f"Found {len(endpoints)} endpoints, "
            f"{len(non_compliant)} with screen lock timeout > 15 minutes"
        )

        return CheckResult(
            control_id="CCM-011",
            status=status,
            details=details,
            evidence={
                "endpoints": endpoints,
                "non_compliant_endpoints": non_compliant,
            },
        )

    def _load_fixture(self, filename: str) -> dict:
        """Load fixture data."""
        fixture_path = Path(__file__).parent.parent.parent.parent / "fixtures" / filename
        with open(fixture_path, "r") as f:
            return json.load(f)

    def _fetch_live_endpoints(self) -> dict:
        """Fetch live endpoint data (placeholder)."""
        raise NotImplementedError("Live endpoint API not implemented in this demo")
