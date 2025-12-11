# Quality Checklist - Reviewer Reference

## Pre-Review Setup

- [ ] Read Section 6: Core UCS Architecture Rules
- [ ] Read Section 7: Quality Checklist (this document)
- [ ] Read Section 8: Reviewer Checklist
- [ ] Review implementation plan and specification
- [ ] Note iteration number (for tracking history)

## Architecture Compliance

### Types (Critical)
- [ ] Uses `RouterDataV2` (NOT `RouterData`)
- [ ] Uses `ConnectorIntegrationV2` (NOT `ConnectorIntegration`)
- [ ] Imports from `domain_types` (NOT `hyperswitch_domain_models`)
- [ ] Imports from `interfaces::connector_integration_v2` (NOT `interfaces::ConnectorIntegration`)

**Check with**:
```bash
grep -r "RouterData[^V2]" code_path --include="*.rs"  # Should return nothing
grep -r "ConnectorIntegration[^V2]" code_path --include="*.rs"  # Should return nothing
```

### Generic Type Parameter
- [ ] Connector struct has generic `<T>`
- [ ] Generic used for trait bounds (JwtSigner, Hypervisor)
- [ ] No compiler warnings about unused type parameters

**Check**:
```rust
// ✅ CORRECT
struct Stripe<T> { }

// ❌ WRONG
struct Stripe { }
```

## Amount Handling

### MinorUnit Usage
- [ ] Uses `MinorUnit` type for amounts (NOT i64, f64, or primitives)
- [ ] Amount converter declared in `create_all_prerequisites!`
- [ ] Proper conversion logic from RouterData to connector format
- [ ] Amounts displayed correctly in requests/responses

**Check**:
```bash
# Look for primitive amount types (should not exist)
grep -r "amount: i64" code_path --include="*.rs"  # Should return nothing
grep -r "amount: f64" code_path --include="*.rs"  # Should return nothing
```

### Amount Converter Declaration
- [ ] Correct converter type specified (StringMinorUnit, StringMajorUnit, or FloatMajorUnit)
- [ ] Converter type matches implementation plan decision
- [ ] Converter used consistently throughout code

**Check**:
```rust
// In create_all_prerequisites!
amount_converters: [
    amount_converter: StringMinorUnit,  // Matched from implementation plan
],
```

## Reference ID Integrity

### Extraction
- [ ] Reference IDs extracted from connector responses
- [ ] IDs stored in `RouterDataV2` fields (payment_id, authorization_id, etc.)
- [ ] No hardcoded IDs anywhere in code
- [ ] No ID mutations (no modifying received IDs)

**Check**:
```bash
# Look for hardcoded IDs (should not exist)
grep -r "\"hardcoded\"" code_path --include="*.rs"  # Should return nothing
grep -r "\"fixed_id\"" code_path --include="*.rs"  # Should return nothing
```

### Usage
- [ ] Reference IDs used for subsequent API calls (PSync, Capture, Refund)
- [ ] IDs passed correctly between flows
- [ ] No ID generation or fabrication

## Status Mapping

### Payment Statuses
- [ ] `succeeded` → `Charged`
- [ ] `pending` → `Pending`
- [ ] `failed` → `Failed`
- [ ] `canceled` → `Failed`
- [ ] **Unknown statuses → `Pending` (NOT `Failed`)**

### Refund Statuses
- [ ] `succeeded` → `Refunded`
- [ ] `pending` → `Pending`
- [ ] `failed` → `Failed`

### Void Statuses
- [ ] `succeeded` → `Voided`
- [ ] `pending` → `Pending`
- [ ] `failed` → `Failed`

**Critical Rule**: Unknown statuses ALWAYS map to `Pending`, never `Failed`

## Authentication

### Auth Type
- [ ] Auth type matches implementation plan (HeaderKey, CreateAccessToken, Signature, MultiHeaderKey)
- [ ] Correct implementation for chosen auth type
- [ ] No hardcoded credentials
- [ ] Credentials use `Secret<T>` wrapper

### CreateAccessToken Flow
- [ ] If auth type is `CreateAccessToken`:
  - [ ] Separate token endpoint handling
  - [ ] Token refresh logic implemented
  - [ ] Token expiry handling
  - [ ] Client ID and Secret properly stored

## Security

### No Unsafe Code
- [ ] No `unsafe` blocks in code
- [ ] No `unwrap()` calls on fallible operations
- [ ] Proper error handling with `?` operator

**Check**:
```bash
# Look for unsafe (should not exist)
grep -r "unsafe {" code_path --include="*.rs"  # Should return nothing

# Look for unwrap (should not exist on fallible operations)
grep -r "\.unwrap()" code_path --include="*.rs"  # Should return nothing
```

### Secret Management
- [ ] Credentials stored in `Secret<T>` wrapper
- [ ] No credential logging
- [ ] No credential exposure in errors

**Check**:
```rust
// ✅ CORRECT
struct Config {
    pub api_key: Secret<String>,
}

// ❌ WRONG
struct Config {
    pub api_key: String,
}
```

