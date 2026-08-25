"""AWS control collectors."""

import json
from datetime import datetime
from pathlib import Path

from ccm.collectors.base import Collector
from ccm.models import CheckResult, Control


class AWSCollector(Collector):
    """Collector for AWS controls."""

    def get_supported_controls(self) -> list[str]:
        """Get supported control IDs."""
        return ["CCM-001", "CCM-002", "CCM-003", "CCM-004"]

    def collect(self, control: Control) -> CheckResult:
        """Collect evidence for AWS control."""
        if control.id == "CCM-001":
            return self._check_iam_mfa()
        elif control.id == "CCM-002":
            return self._check_s3_encryption()
        elif control.id == "CCM-003":
            return self._check_s3_public()
        elif control.id == "CCM-004":
            return self._check_cloudtrail()
        else:
            return CheckResult(
                control_id=control.id,
                status="error",
                details=f"Control {control.id} not supported by AWS collector",
            )

    def _check_iam_mfa(self) -> CheckResult:
        """Check IAM MFA on privileged users."""
        if self.use_fixtures:
            data = self._load_fixture("aws_iam_users.json")
        else:
            data = self._fetch_live_iam_users()

        admin_users = [u for u in data["users"] if u.get("is_admin", False)]
        users_without_mfa = [u for u in admin_users if not u.get("mfa_enabled", False)]

        status = "pass" if not users_without_mfa else "fail"
        details = (
            f"Found {len(admin_users)} admin users, "
            f"{len(users_without_mfa)} without MFA"
        )

        return CheckResult(
            control_id="CCM-001",
            status=status,
            details=details,
            evidence={
                "admin_users": admin_users,
                "users_without_mfa": users_without_mfa,
            },
        )

    def _check_s3_encryption(self) -> CheckResult:
        """Check S3 bucket encryption."""
        if self.use_fixtures:
            data = self._load_fixture("aws_s3_buckets.json")
        else:
            data = self._fetch_live_s3_buckets()

        buckets = data["buckets"]
        unencrypted = [b for b in buckets if not b.get("encryption_enabled", False)]

        status = "pass" if not unencrypted else "fail"
        details = (
            f"Found {len(buckets)} buckets, "
            f"{len(unencrypted)} without encryption"
        )

        return CheckResult(
            control_id="CCM-002",
            status=status,
            details=details,
            evidence={
                "buckets": buckets,
                "unencrypted_buckets": unencrypted,
            },
        )

    def _check_s3_public(self) -> CheckResult:
        """Check for public S3 buckets."""
        if self.use_fixtures:
            data = self._load_fixture("aws_s3_buckets.json")
        else:
            data = self._fetch_live_s3_buckets()

        buckets = data["buckets"]
        public_buckets = [b for b in buckets if b.get("public_access", False)]

        status = "pass" if not public_buckets else "fail"
        details = f"Found {len(buckets)} buckets, {len(public_buckets)} are public"

        return CheckResult(
            control_id="CCM-003",
            status=status,
            details=details,
            evidence={
                "buckets": buckets,
                "public_buckets": public_buckets,
            },
        )

    def _check_cloudtrail(self) -> CheckResult:
        """Check CloudTrail logging."""
        if self.use_fixtures:
            data = self._load_fixture("aws_cloudtrail.json")
        else:
            data = self._fetch_live_cloudtrail()

        trails = data["trails"]
        enabled_trails = [t for t in trails if t.get("is_logging", False)]

        status = "pass" if enabled_trails else "fail"
        details = f"Found {len(trails)} trails, {len(enabled_trails)} are logging"

        return CheckResult(
            control_id="CCM-004",
            status=status,
            details=details,
            evidence={
                "trails": trails,
                "enabled_trails": enabled_trails,
            },
        )

    def _load_fixture(self, filename: str) -> dict:
        """Load fixture data."""
        fixture_path = Path(__file__).parent.parent.parent.parent / "fixtures" / filename
        with open(fixture_path, "r") as f:
            return json.load(f)

    def _fetch_live_iam_users(self) -> dict:
        """Fetch live IAM user data (placeholder)."""
        raise NotImplementedError("Live AWS API not implemented in this demo")

    def _fetch_live_s3_buckets(self) -> dict:
        """Fetch live S3 bucket data (placeholder)."""
        raise NotImplementedError("Live AWS API not implemented in this demo")

    def _fetch_live_cloudtrail(self) -> dict:
        """Fetch live CloudTrail data (placeholder)."""
        raise NotImplementedError("Live AWS API not implemented in this demo")
