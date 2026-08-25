# Control Catalog Reference

This document provides detailed descriptions of all controls in the CCM catalog, including their intent, test procedures, and framework mappings.

## Control Categories

- **Access Control** - User authentication, authorization, and access management
- **Encryption** - Data protection at rest and in transit
- **Logging** - Audit trail and activity monitoring
- **Change Management** - Code and infrastructure change controls
- **Physical Security** - Endpoint and facility security
- **Incident Management** - Security incident response and testing
- **Vendor Management** - Third-party risk management

---

## CCM-001: MFA Required for Privileged Users

**Category:** Access Control  
**Severity:** Critical

### Intent
Ensure all users with privileged access use multi-factor authentication to prevent unauthorized access through compromised credentials.

### Test Procedure
1. Enumerate all IAM users with administrative permissions
2. Check MFA device enrollment for each admin user
3. Verify MFA is enforced via policy (not optional)

### Evidence Expected
- List of IAM users with admin privileges
- MFA device status for each user
- IAM policy requiring MFA for privileged actions

### Framework Mappings
- **SOC 2:** CC6.1 (Logical Access), CC6.2 (Authentication)
- **ISO 27001:** A.9.2.1 (User registration), A.9.4.2 (Secure authentication)
- **PCI-DSS:** 8.3.1 (MFA for all access), 8.3.2 (MFA implementation)
- **HIPAA:** 164.312(a)(2)(i) (Unique user identification)

### Pass Criteria
All users with administrative permissions have MFA enabled.

### Remediation
Enable MFA for all admin users and enforce via IAM policy requiring MFA for privileged actions.

---

## CCM-002: Data Encryption at Rest

**Category:** Encryption  
**Severity:** Critical

### Intent
Protect sensitive data stored in cloud storage through encryption to prevent unauthorized access in case of data breach or misconfiguration.

### Test Procedure
1. List all S3 buckets in production accounts
2. Check default encryption configuration for each bucket
3. Verify encryption key management (AWS KMS or AES-256)

### Evidence Expected
- Inventory of all S3 buckets
- Encryption status (enabled/disabled)
- Encryption type (AES-256, aws:kms)

### Framework Mappings
- **SOC 2:** CC6.7 (Data encryption)
- **ISO 27001:** A.10.1.1 (Cryptographic controls), A.8.24 (Cryptography)
- **PCI-DSS:** 3.4 (Encryption at rest), 3.5.1 (Encryption keys)
- **HIPAA:** 164.312(a)(2)(iv) (Encryption), 164.312(e)(2)(ii) (Encryption standard)

### Pass Criteria
All S3 buckets have default encryption enabled with AES-256 or AWS KMS.

### Remediation
Enable default encryption on all S3 buckets. Use AWS KMS for sensitive data requiring key rotation.

---

## CCM-003: No Public S3 Buckets

**Category:** Access Control  
**Severity:** High

### Intent
Prevent unauthorized access to sensitive data by ensuring S3 buckets are not publicly accessible via ACLs or bucket policies.

### Test Procedure
1. Scan all S3 buckets for public access configuration
2. Check bucket ACLs for public grants
3. Verify Block Public Access settings

### Evidence Expected
- List of S3 buckets
- Public access status for each bucket
- Block Public Access configuration

### Framework Mappings
- **SOC 2:** CC6.1 (Logical access), CC6.6 (Access control)
- **ISO 27001:** A.9.1.2 (Access to networks), A.13.1.3 (Network segregation)
- **PCI-DSS:** 1.2.1 (Network security controls), 1.3.1 (Inbound/outbound restrictions)
- **HIPAA:** 164.312(a)(1) (Access control)

### Pass Criteria
No S3 buckets allow public read or write access unless explicitly required and documented.

### Remediation
Enable Block Public Access on all accounts and buckets. Use pre-signed URLs for temporary public access needs.

---

## CCM-004: CloudTrail Logging Enabled

**Category:** Logging  
**Severity:** High

### Intent
Maintain audit trails of all API activity for security monitoring, incident response, and compliance requirements.

### Test Procedure
1. Verify CloudTrail is enabled in all regions
2. Check trail is logging to a secure S3 bucket
3. Verify log file validation is enabled

### Evidence Expected
- CloudTrail configuration
- S3 bucket destination
- Multi-region trail status
- Log file validation status

### Framework Mappings
- **SOC 2:** CC7.2 (Monitoring), CC7.3 (Anomaly detection)
- **ISO 27001:** A.12.4.1 (Event logging), A.12.4.3 (Administrator logs)
- **PCI-DSS:** 10.2.2 (Automated audit trails), 10.3.1 (Audit trail entries)
- **HIPAA:** 164.312(b) (Audit controls)

