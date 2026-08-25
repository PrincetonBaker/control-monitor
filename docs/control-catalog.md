# Control Catalog

## Overview

The CCM control catalog defines a curated set of security and compliance controls that map to multiple compliance frameworks. Each control represents a specific requirement that can be automated, measured, and tracked over time.

## Structure

Each control in the catalog includes:

- **Control ID**: Unique identifier following the pattern `CCM-{CATEGORY}-{NUMBER}`
- **Title**: Human-readable control name
- **Description**: What the control requires
- **Category**: Logical grouping (Access Control, Data Security, Logging & Monitoring, etc.)
- **Severity**: Impact rating (critical, high, medium, low, info)
- **Intent**: Why this control exists
- **Test Procedure**: How compliance is verified
- **Evidence Expected**: What artifacts auditors need
- **Framework Mappings**: Links to SOC 2, ISO 27001, PCI-DSS, HIPAA requirements

## Control Categories

### Access Control (AC)
Controls related to user authentication, authorization, and privilege management.

- **CCM-AC-001**: Multi-Factor Authentication for Privileged Users
- **CCM-AC-002**: Dormant User Account Review
- **CCM-AC-003**: Privileged Role Assignment Review

### Data Security (DS)
Controls protecting data at rest and in transit.

- **CCM-DS-001**: S3 Bucket Default Encryption
- **CCM-DS-002**: S3 Bucket Public Access Blocked
- **CCM-DS-003**: Endpoint Disk Encryption

### Logging & Monitoring (LOG)
Controls for audit trails and security monitoring.

- **CCM-LOG-001**: CloudTrail Logging Enabled

### Change Management (CM)
Controls for source code and infrastructure changes.

- **CCM-CM-001**: GitHub Branch Protection
- **CCM-CM-002**: GitHub Organization 2FA Enforcement

### Endpoint Security (EP)
Controls for end-user devices.

- **CCM-EP-001**: Endpoint Screen Lock Configuration

## Framework Mappings

### SOC 2 Trust Services Criteria

The catalog maps to the following TSC categories:

- **CC6** (Logical and Physical Access Controls): Controls who can access systems
- **CC7** (System Operations): Monitoring and incident response
- **CC8** (Change Management): Authorization and testing of changes

### ISO 27001:2022 Annex A

Selected controls map to:

- **A.5** (Organizational controls): Access control policies
- **A.8** (Technological controls): Encryption, logging, change management

### PCI-DSS v4

Relevant requirements include:

- **3.x** (Protect stored cardholder data): Encryption controls
- **8.x** (Identify and authenticate access): MFA and authentication
- **10.x** (Log and monitor all access): Audit logging

### HIPAA Security Rule

Technical safeguards covered:

- **164.312(a)** (Access control): Authentication and authorization
- **164.312(b)** (Audit controls): Logging and monitoring
- **164.312(e)** (Transmission security): Encryption

## Usage in Audits

### For Internal Use

1. Run `ccm scan` regularly to collect evidence
2. Store evidence artifacts in version control or compliance platforms
3. Review failures and create exceptions when compensating controls exist
4. Track trends over time to show continuous compliance

### For External Auditors

Evidence files provide:

- **Timestamped snapshots**: When the control was tested
- **Detailed findings**: Specific resources that passed or failed
- **Traceability**: Which collector verified which control
- **Exception tracking**: Approved deviations with expiry dates

Share evidence via:
- Export to JSON: `ccm export-evidence`
- HTML reports: `ccm scan --output html`
- Direct file sharing from `evidence/` directory

## Adding New Controls

To extend the catalog:

1. Add control definition to `controls.yaml`
2. Implement a collector in `src/ccm/collectors/`
3. Register the collector in `src/ccm/collectors/__init__.py`
4. Add fixture data in `fixtures/` for testing
5. Write tests in `tests/unit/`
6. Update this documentation

## Design Decisions

### Why YAML over OPA/Rego?

- **Readability**: Security teams, not just engineers, need to understand controls
- **Simplicity**: No need for policy-as-code complexity for this use case
- **Portability**: YAML imports easily into Vanta, Drata, and other GRC tools

### Why Fixture Data?

- **No credentials required**: Demo works immediately after clone
- **Reproducible tests**: Same fixture data = same test results
- **Safe for CI**: No secrets, no API rate limits
- **Educational**: Shows what real data looks like

### Why Multiple Frameworks?

Real compliance programs rarely focus on one framework. Mapping controls across frameworks:

- Reduces audit burden (one control → multiple requirements)
- Shows overlap between standards
- Demonstrates mature GRC thinking
