"""Okta/IdP collectors for identity and access management controls."""

import json
from datetime import datetime, timedelta
from pathlib import Path

from dateutil import parser

from ccm.collectors.base import Collector
from ccm.models import CheckStatus, Evidence


class AdminMFACollector(Collector):
    """Check that admin users have MFA enabled."""

    @property
    def control_id(self) -> str:
        return "CCM-AC-001"

    @property
    def name(self) -> str:
        return "okta_admin_mfa"

    def collect(self) -> Evidence:
        try:
            fixture_path = Path(self.config.get("fixture_path", "fixtures/okta/users.json"))
            with open(fixture_path) as f:
                data = json.load(f)

            admin_roles = ["SUPER_ADMIN", "ORG_ADMIN", "APP_ADMIN", "USER_ADMIN"]
            admin_users = []
            admins_without_mfa = []

            for user in data["users"]:
                user_roles = user.get("roles", [])
                is_admin = any(role in admin_roles for role in user_roles)

                if is_admin:
                    admin_users.append(user["profile"]["email"])
                    if not user.get("factors"):
                        admins_without_mfa.append(
                            {"email": user["profile"]["email"], "roles": user_roles}
                        )

            if admins_without_mfa:
                return self._create_evidence(
                    status=CheckStatus.FAIL,
                    message=f"{len(admins_without_mfa)} admin user(s) without MFA",
                    details={
                        "admin_users": admin_users,
                        "admins_without_mfa": admins_without_mfa,
                        "total_admins": len(admin_users),
                    },
                )

            return self._create_evidence(
                status=CheckStatus.PASS,
                message=f"All {len(admin_users)} admin user(s) have MFA enabled",
                details={
                    "admin_users": admin_users,
                    "total_admins": len(admin_users),
                },
            )

        except Exception as e:
            return self._create_evidence(
                status=CheckStatus.ERROR,
                message="Failed to check admin MFA status",
                error=str(e),
            )


class DormantUsersCollector(Collector):
    """Check for user accounts inactive for 90+ days."""

    @property
    def control_id(self) -> str:
        return "CCM-AC-002"

    @property
    def name(self) -> str:
        return "okta_dormant_users"

    def collect(self) -> Evidence:
        try:
            fixture_path = Path(self.config.get("fixture_path", "fixtures/okta/users.json"))
            with open(fixture_path) as f:
                data = json.load(f)

            dormancy_threshold = datetime.now(parser.parse("2020-01-01T00:00:00Z").tzinfo) - timedelta(days=90)
            dormant_users = []
            active_users = []

            for user in data["users"]:
                if user["status"] != "ACTIVE":
                    continue

                last_login_str = user.get("lastLogin")
                if not last_login_str:
                    created_date = parser.parse(user["created"])
                    now_aware = datetime.now(created_date.tzinfo)
                    days_dormant = (now_aware - created_date).days
                    if days_dormant > 90:
                        dormant_users.append(
                            {
                                "email": user["profile"]["email"],
                                "last_login": "never",
                                "days_since_created": days_dormant,
                            }
                        )
                    continue

                last_login = parser.parse(last_login_str)
                if last_login < dormancy_threshold:
                    now_aware = datetime.now(last_login.tzinfo)
                    days_dormant = (now_aware - last_login).days
                    dormant_users.append(
                        {
                            "email": user["profile"]["email"],
                            "last_login": last_login_str,
                            "days_dormant": days_dormant,
                        }
                    )
                else:
                    active_users.append(user["profile"]["email"])

            if dormant_users:
                return self._create_evidence(
                    status=CheckStatus.FAIL,
                    message=f"{len(dormant_users)} user(s) inactive for 90+ days",
                    details={
                        "dormant_users": dormant_users,
                        "active_users": active_users,
                        "total_active_status": len(dormant_users) + len(active_users),
                    },
                )

            return self._create_evidence(
                status=CheckStatus.PASS,
                message=f"All {len(active_users)} active user(s) logged in within 90 days",
                details={
                    "active_users": active_users,
                    "total_active_status": len(active_users),
                },
            )

        except Exception as e:
            return self._create_evidence(
                status=CheckStatus.ERROR,
                message="Failed to check dormant users",
                error=str(e),
            )


class UnusedAdminRolesCollector(Collector):
    """Check for admin roles assigned to users who haven't used them recently."""

    @property
    def control_id(self) -> str:
        return "CCM-AC-003"

    @property
    def name(self) -> str:
        return "okta_unused_admin_roles"

    def collect(self) -> Evidence:
        try:
            fixture_path = Path(self.config.get("fixture_path", "fixtures/okta/users.json"))
            with open(fixture_path) as f:
                data = json.load(f)

            usage_threshold = datetime.now(parser.parse("2020-01-01T00:00:00Z").tzinfo) - timedelta(days=30)
            admin_roles = ["SUPER_ADMIN", "ORG_ADMIN", "APP_ADMIN", "USER_ADMIN"]
            unused_role_assignments = []
            active_admins = []

            for user in data["users"]:
                user_roles = user.get("roles", [])
                has_admin_role = any(role in admin_roles for role in user_roles)

                if not has_admin_role:
                    continue

                last_login_str = user.get("lastLogin")
                if not last_login_str:
                    unused_role_assignments.append(
                        {
                            "email": user["profile"]["email"],
                            "roles": user_roles,
                            "last_login": "never",
                        }
                    )
                    continue

                last_login = parser.parse(last_login_str)
                if last_login < usage_threshold:
                    now_aware = datetime.now(last_login.tzinfo)
                    unused_role_assignments.append(
                        {
                            "email": user["profile"]["email"],
                            "roles": user_roles,
                            "last_login": last_login_str,
                            "days_since_login": (now_aware - last_login).days,
                        }
                    )
                else:
                    active_admins.append(user["profile"]["email"])

            if unused_role_assignments:
                return self._create_evidence(
                    status=CheckStatus.FAIL,
                    message=f"{len(unused_role_assignments)} admin role(s) unused for 30+ days",
                    details={
                        "unused_role_assignments": unused_role_assignments,
                        "active_admins": active_admins,
                        "total_admin_assignments": len(unused_role_assignments)
                        + len(active_admins),
                    },
                )

            return self._create_evidence(
                status=CheckStatus.PASS,
                message=f"All {len(active_admins)} admin role(s) used within 30 days",
                details={
                    "active_admins": active_admins,
                    "total_admin_assignments": len(active_admins),
                },
            )

        except Exception as e:
            return self._create_evidence(
                status=CheckStatus.ERROR,
                message="Failed to check unused admin roles",
                error=str(e),
            )
