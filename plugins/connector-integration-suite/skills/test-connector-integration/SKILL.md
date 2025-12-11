---
name: test-connector-integration
description: |
  Run comprehensive integration tests for connectors including cargo tests,
  gRPC tests, and webhook verification. Validates implementation against
  actual specifications. Use when testing connector implementations,
  running integration tests, or validating deployments.
  Auto-activates for requests like: "test [connector] integration",
  "run connector tests for", "validate [connector] implementation",
  "verify webhook handling".
allowed-tools: Read, Write, Bash, Grep, Glob
version: 1.0.0
---

# Test Connector Integration Skill

## Overview

Run comprehensive integration tests for connector implementations including cargo tests, gRPC tests, and webhook verification. Validates that the connector works correctly with UCS.

## When to Use This Skill

Auto-activates for these request patterns:
- "Test [connector] integration"
- "Run connector tests for [connector]"
- "Validate [connector] implementation"
- "Verify webhook handling"

Also useful for:
- Pre-deployment validation
- Regression testing
- Performance testing
- Webhook verification

## Input Context

The skill receives these parameters:
- `connector_name` (required): Name of the connector
- `implementation_plan_path` (required): Path to implementation_plan.md

## Testing Process

### Phase 0: Consult Testing Guide

Read testing strategy reference:

```bash
Read(".claude/skills/test-connector-integration/references/testing-guide.md")
Read(".claude/knowledge/connector_integration_guide.md")
```

Refer to **Section 8: For the Coder-Reviewer-Tester Loop** for testing standards.

### Phase 1: Integration Tests

Run standard integration tests:
```bash
cargo test {connector_name}_integration_test
```

**Expected Test Structure**:
```rust
#[cfg(feature = "connector_{connector_name}")]
mod connector_{connector_name} {
    use super::*;

    #[test]
    fn authorize_test() { }
    fn capture_test() { }
    fn refund_test() { }
    // Tests for each supported flow
}
```

**Test Results**:
- **Success**: All tests pass
- **Failure**: Analyze output, report issues to Implementation Agent

### Phase 2: gRPC Testing

Run gRPC tests for all flows defined in implementation plan:

```bash
# Get flows from implementation plan
grep "| Flow |" {implementation_plan_path} | tail -n +2 | cut -d'|' -f2 | tr -d ' '

# For each flow, construct grpcurl command
grpcurl -plaintext \
  -H "x-tenant-id: default" \
  -d '{"request_ref_id": {"id": "test123"}, "amount": 1000}' \
  localhost:50051 \
  payment.PaymentService/{FlowName}
```

**Example Commands**:

**Authorize**:
```bash
grpcurl -plaintext \
  -H "x-tenant-id: default" \
  -d '{"request_ref_id": {"id": "test123"}, "amount": 1000, "currency": "USD", "payment_method_data": {...}}' \
  localhost:50051 \
  payment.PaymentService/Authorize
```

**Capture**:
```bash
grpcurl -plaintext \
  -H "x-tenant-id: default" \
  -d '{"request_ref_id": {"id": "test123"}, "amount": 500}' \
  localhost:50051 \
  payment.PaymentService/Capture
```

**Refund**:
```bash
grpcurl -plaintext \
  -H "x-tenant-id: default" \
  -d '{"request_ref_id": {"id": "test123"}, "amount": 500}' \
  localhost:50051 \
  payment.PaymentService/Refund
```

**gRPC Testing Rules**:
1. Include required headers (e.g., `x-tenant-id: default`)
2. Verify successful responses (Status: `Charged`, `Pending`, `Failed`)
3. Check response contains valid reference IDs
4. Validate amount conversions worked correctly

### Phase 3: Webhook Verification

If connector supports webhooks:

```bash
# Check if webhooks are supported in spec
grep -i "webhook" {spec_path}

# If supported, test webhook handling
curl -X POST http://localhost:8080/webhooks/{connector_name} \
  -H "Content-Type: application/json" \
  -d @test_webhook_payload.json

# Verify payment status updated
# Check logs for correct processing
```

**Webhook Test Cases**:
- Payment succeeded notification
- Payment failed notification
- Refund succeeded notification
- Refund failed notification

**Validation**:
- Webhook processor handles event
- Payment status updated correctly
- No errors in logs
- Idempotency maintained

