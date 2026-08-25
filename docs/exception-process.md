# Exception Process

## Overview

Risk exceptions (also called risk acceptances or control exceptions) allow an organization to acknowledge a failing control while documenting compensating controls and accepting the residual risk for a defined period.

This is a standard practice in GRC programs and required by most compliance frameworks.

## When to Use Exceptions

Valid scenarios for exceptions include:

- **Implementation in progress**: Control is being rolled out but not yet complete
- **Technical limitations**: Current technology doesn't support the control
- **Business constraints**: Legitimate business need conflicts with control
- **Compensating controls**: Alternative measures provide equivalent protection

Invalid scenarios:

- ❌ Avoiding fixing a problem indefinitely
- ❌ Hiding findings from auditors
- ❌ Circumventing policy without approval

## Exception Lifecycle

```
[Control Fails] → [Exception Request] → [Approval] → [Active] → [Renewal/Remediation] → [Closed]
```

### 1. Exception Request

When a control fails, the control owner may request an exception.

Required information:
- **Control ID**: Which control is failing
- **Reason**: Why the control cannot be met
- **Compensating Control**: What alternative measures are in place
- **Expiry Date**: When this exception must be reviewed or remediated
- **Approver**: Who accepts the risk (typically CISO, Risk Manager, or Compliance Officer)

### 2. Approval

The designated risk owner reviews the request and either:
- **Approves**: Exception is active and the control won't fail scans
- **Rejects**: Control must be remediated before acceptance
- **Requests changes**: More detail or stronger compensating controls needed

### 3. Active Exception

While active and unexpired, the exception:
- Changes control status from `fail` to `accepted` in scans
- Appears in reports and dashboards
- Stores the compensating control details for auditors
- Tracks expiry date for automatic notification

### 4. Renewal or Remediation

Before expiry:
- **Remediate**: Fix the underlying issue and deactivate the exception
- **Renew**: If the situation hasn't changed, request a new exception (requires fresh approval)

If an exception expires without renewal:
- The control reverts to `fail` status in the next scan
- CI/CD pipelines may fail
- Alerts notify the compliance team

## Using CCM for Exceptions

### Add an Exception

```bash
ccm exception add CCM-AC-001 \
  --reason "MFA rollout in progress, completing Q3 2024" \
  --compensating "Weekly manual review of privileged access logs" \
  --expires 2024-09-30 \
  --approver "Jane Doe, CISO"
```

This creates an exception that:
- Applies to control `CCM-AC-001`
- Is valid until September 30, 2024
- Documents the compensating control for auditors
- Records the risk owner who approved it

### List Exceptions

```bash
# All active exceptions
ccm exception list

# Exceptions for a specific control
ccm exception list --control CCM-AC-001

# Include expired exceptions
ccm exception list --include-expired
```

### Scan Behavior

When a scan runs:

1. Collector executes and returns `fail` status
2. Scanner checks for a valid exception
3. If found:
   - Status changes to `accepted`
   - Exception details are attached to evidence
   - Exception ID is logged
4. If not found or expired:
   - Status remains `fail`
   - CI/CD job exits with code 1

### Exception Data Structure

Exceptions are stored in `exceptions.json`:

```json
{
  "id": "a3f2c1d4",
  "control_id": "CCM-AC-001",
  "reason": "MFA rollout in progress",
  "compensating_control": "Weekly manual review of privileged access logs",
  "expiry_date": "2024-09-30T00:00:00",
  "approver": "Jane Doe, CISO",
  "created_date": "2024-06-15T10:30:00",
  "is_active": true
}
```

## Auditor Expectations

External auditors will:

1. Review all active exceptions
2. Verify compensating controls are documented and reasonable
3. Check that expiry dates are appropriate (typically 90-180 days)
4. Confirm approver has authority to accept risk
5. Test that compensating controls are actually in place

**Do not:**
- Create permanent exceptions (> 1 year)
- Use vague compensating controls ("we'll be careful")
- Stack multiple exceptions on the same control without strong justification

## Exception Reports

Exceptions appear in:

- **CLI output**: `ccm exception list`
- **Dashboard**: Orange warning badges
- **Scan reports**: Separate section for accepted risks
- **Evidence files**: Included in JSON details

Example from scan report:

```
### ACCEPTED ⚠

#### CCM-AC-001: Multi-Factor Authentication Required for Privileged Users
- Status: accepted
- Message: 1 privileged user(s) without MFA (Exception a3f2c1d4: MFA rollout in progress)
- Compensating Control: Weekly manual review of privileged access logs
- Approver: Jane Doe, CISO
- Expires: 2024-09-30
```

## Integration with GRC Platforms

CCM exceptions are designed to complement, not replace, your GRC tool:

- **Export to Vanta/Drata**: Use `ccm export-evidence` and upload as custom test results
- **Jira/Linear**: Create tickets for exception remediation with expiry date as due date
- **Slack/Email**: Script notifications for expiring exceptions

## Best Practices

### For Security Teams

- Review all exceptions monthly
- Set expiry dates no longer than 90 days for critical controls
- Require strong compensating controls, not just acknowledgment
- Track metrics: total exceptions, average duration, renewal rate

### For Engineering Teams

- Fix the root cause rather than renewing exceptions repeatedly
- Propose compensating controls that are technical, not just procedural
- Run `ccm scan` in CI to catch expired exceptions before auditors do

### For Compliance Teams

- Maintain a register of all exceptions in your GRC platform
- Provide exception template and approval workflow
- Include exception review in audit readiness checklist
- Train teams on when exceptions are appropriate

## Example Scenarios

### Scenario 1: MFA Rollout

**Situation**: You're rolling out MFA for all privileged users but it's not complete yet.

**Exception**:
- Reason: "MFA enforcement begins Aug 1, current rollout at 60%"
- Compensating: "Increased login monitoring, anomaly detection alerts"
- Expiry: 60 days
- Approver: CISO

### Scenario 2: Legacy System

**Situation**: A legacy application doesn't support MFA and is scheduled for decommission.

**Exception**:
- Reason: "Legacy system does not support MFA, decommission planned Q4"
- Compensating: "IP allowlist, VPN required, enhanced audit logging"
- Expiry: Until decommission date
- Approver: CTO + CISO (joint approval for long-term exception)

### Scenario 3: Public S3 Bucket

**Situation**: A bucket must be public for website hosting but contains no sensitive data.

**Exception**:
- Reason: "Marketing website assets, public by design"
- Compensating: "No PII/PCI/PHI allowed in bucket, automated scanning for secrets"
- Expiry: Annual review
- Approver: CISO

**Note**: This might be better solved by excluding the bucket from scans or changing the control definition rather than a perpetual exception.

## Questions?

- **"How long should an exception last?"** 
  90 days for critical/high, 180 days for medium, up to 1 year for low severity with strong compensating controls.

- **"Who can approve exceptions?"**
  Typically CISO, Risk Manager, or Compliance Officer. Document approval authority in your policy.

- **"Can I have multiple exceptions for one control?"**
  Rare. If the same control fails for different reasons, consider whether your control is too broad.

- **"Do auditors accept exceptions?"**
  Yes, if documented properly. They're looking for mature risk management, not perfection.
