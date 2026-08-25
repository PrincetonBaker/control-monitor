"""Okta control collectors."""

import json
from datetime import datetime, timedelta
from pathlib import Path

from ccm.collectors.base import Collector
from ccm.models import CheckResult, Control


class OktaCollector(Collector):
    """Collector for Okta controls."""

    def get_supported_controls(self) -> list[str]:
        """Get supported control IDs."""
        return ["CCM-005", "CCM-006", "CCM-007"]

    def collect(self, control: Control) -> CheckResult:
        """Collect evidence for Okta control."""
        if control.id == "CCM-005":
            return self._check_admin_mfa()
        elif control.id == "CCM-006":
            return self._check_dormant_users()
        elif control.id == "CCM-007":
            return self._check_unused_admin_roles()
        else:
            return CheckResult(
                control_id=control.id,
                status="error",
                details=f"Control {control.id} not supported by Okta collector",
            )

    def _check_admin_mfa(self) -> CheckResult:
        """Check Okta admin MFA enforcement."""
        if self.use_fixtures:
            data = self._load_fixture("okta_admins.json")
        else:
            data = self._fetch_live_okta_admins()

        admins = data["admins"]
        admins_without_mfa = [a for a in admins if not a.get("mfa_enforced", False)]

        status = "pass" if not admins_without_mfa else "fail"
        details = (
            f"Found {len(admins)} admins, "
            f"{len(admins_without_mfa)} without MFA enforced"
        )

        return CheckResult(
            control_id="CCM-005",
            status=status,
            details=details,
            evidence={
                "admins": admins,
                "admins_without_mfa": admins_without_mfa,
            },
        )

    def _check_dormant_users(self) -> CheckResult:
        """Check for dormant user accounts."""
        if self.use_fixtures:
            data = self._load_fixture("okta_users.json")
        else:
            data = self._fetch_live_okta_users()

        users = data["users"]
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        dormant_users = []

        for user in users:
            last_login = user.get("last_login")
            if last_login:
                last_login_dt = datetime.fromisoformat(last_login.replace("Z", "+00:00"))
                if last_login_dt.replace(tzinfo=None) < cutoff_date:
                    dormant_users.append(user)
            else:
                dormant_users.append(user)

        status = "pass" if not dormant_users else "fail"
        details = f"Found {len(users)} users, {len(dormant_users)} are dormant (>90 days)"

        return CheckResult(
            control_id="CCM-006",
            status=status,
            details=details,
            evidence={
                "users": users,
                "dormant_users": dormant_users,
                "cutoff_date": cutoff_date.isoformat(),
            },
        )

    def _check_unused_admin_roles(self) -> CheckResult:
        """Check for unused admin roles."""
        if self.use_fixtures:
            data = self._load_fixture("okta_role_assignments.json")
        else:
            data = self._fetch_live_okta_roles()

        assignments = data["role_assignments"]
        cutoff_date = datetime.utcnow() - timedelta(days=60)
        unused_assignments = []

        for assignment in assignments:
            if not assignment.get("is_admin_role", False):
                continue
            last_used = assignment.get("last_used")
            if last_used:
                last_used_dt = datetime.fromisoformat(last_used.replace("Z", "+00:00"))
                if last_used_dt.replace(tzinfo=None) < cutoff_date:
                    unused_assignments.append(assignment)
            else:
                unused_assignments.append(assignment)

        status = "pass" if not unused_assignments else "fail"
        details = (
            f"Found {len([a for a in assignments if a.get('is_admin_role')])} admin "
            f"role assignments, {len(unused_assignments)} unused (>60 days)"
        )

        return CheckResult(
            control_id="CCM-007",
            status=status,
            details=details,
            evidence={
                "role_assignments": assignments,
                "unused_assignments": unused_assignments,
                "cutoff_date": cutoff_date.isoformat(),
            },
        )

    def _load_fixture(self, filename: str) -> dict:
        """Load fixture data."""
        fixture_path = Path(__file__).parent.parent.parent.parent / "fixtures" / filename
        with open(fixture_path, "r") as f:
            return json.load(f)

    def _fetch_live_okta_admins(self) -> dict:
        """Fetch live Okta admin data (placeholder)."""
        raise NotImplementedError("Live Okta API not implemented in this demo")

    def _fetch_live_okta_users(self) -> dict:
        """Fetch live Okta user data (placeholder)."""
        raise NotImplementedError("Live Okta API not implemented in this demo")

    def _fetch_live_okta_roles(self) -> dict:
        """Fetch live Okta role data (placeholder)."""
        raise NotImplementedError("Live Okta API not implemented in this demo")