### Pass Criteria
CloudTrail enabled with multi-region trail logging to protected S3 bucket with log file validation.

### Remediation
Enable CloudTrail organization trail covering all accounts and regions. Implement S3 bucket lifecycle policies for log retention.

---

## CCM-005: Okta Admin MFA Enforcement

**Category:** Access Control  
**Severity:** Critical

### Intent
Require MFA for all administrative accounts in the identity provider to protect against credential compromise.

### Test Procedure
1. List all users with Okta admin roles
2. Check MFA policy enforcement for admin users
3. Verify no admin accounts have MFA exemptions

### Evidence Expected
- List of Okta admins with role assignments
- MFA enforcement status per admin
- MFA policy configuration

### Framework Mappings
- **SOC 2:** CC6.1 (Logical access), CC6.2 (Authentication)
- **ISO 27001:** A.9.2.1 (User registration), A.9.4.2 (Secure authentication), A.9.4.3 (Password management)
- **PCI-DSS:** 8.3.1 (MFA for all access), 8.3.2 (MFA implementation)
- **HIPAA:** 164.312(a)(2)(i) (Unique user identification)

### Pass Criteria
All Okta admin accounts have MFA enforced via policy with no exemptions.

### Remediation
Configure Okta sign-on policy requiring MFA for all admin roles. Remove any admin-level exemptions.

---

## CCM-006: No Dormant User Accounts

**Category:** Access Control  
**Severity:** Medium

### Intent
Reduce attack surface by identifying and disabling user accounts that have been inactive for extended periods.

### Test Procedure
1. Query all user accounts with last login timestamp
2. Identify accounts with no login in past 90 days
3. Check if dormant accounts have been disabled

### Evidence Expected
- User inventory with last login dates
- List of dormant accounts (>90 days)
- Account status (active/suspended)

### Framework Mappings
- **SOC 2:** CC6.1 (Logical access), CC6.3 (Access reviews)
- **ISO 27001:** A.9.2.5 (User access reviews), A.9.2.6 (Access rights removal)
- **PCI-DSS:** 8.1.4 (Inactive account removal)
- **HIPAA:** 164.308(a)(3)(ii)(C) (Termination procedures)

### Pass Criteria
No user accounts have been inactive for more than 90 days without formal exception or deprovisioning.

### Remediation
Implement automated account deprovisioning after 90 days of inactivity. Require manager attestation for extended dormancy.

---

## CCM-007: Remove Unused Admin Roles

**Category:** Access Control  
**Severity:** Medium

### Intent
Follow principle of least privilege by removing administrative roles that are not actively used.

### Test Procedure
1. Enumerate all admin role assignments
2. Check usage timestamps for each role
3. Identify roles not used in past 60 days

### Evidence Expected
- Admin role assignments with user details
- Last usage timestamp per role
- Role removal workflow documentation

### Framework Mappings
- **SOC 2:** CC6.3 (Least privilege)
- **ISO 27001:** A.9.2.5 (Access reviews), A.9.1.1 (Access control policy)
- **PCI-DSS:** 7.1.2 (Access based on job function)
- **HIPAA:** 164.308(a)(4)(i) (Access authorization)

### Pass Criteria
All admin role assignments have been used within past 60 days or have documented justification.

### Remediation
Review admin role assignments quarterly. Remove unused roles and implement time-limited elevated access (JIT).

---

## CCM-008: GitHub Branch Protection

**Category:** Change Management  
**Severity:** High

### Intent
Prevent unauthorized or unreviewed code changes by requiring pull request reviews before merging to protected branches.

### Test Procedure
1. List all repositories in organization
2. Check branch protection rules for main/master branches
3. Verify required approving review count

### Evidence Expected
- Repository inventory
- Branch protection configuration per repo
- Required reviewers and dismissal settings

### Framework Mappings
- **SOC 2:** CC8.1 (Change management)
- **ISO 27001:** A.12.1.2 (Change management), A.14.2.2 (System change review)
- **PCI-DSS:** 6.3.2 (Segregation of duties), 6.5.3 (Code review)

### Pass Criteria
All production repositories have branch protection requiring at least 1 approving review before merge.

### Remediation
Enable branch protection on all repositories with production code. Require code owner reviews for sensitive directories.

---

## CCM-009: GitHub Organization 2FA Required

**Category:** Access Control  
**Severity:** Critical

### Intent
Enforce two-factor authentication for all members of the GitHub organization to protect source code and CI/CD pipelines.

### Test Procedure
1. Check GitHub organization security settings
2. Verify 2FA requirement is enabled
3. Confirm all members have 2FA enrolled

### Evidence Expected
- Organization security settings
- 2FA requirement status
- Member 2FA compliance report

