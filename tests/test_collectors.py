"""Tests for collectors."""

import pytest

from ccm.catalog import load_catalog
from ccm.collectors import AWSCollector, EndpointCollector, GitHubCollector, OktaCollector


def test_aws_collector_mfa_pass():
    """Test AWS MFA collector with passing data."""
    catalog = load_catalog()
    control = next(c for c in catalog.controls if c.id == "CCM-001")
    
    collector = AWSCollector(use_fixtures=True)
    result = collector.collect(control)
    
    assert result.control_id == "CCM-001"
    assert result.status == "fail"
    assert "admin_users" in result.evidence
    assert "users_without_mfa" in result.evidence


def test_aws_collector_s3_encryption():
    """Test AWS S3 encryption collector."""
    catalog = load_catalog()
    control = next(c for c in catalog.controls if c.id == "CCM-002")
    
    collector = AWSCollector(use_fixtures=True)
    result = collector.collect(control)
    
    assert result.control_id == "CCM-002"
    assert result.status in ("pass", "fail")
    assert "buckets" in result.evidence


def test_aws_collector_s3_public():
    """Test AWS S3 public access collector."""
    catalog = load_catalog()
    control = next(c for c in catalog.controls if c.id == "CCM-003")
    
    collector = AWSCollector(use_fixtures=True)
    result = collector.collect(control)
    
    assert result.control_id == "CCM-003"
    assert result.status in ("pass", "fail")
    assert "public_buckets" in result.evidence


def test_aws_collector_cloudtrail():
    """Test AWS CloudTrail collector."""
    catalog = load_catalog()
    control = next(c for c in catalog.controls if c.id == "CCM-004")
    
    collector = AWSCollector(use_fixtures=True)
    result = collector.collect(control)
    
    assert result.control_id == "CCM-004"
    assert result.status in ("pass", "fail")
    assert "trails" in result.evidence


def test_okta_collector_admin_mfa():
    """Test Okta admin MFA collector."""
    catalog = load_catalog()
    control = next(c for c in catalog.controls if c.id == "CCM-005")
    
    collector = OktaCollector(use_fixtures=True)
    result = collector.collect(control)
    
    assert result.control_id == "CCM-005"
    assert result.status in ("pass", "fail")
    assert "admins" in result.evidence


def test_okta_collector_dormant_users():
    """Test Okta dormant users collector."""
    catalog = load_catalog()
    control = next(c for c in catalog.controls if c.id == "CCM-006")
    
    collector = OktaCollector(use_fixtures=True)
    result = collector.collect(control)
    
    assert result.control_id == "CCM-006"
    assert result.status in ("pass", "fail")
    assert "dormant_users" in result.evidence


def test_okta_collector_unused_roles():
    """Test Okta unused admin roles collector."""
    catalog = load_catalog()
    control = next(c for c in catalog.controls if c.id == "CCM-007")
    
    collector = OktaCollector(use_fixtures=True)
    result = collector.collect(control)
    
    assert result.control_id == "CCM-007"
    assert result.status in ("pass", "fail")
    assert "unused_assignments" in result.evidence


def test_github_collector_branch_protection():
    """Test GitHub branch protection collector."""
    catalog = load_catalog()
    control = next(c for c in catalog.controls if c.id == "CCM-008")
    
    collector = GitHubCollector(use_fixtures=True)
    result = collector.collect(control)
    
    assert result.control_id == "CCM-008"
    assert result.status in ("pass", "fail")
    assert "repositories" in result.evidence


def test_github_collector_org_2fa():
    """Test GitHub organization 2FA collector."""
    catalog = load_catalog()
    control = next(c for c in catalog.controls if c.id == "CCM-009")
    
    collector = GitHubCollector(use_fixtures=True)
    result = collector.collect(control)
    
    assert result.control_id == "CCM-009"
    assert result.status in ("pass", "fail")
    assert "organization" in result.evidence


def test_endpoint_collector_disk_encryption():
    """Test endpoint disk encryption collector."""
    catalog = load_catalog()
    control = next(c for c in catalog.controls if c.id == "CCM-010")
    
    collector = EndpointCollector(use_fixtures=True)
    result = collector.collect(control)
    
    assert result.control_id == "CCM-010"
    assert result.status in ("pass", "fail")
    assert "endpoints" in result.evidence


def test_endpoint_collector_screen_lock():
    """Test endpoint screen lock collector."""
    catalog = load_catalog()
    control = next(c for c in catalog.controls if c.id == "CCM-011")
    
    collector = EndpointCollector(use_fixtures=True)
    result = collector.collect(control)
    
    assert result.control_id == "CCM-011"
    assert result.status in ("pass", "fail")
    assert "endpoints" in result.evidence


def test_collector_supports_control():
    """Test collector support checking."""
    aws_collector = AWSCollector(use_fixtures=True)
    catalog = load_catalog()
    
    aws_control = next(c for c in catalog.controls if c.id == "CCM-001")
    okta_control = next(c for c in catalog.controls if c.id == "CCM-005")
    
    assert aws_collector.supports_control(aws_control)
    assert not aws_collector.supports_control(okta_control)


def test_collector_unsupported_control():
    """Test collector with unsupported control."""
    catalog = load_catalog()
    unsupported_control = next(c for c in catalog.controls if c.id == "CCM-012")
    
    collector = AWSCollector(use_fixtures=True)
    result = collector.collect(unsupported_control)
    
    assert result.status == "error"
    assert "not supported" in result.details.lower()
