"""Control evidence collectors."""

from ccm.collectors.base import Collector
from ccm.collectors.aws import AWSCollector
from ccm.collectors.okta import OktaCollector
from ccm.collectors.github import GitHubCollector
from ccm.collectors.endpoint import EndpointCollector

__all__ = [
    "Collector",
    "AWSCollector",
    "OktaCollector",
    "GitHubCollector",
    "EndpointCollector",
]