## Code Quality

### Error Handling
- [ ] Uses `?` operator for error propagation
- [ ] Proper error context added
- [ ] No manual match statements for error handling

### Pattern Matching
- [ ] Proper match statements for enums
- [ ] Catch-all cases (e.g., `_ =>`) where appropriate
- [ ] No unwrap() in match arms

### Naming
- [ ] Clear, descriptive variable names
- [ ] Consistent naming conventions
- [ ] No single-letter variables (except well-known patterns)

### Documentation
- [ ] Complex logic has comments
- [ ] Public functions have doc comments
- [ ] No commented-out code

## Macro Framework

### create_all_prerequisites!
- [ ] Macro called with correct connector name
- [ ] All supported flows listed
- [ ] Amount converter specified
- [ ] Request/response types match transformers

### macro_connector_implementation!
- [ ] Called for each supported flow
- [ ] Correct transformer functions referenced
- [ ] Request transformer: `From<&RouterDataV2<T>>`
- [ ] Response transformer: `TryFrom<ConnectorResponse>`

## Module Declarations

### connectors.rs
- [ ] Module declaration added
- [ ] Feature flag gate added
- [ ] Export statement correct

**Check**:
```rust
// In connectors.rs
pub mod stripe;

#[cfg(feature = "connector_stripe")]
pub use stripe::Stripe;
```

### Config Files
- [ ] Development.toml updated with base URL
- [ ] Production config (if needed)

## Build Success

### Compilation
- [ ] `cargo build` succeeds with no errors
- [ ] No compiler warnings
- [ ] All dependencies resolved

**Check**:
```bash
cargo build 2>&1 | grep -i error  # Should return no errors
```

### Clippy
- [ ] `cargo clippy` shows no warnings
- [ ] No style violations
- [ ] No complexity warnings that need addressing

## Flow-Specific Checks

### Authorize
- [ ] Proper payment method handling
- [ ] Customer data extraction
- [ ] Amount validation
- [ ] Status mapping correct

### Capture
- [ ] References authorization ID correctly
- [ ] Partial capture supported (if applicable)
- [ ] Capture amount handling correct

### Refund
- [ ] References payment/capture ID
- [ ] Refund amount handling
- [ ] Partial refund supported (if applicable)

### Void
- [ ] References authorization ID
- [ ] Pre-capture validation

### PSync
- [ ] Retrieves payment status correctly
- [ ] Maps connector status to UCS status
- [ ] Handles payment not found errors

### RSync
- [ ] Retrieves refund status correctly
- [ ] Maps connector status to UCS refund status

## Common Violations (Auto-Block)

These violations automatically trigger BLOCK regardless of score:

1. ❌ Using `RouterData` instead of `RouterDataV2`
2. ❌ Hardcoded reference IDs
3. ❌ Mutated reference IDs
4. ❌ Primitive amount types (i64, f64) instead of MinorUnit
5. ❌ Unknown statuses mapped to `Failed` instead of `Pending`
6. ❌ Unsafe code blocks
7. ❌ Unwrap() calls on fallible operations
8. ❌ Missing generic type parameter on connector struct
9. ❌ Using `hyperswitch_domain_models` instead of `domain_types`
10. ❌ Hardcoded credentials

## Scoring

### Critical Issues (20 points each)
- Wrong architecture types
- Security violations (unsafe, hardcoded creds)
- Hardcoded reference IDs
- Missing generic parameters
- Build failures

### Warnings (5 points each)
- Code style issues
- Clippy warnings
- Missing documentation
- Suboptimal error handling

### Suggestions (1 point each)
- Naming improvements
- Code organization
- Documentation enhancements

## Review Report Requirements

### For BLOCKED Reviews (score < 90)
Must include:
- [ ] Exact file:line locations for each critical issue
- [ ] Required fix for each issue
- [ ] Example of correct code
- [ ] Remaining issues to fix for approval

### For APPROVED Reviews (score ≥ 90)
Must include:
- [ ] Score breakdown
- [ ] Critical issues (if any) with warnings
- [ ] Suggestions for improvement
- [ ] Ready for testing phase

## Iteration Tracking

For re-reviews, track:
- [ ] Previous iteration score
- [ ] Which issues were fixed
- [ ] New issues introduced
- [ ] Overall progress

```yaml
iteration_memory:
  iteration_1:
    score: 45
    issues: [CRIT-001, CRIT-002, WARN-001]
  iteration_2:
    score: 72
    issues_fixed: [CRIT-001, CRIT-002]
    new_issues: [WARN-002]
```

## Final Decision

### APPROVED (score ≥ 90)
- [ ] Code meets quality standards
- [ ] Ready for testing phase
- [ ] No critical issues remain
- [ ] Build succeeds

### BLOCKED (score < 90)
- [ ] Critical issues present
- [ ] Requires fixes before approval
- [ ] Feedback loop initiated
- [ ] Re-review after fixes

**Remember**: Quality score determines if code can proceed to testing and deployment.