"""GitHub control collectors."""

import json
from pathlib import Path

from ccm.collectors.base import Collector
from ccm.models import CheckResult, Control


class GitHubCollector(Collector):
    """Collector for GitHub controls."""

    def get_supported_controls(self) -> list[str]:
        """Get supported control IDs."""
        return ["CCM-008", "CCM-009"]

    def collect(self, control: Control) -> CheckResult:
        """Collect evidence for GitHub control."""
        if control.id == "CCM-008":
            return self._check_branch_protection()
        elif control.id == "CCM-009":
            return self._check_org_2fa()
        else:
            return CheckResult(
                control_id=control.id,
                status="error",
                details=f"Control {control.id} not supported by GitHub collector",
            )

    def _check_branch_protection(self) -> CheckResult:
        """Check branch protection rules."""
        if self.use_fixtures:
            data = self._load_fixture("github_repos.json")
        else:
            data = self._fetch_live_github_repos()

        repos = data["repositories"]
        unprotected_repos = []

        for repo in repos:
            default_branch = repo.get("default_branch", {})
            if not default_branch.get("protection_enabled", False):
                unprotected_repos.append(repo)

        status = "pass" if not unprotected_repos else "fail"
        details = (
            f"Found {len(repos)} repositories, "
            f"{len(unprotected_repos)} without branch protection"
        )

        return CheckResult(
            control_id="CCM-008",
            status=status,
            details=details,
            evidence={
                "repositories": repos,
                "unprotected_repos": unprotected_repos,
            },
        )

    def _check_org_2fa(self) -> CheckResult:
        """Check organization 2FA requirement."""
        if self.use_fixtures:
            data = self._load_fixture("github_org.json")
        else:
            data = self._fetch_live_github_org()

        org = data["organization"]
        requires_2fa = org.get("two_factor_requirement_enabled", False)

        status = "pass" if requires_2fa else "fail"
        details = f"Organization 2FA requirement: {'enabled' if requires_2fa else 'disabled'}"

        return CheckResult(
            control_id="CCM-009",
            status=status,
            details=details,
            evidence={"organization": org},
        )

    def _load_fixture(self, filename: str) -> dict:
        """Load fixture data."""
        fixture_path = Path(__file__).parent.parent.parent.parent / "fixtures" / filename
        with open(fixture_path, "r") as f:
            return json.load(f)

    def _fetch_live_github_repos(self) -> dict:
        """Fetch live GitHub repo data (placeholder)."""
        raise NotImplementedError("Live GitHub API not implemented in this demo")

    def _fetch_live_github_org(self) -> dict:
        """Fetch live GitHub org data (placeholder)."""
        raise NotImplementedError("Live GitHub API not implemented in this demo")