### Framework Mappings
- **SOC 2:** CC6.1 (Logical access), CC6.2 (Authentication)
- **ISO 27001:** A.9.4.2 (Secure authentication)
- **PCI-DSS:** 8.3.1 (MFA for all access)

### Pass Criteria
GitHub organization requires 2FA for all members with no exemptions.

### Remediation
Enable 2FA requirement in organization settings. Remove members who don't enroll within grace period.

---

## CCM-010: Endpoint Disk Encryption

**Category:** Encryption  
**Severity:** Critical

### Intent
Protect data on endpoint devices through full disk encryption to prevent data loss from stolen or lost devices.

### Test Procedure
1. Query endpoint management system for device inventory
2. Check disk encryption status (FileVault, BitLocker)
3. Verify encryption keys are escrowed

### Evidence Expected
- Endpoint device inventory
- Disk encryption status per device
- Key escrow configuration

### Framework Mappings
- **SOC 2:** CC6.7 (Data encryption)
- **ISO 27001:** A.8.24 (Cryptography), A.8.3.1 (Media handling)
- **PCI-DSS:** 3.4.1 (Disk encryption)
- **HIPAA:** 164.312(a)(2)(iv) (Encryption)

### Pass Criteria
All corporate endpoints have full disk encryption enabled with centrally managed recovery keys.

### Remediation
Deploy endpoint management solution enforcing FileVault (macOS) or BitLocker (Windows). Escrow recovery keys to central vault.

---

## CCM-011: Endpoint Screen Lock

**Category:** Physical Security  
**Severity:** Medium

### Intent
Prevent unauthorized physical access to systems through automatic screen locking after inactivity.

### Test Procedure
1. Query endpoint configuration for screen lock settings
2. Verify timeout is <= 15 minutes
3. Check password requirement on wake

### Evidence Expected
- Endpoint screen lock configuration
- Timeout values per device
- Password requirement status

### Framework Mappings
- **SOC 2:** CC6.6 (Physical access)
- **ISO 27001:** A.11.2.8 (Unattended equipment), A.11.2.9 (Clear desk policy)
- **PCI-DSS:** 8.1.8 (Session timeout)
- **HIPAA:** 164.312(a)(2)(iii) (Automatic logoff)

### Pass Criteria
All endpoints have automatic screen lock configured with timeout <= 15 minutes and password required on wake.

### Remediation
Push endpoint configuration policy enforcing 10-minute screen lock timeout with password requirement.

---

## CCM-012: Regular Access Reviews

**Category:** Access Control  
**Severity:** Medium

### Intent
Periodically review user access rights to ensure they remain appropriate for current job responsibilities.

### Test Procedure
1. Verify access review process is documented
2. Check review frequency (quarterly recommended)
3. Confirm reviews are completed with manager sign-off

### Evidence Expected
- Access review policy documentation
- Review reports with approval signatures
- Remediation tracking for access removals

### Framework Mappings
- **SOC 2:** CC6.3 (Access reviews)
- **ISO 27001:** A.9.2.5 (User access reviews)
- **PCI-DSS:** 7.1.2 (Access review and revalidation)
- **HIPAA:** 164.308(a)(4)(ii)(C) (Access reviews)

### Pass Criteria
Access reviews conducted quarterly with documented manager approval and remediation of findings.

### Remediation
Implement quarterly access review process using automated tools. Require manager attestation and track remediation.

---

## CCM-013: Secure Password Policy

**Category:** Access Control  
**Severity:** High

### Intent
Enforce strong password requirements to prevent credential compromise through brute force or dictionary attacks.

### Test Procedure
1. Review identity provider password policy
2. Verify minimum length >= 12 characters
3. Check complexity requirements and rotation policy

### Evidence Expected
- Password policy configuration
- Minimum length setting
- Complexity rules
- Rotation requirements

### Framework Mappings
- **SOC 2:** CC6.1 (Logical access)
- **ISO 27001:** A.9.4.3 (Password management)
- **PCI-DSS:** 8.2.3 (Password complexity), 8.2.4 (Password changes), 8.2.5 (Password reuse)
- **HIPAA:** 164.308(a)(5)(ii)(D) (Password management)

### Pass Criteria
Password policy requires minimum 12 characters, complexity (upper, lower, number, special), and 90-day rotation.

### Remediation
Update identity provider password policy to meet minimum requirements. Consider passwordless authentication (FIDO2).

---

## CCM-014: Incident Response Plan Testing

**Category:** Incident Management  
**Severity:** High

### Intent
Ensure the organization can effectively respond to security incidents through regular testing of incident response procedures.

### Test Procedure
1. Verify incident response plan is documented
2. Check plan testing frequency (annual minimum)
3. Review test results and remediation tracking

