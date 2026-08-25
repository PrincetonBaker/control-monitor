"""Collector implementations."""

from ccm.collectors.base import registry
from ccm.collectors.aws import (
    CloudTrailCollector,
    IAMMFACollector,
    S3EncryptionCollector,
    S3PublicAccessCollector,
)
from ccm.collectors.endpoint import DiskEncryptionCollector, ScreenLockCollector
from ccm.collectors.github import BranchProtectionCollector, Org2FACollector
from ccm.collectors.okta import (
    AdminMFACollector,
    DormantUsersCollector,
    UnusedAdminRolesCollector,
)

# Register all collectors
registry.register(IAMMFACollector)
registry.register(S3EncryptionCollector)
registry.register(S3PublicAccessCollector)
registry.register(CloudTrailCollector)
registry.register(AdminMFACollector)
registry.register(DormantUsersCollector)
registry.register(UnusedAdminRolesCollector)
registry.register(BranchProtectionCollector)
registry.register(Org2FACollector)
registry.register(DiskEncryptionCollector)
registry.register(ScreenLockCollector)

__all__ = ["registry"]
