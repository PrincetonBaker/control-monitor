"""Endpoint security collectors for device compliance controls."""

import json
from pathlib import Path

from ccm.collectors.base import Collector
from ccm.models import CheckStatus, Evidence


class DiskEncryptionCollector(Collector):
    """Check that endpoints have full disk encryption enabled."""

    @property
    def control_id(self) -> str:
        return "CCM-DS-003"

    @property
    def name(self) -> str:
        return "endpoint_disk_encryption"

    def collect(self) -> Evidence:
        try:
            fixture_path = Path(self.config.get("fixture_path", "fixtures/endpoint/devices.json"))
            with open(fixture_path) as f:
                data = json.load(f)

            devices = data.get("devices", [])
            unencrypted_devices = []
            encrypted_devices = []

            for device in devices:
                encryption = device.get("disk_encryption", {})

                if encryption.get("enabled") and encryption.get("status") == "verified":
                    encrypted_devices.append(
                        {
                            "hostname": device["hostname"],
                            "user": device["user"],
                            "method": encryption.get("method"),
                        }
                    )
                else:
                    unencrypted_devices.append(
                        {
                            "hostname": device["hostname"],
                            "user": device["user"],
                            "status": encryption.get("status", "not_configured"),
                        }
                    )

            if unencrypted_devices:
                return self._create_evidence(
                    status=CheckStatus.FAIL,
                    message=f"{len(unencrypted_devices)} device(s) without disk encryption",
                    details={
                        "unencrypted_devices": unencrypted_devices,
                        "encrypted_devices": [d["hostname"] for d in encrypted_devices],
                        "total_devices": len(devices),
                    },
                )

            return self._create_evidence(
                status=CheckStatus.PASS,
                message=f"All {len(encrypted_devices)} device(s) have disk encryption enabled",
                details={
                    "encrypted_devices": encrypted_devices,
                    "total_devices": len(devices),
                },
            )

        except Exception as e:
            return self._create_evidence(
                status=CheckStatus.ERROR,
                message="Failed to check disk encryption status",
                error=str(e),
            )


class ScreenLockCollector(Collector):
    """Check that endpoints have automatic screen lock configured."""

    @property
    def control_id(self) -> str:
        return "CCM-EP-001"

    @property
    def name(self) -> str:
        return "endpoint_screen_lock"

    def collect(self) -> Evidence:
        try:
            fixture_path = Path(self.config.get("fixture_path", "fixtures/endpoint/devices.json"))
            with open(fixture_path) as f:
                data = json.load(f)

            devices = data.get("devices", [])
            max_timeout = 15
            non_compliant_devices = []
            compliant_devices = []

            for device in devices:
                screen_lock = device.get("screen_lock", {})

                if not screen_lock.get("enabled"):
                    non_compliant_devices.append(
                        {
                            "hostname": device["hostname"],
                            "user": device["user"],
                            "issue": "screen_lock_disabled",
                        }
                    )
                elif screen_lock.get("timeout_minutes", 999) > max_timeout:
                    non_compliant_devices.append(
                        {
                            "hostname": device["hostname"],
                            "user": device["user"],
                            "issue": "timeout_exceeds_15min",
                            "timeout_minutes": screen_lock.get("timeout_minutes"),
                        }
                    )
                else:
                    compliant_devices.append(
                        {
                            "hostname": device["hostname"],
                            "user": device["user"],
                            "timeout_minutes": screen_lock.get("timeout_minutes"),
                        }
                    )

            if non_compliant_devices:
                return self._create_evidence(
                    status=CheckStatus.FAIL,
                    message=f"{len(non_compliant_devices)} device(s) with non-compliant screen lock",
                    details={
                        "non_compliant_devices": non_compliant_devices,
                        "compliant_devices": [d["hostname"] for d in compliant_devices],
                        "total_devices": len(devices),
                        "max_timeout_minutes": max_timeout,
                    },
                )

            return self._create_evidence(
                status=CheckStatus.PASS,
                message=f"All {len(compliant_devices)} device(s) have compliant screen lock",
                details={
                    "compliant_devices": compliant_devices,
                    "total_devices": len(devices),
                    "max_timeout_minutes": max_timeout,
                },
            )

        except Exception as e:
            return self._create_evidence(
                status=CheckStatus.ERROR,
                message="Failed to check screen lock configuration",
                error=str(e),
            )
