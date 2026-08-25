"""GitHub collectors for source code and change management controls."""

import json
from pathlib import Path

from ccm.collectors.base import Collector
from ccm.models import CheckStatus, Evidence


class BranchProtectionCollector(Collector):
    """Check that production repositories have branch protection enabled."""

    @property
    def control_id(self) -> str:
        return "CCM-CM-001"

    @property
    def name(self) -> str:
        return "github_branch_protection"

    def collect(self) -> Evidence:
        try:
            fixture_path = Path(
                self.config.get("fixture_path", "fixtures/github/organization.json")
            )
            with open(fixture_path) as f:
                data = json.load(f)

            repositories = data.get("repositories", [])
            unprotected_repos = []
            protected_repos = []

            for repo in repositories:
                bp = repo.get("branch_protection")

                if bp and bp.get("enabled"):
                    protected_repos.append(
                        {
                            "name": repo["full_name"],
                            "branch": repo["default_branch"],
                            "required_reviewers": bp.get("required_approving_review_count", 0),
                        }
                    )
                else:
                    unprotected_repos.append(
                        {
                            "name": repo["full_name"],
                            "branch": repo["default_branch"],
                        }
                    )

            if unprotected_repos:
                return self._create_evidence(
                    status=CheckStatus.FAIL,
                    message=f"{len(unprotected_repos)} repository/ies without branch protection",
                    details={
                        "unprotected_repos": unprotected_repos,
                        "protected_repos": [r["name"] for r in protected_repos],
                        "total_repos": len(repositories),
                    },
                )

            return self._create_evidence(
                status=CheckStatus.PASS,
                message=f"All {len(protected_repos)} repository/ies have branch protection",
                details={
                    "protected_repos": protected_repos,
                    "total_repos": len(repositories),
                },
            )

        except Exception as e:
            return self._create_evidence(
                status=CheckStatus.ERROR,
                message="Failed to check branch protection status",
                error=str(e),
            )


class Org2FACollector(Collector):
    """Check that GitHub organization requires 2FA for all members."""

    @property
    def control_id(self) -> str:
        return "CCM-CM-002"

    @property
    def name(self) -> str:
        return "github_org_2fa"

    def collect(self) -> Evidence:
        try:
            fixture_path = Path(
                self.config.get("fixture_path", "fixtures/github/organization.json")
            )
            with open(fixture_path) as f:
                data = json.load(f)

            org = data.get("organization", {})
            org_name = org.get("login", "unknown")
            two_fa_enabled = org.get("two_factor_requirement_enabled", False)

            if not two_fa_enabled:
                return self._create_evidence(
                    status=CheckStatus.FAIL,
                    message=f"Organization '{org_name}' does not require 2FA",
                    details={
                        "organization": org_name,
                        "two_factor_required": False,
                    },
                )

            return self._create_evidence(
                status=CheckStatus.PASS,
                message=f"Organization '{org_name}' requires 2FA for all members",
                details={
                    "organization": org_name,
                    "two_factor_required": True,
                },
            )

        except Exception as e:
            return self._create_evidence(
                status=CheckStatus.ERROR,
                message="Failed to check organization 2FA requirement",
                error=str(e),
            )
