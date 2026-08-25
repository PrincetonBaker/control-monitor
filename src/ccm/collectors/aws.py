"""AWS-shaped collectors for IAM, S3, and CloudTrail controls."""

import json
from datetime import datetime, timedelta
from pathlib import Path

from ccm.collectors.base import Collector
from ccm.models import CheckStatus, Evidence


class IAMMFACollector(Collector):
    """Check that privileged IAM users have MFA enabled."""

    @property
    def control_id(self) -> str:
        return "CCM-AC-001"

    @property
    def name(self) -> str:
        return "aws_iam_mfa"

    def collect(self) -> Evidence:
        try:
            fixture_path = Path(self.config.get("fixture_path", "fixtures/aws/iam_users.json"))
            with open(fixture_path) as f:
                data = json.load(f)

            admin_policies = ["AdministratorAccess", "PowerUserAccess"]
            privileged_users = []
            users_without_mfa = []

            for user in data["users"]:
                is_privileged = any(
                    policy in admin_policies
                    for policy_arn in user.get("attached_policies", [])
                    for policy in [policy_arn.split("/")[-1]]
                )

                if is_privileged:
                    privileged_users.append(user["user_name"])
                    if not user.get("mfa_devices"):
                        users_without_mfa.append(user["user_name"])

            if users_without_mfa:
                return self._create_evidence(
                    status=CheckStatus.FAIL,
                    message=f"{len(users_without_mfa)} privileged user(s) without MFA",
                    details={
                        "privileged_users": privileged_users,
                        "users_without_mfa": users_without_mfa,
                        "total_privileged": len(privileged_users),
                        "compliant_count": len(privileged_users) - len(users_without_mfa),
                    },
                )

            return self._create_evidence(
                status=CheckStatus.PASS,
                message=f"All {len(privileged_users)} privileged user(s) have MFA enabled",
                details={
                    "privileged_users": privileged_users,
                    "total_privileged": len(privileged_users),
                },
            )

        except Exception as e:
            return self._create_evidence(
                status=CheckStatus.ERROR,
                message="Failed to check IAM MFA status",
                error=str(e),
            )


class S3EncryptionCollector(Collector):
    """Check that S3 buckets have default encryption enabled."""

    @property
    def control_id(self) -> str:
        return "CCM-DS-001"

    @property
    def name(self) -> str:
        return "aws_s3_encryption"

    def collect(self) -> Evidence:
        try:
            fixture_path = Path(self.config.get("fixture_path", "fixtures/aws/s3_buckets.json"))
            with open(fixture_path) as f:
                data = json.load(f)

            unencrypted_buckets = []
            encrypted_buckets = []

            for bucket in data["buckets"]:
                if bucket.get("encryption"):
                    encrypted_buckets.append(
                        {
                            "name": bucket["name"],
                            "algorithm": bucket["encryption"]["rules"][0][
                                "apply_server_side_encryption_by_default"
                            ]["sse_algorithm"],
                        }
                    )
                else:
                    unencrypted_buckets.append(bucket["name"])

            if unencrypted_buckets:
                return self._create_evidence(
                    status=CheckStatus.FAIL,
                    message=f"{len(unencrypted_buckets)} bucket(s) without default encryption",
                    details={
                        "unencrypted_buckets": unencrypted_buckets,
                        "encrypted_buckets": [b["name"] for b in encrypted_buckets],
                        "total_buckets": len(data["buckets"]),
                    },
                )

            return self._create_evidence(
                status=CheckStatus.PASS,
                message=f"All {len(encrypted_buckets)} bucket(s) have default encryption enabled",
                details={
                    "encrypted_buckets": encrypted_buckets,
                    "total_buckets": len(data["buckets"]),
                },
            )

        except Exception as e:
            return self._create_evidence(
                status=CheckStatus.ERROR,
                message="Failed to check S3 encryption status",
                error=str(e),
            )


class S3PublicAccessCollector(Collector):
    """Check that S3 buckets block public access."""

    @property
    def control_id(self) -> str:
        return "CCM-DS-002"

    @property
    def name(self) -> str:
        return "aws_s3_public_access"

    def collect(self) -> Evidence:
        try:
            fixture_path = Path(self.config.get("fixture_path", "fixtures/aws/s3_buckets.json"))
            with open(fixture_path) as f:
                data = json.load(f)

            public_buckets = []
            protected_buckets = []

            for bucket in data["buckets"]:
                pab = bucket.get("public_access_block", {})
                is_public = (
                    bucket.get("acl") == "public-read"
                    or not pab.get("block_public_acls", False)
                    or not pab.get("block_public_policy", False)
                    or not pab.get("restrict_public_buckets", False)
                )

                if is_public:
                    public_buckets.append(
                        {"name": bucket["name"], "acl": bucket.get("acl", "unknown")}
                    )
                else:
                    protected_buckets.append(bucket["name"])

            if public_buckets:
                return self._create_evidence(
                    status=CheckStatus.FAIL,
                    message=f"{len(public_buckets)} bucket(s) have public access enabled",
                    details={
                        "public_buckets": public_buckets,
                        "protected_buckets": protected_buckets,
                        "total_buckets": len(data["buckets"]),
                    },
                )

            return self._create_evidence(
                status=CheckStatus.PASS,
                message=f"All {len(protected_buckets)} bucket(s) block public access",
                details={
                    "protected_buckets": protected_buckets,
                    "total_buckets": len(data["buckets"]),
                },
            )

        except Exception as e:
            return self._create_evidence(
                status=CheckStatus.ERROR,
                message="Failed to check S3 public access status",
                error=str(e),
            )


class CloudTrailCollector(Collector):
    """Check that CloudTrail is enabled and logging."""

    @property
    def control_id(self) -> str:
        return "CCM-LOG-001"

    @property
    def name(self) -> str:
        return "aws_cloudtrail"

    def collect(self) -> Evidence:
        try:
            fixture_path = Path(self.config.get("fixture_path", "fixtures/aws/cloudtrail.json"))
            with open(fixture_path) as f:
                data = json.load(f)

            trails = data.get("trails", [])

            if not trails:
                return self._create_evidence(
                    status=CheckStatus.FAIL,
                    message="No CloudTrail trails configured",
                    details={"trail_count": 0},
                )

            active_trails = []
            inactive_trails = []

            for trail in trails:
                if trail.get("is_logging") and trail.get("is_multi_region_trail"):
                    active_trails.append(
                        {
                            "name": trail["name"],
                            "multi_region": trail["is_multi_region_trail"],
                            "log_validation": trail.get("log_file_validation_enabled", False),
                        }
                    )
                else:
                    inactive_trails.append(trail["name"])

            if not active_trails:
                return self._create_evidence(
                    status=CheckStatus.FAIL,
                    message="No active multi-region CloudTrail trails",
                    details={
                        "trail_count": len(trails),
                        "inactive_trails": inactive_trails,
                    },
                )

            return self._create_evidence(
                status=CheckStatus.PASS,
                message=f"{len(active_trails)} active multi-region CloudTrail trail(s) configured",
                details={
                    "active_trails": active_trails,
                    "trail_count": len(trails),
                },
            )

        except Exception as e:
            return self._create_evidence(
                status=CheckStatus.ERROR,
                message="Failed to check CloudTrail status",
                error=str(e),
            )