### Evidence Expected
- Incident response plan document
- Test/tabletop exercise reports from last 12 months
- Lessons learned and improvement tracking

### Framework Mappings
- **SOC 2:** CC7.4 (Incident handling), CC7.5 (Incident management)
- **ISO 27001:** A.16.1.1 (Incident management), A.16.1.5 (Incident response testing)
- **PCI-DSS:** 12.10.1 (Incident response plan testing)
- **HIPAA:** 164.308(a)(6)(ii) (Incident response and reporting)

### Pass Criteria
Incident response plan tested at least annually with documented results and improvement actions.

### Remediation
Schedule annual tabletop exercise for security incidents. Document results and track improvement actions.

---

## CCM-015: Vendor Security Assessments

**Category:** Vendor Management  
**Severity:** Medium

### Intent
Ensure third-party vendors meet security requirements before they process, store, or transmit sensitive data.

### Test Procedure
1. Maintain inventory of vendors with data access
2. Verify security assessments completed before data sharing
3. Check assessment refresh frequency (annual)

### Evidence Expected
- Vendor inventory with data classification
- Security assessment documents (SOC 2, questionnaires)
- Assessment tracking with expiry dates

### Framework Mappings
- **SOC 2:** CC9.1 (Vendor management), CC9.2 (Vendor monitoring)
- **ISO 27001:** A.15.1.1 (Vendor policy), A.15.1.2 (Vendor agreements)
- **PCI-DSS:** 12.8.2 (Vendor due diligence), 12.8.4 (Vendor monitoring)
- **HIPAA:** 164.308(b)(1) (Business associate contracts), 164.314(a)(1) (Business associate requirements)

### Pass Criteria
All vendors with access to sensitive data have security assessments completed within past 12 months.

### Remediation
Implement vendor risk management process. Require SOC 2 Type 2 or equivalent for high-risk vendors. Track assessment expiry dates.

---

## Framework Mapping Summary

### SOC 2 TSC Coverage

- **CC6.1 (Logical Access):** CCM-001, 003, 005, 006, 009, 013
- **CC6.2 (Authentication):** CCM-001, 005, 009
- **CC6.3 (Least Privilege):** CCM-006, 007, 012
- **CC6.6 (Physical Access):** CCM-003, 011
- **CC6.7 (Encryption):** CCM-002, 010
- **CC7.2 (Monitoring):** CCM-004
- **CC7.3 (Anomaly Detection):** CCM-004
- **CC7.4 (Incident Handling):** CCM-014
- **CC7.5 (Incident Management):** CCM-014
- **CC8.1 (Change Management):** CCM-008
- **CC9.1 (Vendor Management):** CCM-015
- **CC9.2 (Vendor Monitoring):** CCM-015

### ISO 27001:2022 Annex A Coverage

**Access Control:**
- A.9.1.1, A.9.1.2, A.9.2.1, A.9.2.5, A.9.2.6, A.9.4.2, A.9.4.3

**Cryptography:**
- A.8.24, A.10.1.1

**Operations:**
- A.12.1.2, A.12.4.1, A.12.4.3

**Physical Security:**
- A.11.2.8, A.11.2.9

**Supplier Relationships:**
- A.15.1.1, A.15.1.2

**Incident Management:**
- A.16.1.1, A.16.1.5

### PCI-DSS v4 Coverage

**Requirement 1 (Network Security):** CCM-003  
**Requirement 3 (Data Protection):** CCM-002, 010  
**Requirement 6 (Secure Development):** CCM-008  
**Requirement 7 (Access Control):** CCM-007, 012  
**Requirement 8 (User Identity):** CCM-001, 005, 006, 009, 011, 013  
**Requirement 10 (Logging):** CCM-004  
**Requirement 12 (Security Governance):** CCM-014, 015

### HIPAA Security Rule Coverage

**164.308(a) - Administrative Safeguards:**
- (a)(3)(ii)(C) - Termination: CCM-006
- (a)(4)(i) - Access authorization: CCM-007
- (a)(4)(ii)(C) - Access reviews: CCM-012
- (a)(5)(ii)(D) - Password management: CCM-013
- (a)(6)(ii) - Incident response: CCM-014
- (b)(1) - Business associates: CCM-015

**164.312 - Technical Safeguards:**
- (a)(1) - Access control: CCM-003
- (a)(2)(i) - Unique user ID: CCM-001, 005
- (a)(2)(iii) - Automatic logoff: CCM-011
- (a)(2)(iv) - Encryption: CCM-002, 010
- (b) - Audit controls: CCM-004
- (e)(2)(ii) - Encryption: CCM-002

**164.314(a) - Organizational Requirements:**
- (a)(1) - Business associate requirements: CCM-015