### Phase 4: Performance Testing

Run basic performance tests:
```bash
# Run multiple rapid requests
for i in {1..10}; do
  grpcurl -plaintext -H "x-tenant-id: default" \
    -d '{"request_ref_id": {"id": "perf'$i'"}, "amount": 1000}' \
    localhost:50051 \
    payment.PaymentService/Authorize &
done
wait

# Check for race conditions, timeouts, or failures
```

### Phase 5: Error Handling Testing

Test error scenarios:
```bash
# Invalid credentials
# Wrong amount format
# Invalid payment method
# Network timeout handling

# Verify graceful error responses
# Check error mapping is correct
# Validate no panics or crashes
```

## Output

Create `.claude/context/connectors/<connector_name>/testing_report.md`:

```markdown
# Testing Report - {Connector Name}

## Test Summary
- **Overall Status**: {✅ PASS/❌ FAIL}
- **Date**: {timestamp}
- **Duration**: {minutes}

## Integration Tests (cargo test)
- **Status**: {✅ PASS/❌ FAIL}
- **Tests Run**: {N}
- **Tests Passed**: {N}
- **Tests Failed**: {N}
- **Output Summary**:
  ```
  {cargo test output}
  ```

## gRPC Tests
| Flow | Command | Result | Response Time | Status |
|------|---------|--------|---------------|---------|
| Authorize | `grpcurl ...` | ✅ Success | 250ms | Charged |
| Capture | `grpcurl ...` | ✅ Success | 200ms | Charged |
| Refund | `grpcurl ...` | ✅ Success | 300ms | Refunded |
| Void | `grpcurl ...` | ⚠️ Skipped | N/A | N/A |

**Total**: {N}/{N} flows tested

## Webhook Verification
- **Status**: {✅ PASS/⚠️ SKIPPED/❌ FAIL}
- **Webhooks Tested**: {N}
- **Details**:
  - Payment Notification: {✅/❌}
  - Refund Notification: {✅/❌}
  - Failed Payment Notification: {✅/❌}

**Verification**:
- Webhook processor handled events: {✅/❌}
- Status updates correct: {✅/❌}
- No errors in logs: {✅/❌}

## Performance Testing
- **Requests**: 10 concurrent
- **Success Rate**: 100%
- **Average Response Time**: 250ms
- **Errors**: 0
- **Throughput**: 40 req/sec

## Error Handling
- **Invalid Credentials**: {✅ Handled correctly/❌ Crashed}
- **Invalid Amount**: {✅ Handled correctly/❌ Crashed}
- **Invalid Payment Method**: {✅ Handled correctly/❌ Crashed}
- **Network Timeout**: {✅ Handled correctly/❌ Crashed}

**Error Mapping**: All connector errors correctly mapped to UCS error types

## Test Environment
- **Rust Version**: {version}
- **UCS Version**: {version}
- **Connector Version**: {version}
- **Base URL**: {sandbox/production}

## Issues Found
{If any issues were discovered, list them here}

## Recommendations
- {Any improvements or follow-up actions}

## Final Verdict
{✅ Ready for Release / ❌ Needs Fixes}

**Next Steps**:
1. {action items if any}
2. {deployment steps}
3. {monitoring recommendations}
```

## Examples

### Standalone Usage

**User**: "Run integration tests for the Stripe connector"

**Skill Action**:
1. Reads implementation plan
2. Runs cargo integration tests
3. Executes gRPC tests for all flows
4. Tests webhook handling (if applicable)
5. Creates comprehensive testing report

**Output**: Pass/fail verdict with detailed test results

### Orchestrated Usage

Called by `/connector-integrate` after successful review:
1. Tests the approved connector
2. Runs comprehensive validation
3. Creates final testing report
4. Reports success to user

## Integration

**Prerequisites**:
- Code approved by `review-connector-quality` skill
- Implementation plan from `plan-connector-implementation` skill

**Dependents**:
- `/connector-integrate` orchestrates this as final Phase 5

**Command Integration**: The `/connector-integrate` command invokes this skill after review approval.

## References

- Testing Guide: `.claude/skills/test-connector-integration/references/testing-guide.md`
- Integration Guide: `.claude/knowledge/connector_integration_guide.md`