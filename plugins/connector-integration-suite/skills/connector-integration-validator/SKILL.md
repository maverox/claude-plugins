---
name: connector-integration-validator
description: |
  Validate connector integration changes against official API documentation and UCS architecture patterns. Verifies authentication, payment flows, amount converters, and status mappings. Auto-activates for: "validate connector", "review connector integration", "check connector patterns", "verify UCS compliance".
allowed-tools: Read, Grep, Glob, Bash, Write, Skill, WebFetch
version: 1.0.0
---

# Connector Integration Validator Skill

## Overview

This skill performs specialized validation of connector integration code against official API documentation and UCS (Universal Connector Service) architecture patterns. It goes beyond generic code quality to ensure connector-specific correctness, including API conformance, authentication patterns, flow implementations, and data transformations.

## When to Use This Skill

This skill **auto-activates** when users request:
- "Validate connector changes in PR #238"
- "Review Stripe connector integration"
- "Check connector patterns"
- "Verify UCS compliance for this connector"
- "Validate connector against API docs"
- "Review connector implementation"

The skill can also be invoked as part of `/pr-review` workflow when connector integration files are detected.

## Input Context

The skill expects one of the following:

1. **PR Number with connector changes**:
   ```
   User: "Validate connector in PR #238"
   → Auto-detects connector from changed files
   → Identifies connector name (e.g., "stripe")
   ```

2. **Specific connector files**:
   ```
   User: "Validate backend/connector-integration/src/connectors/stripe.rs"
   → Extracts connector name: "stripe"
   ```

3. **Connector name explicitly**:
   ```
   User: "Validate the Stripe connector integration"
   → Connector name: "stripe"
   ```

4. **Output from pr-analysis skill**:
   ```
   pr-analysis detected: connector_integration scope
   connector_name: stripe
   ```

## Process

### Step 1: Identify Connector

**From PR Changes**:
```bash
# Get changed files in connector directory
gh pr diff {pr-number} --name-only | grep "backend/connector-integration/src/connectors/"

# Extract connector name
# Example: backend/connector-integration/src/connectors/stripe.rs → "stripe"
```

**From File Path**:
```bash
# Parse path: connectors/{name}.rs or connectors/{name}/transformers.rs
```

### Step 2: Read Implementation Code

Read all connector files:
- Main file: `backend/connector-integration/src/connectors/{name}.rs`
- Transformers: `backend/connector-integration/src/connectors/{name}/transformers.rs`
- Tests: `backend/connector-integration/tests/{name}_tests.rs` (if exists)

**Extract Implementation Details**:
- Flows implemented (Authorize, Capture, Void, Refund, etc.)
- Authentication method used
- Amount converter type
- Status mapping logic
- API endpoints used
- Request/response structures

---

### Step 2.5: Extract Line Numbers from NEW File

**CRITICAL**: When identifying issues, extract line numbers from the **NEW file version** (PR HEAD commit) for GitHub API compatibility.

**Process** (same as code-quality-review):

#### A. Get PR HEAD Commit SHA

```bash
HEAD_SHA=$(gh pr view {pr-number} --repo {owner}/{repo} --json headRefOid -q '.headRefOid')
```

#### B. Fetch File Content at HEAD Commit

```bash
gh api repos/{owner}/{repo}/contents/{file-path}?ref=$HEAD_SHA \
  --jq '.content' | base64 -d > /tmp/connector_file.rs
```

#### C. Find Line Numbers

```bash
# Find line number for issue
LINE_NUM=$(grep -n "{pattern}" /tmp/connector_file.rs | head -1 | cut -d: -f1)

# Extract code at line
CODE=$(sed -n "${LINE_NUM}p" /tmp/connector_file.rs)
```

#### D. Validate

```bash
FILE_LENGTH=$(wc -l < /tmp/connector_file.rs)

if (( LINE_NUM > 0 && LINE_NUM <= FILE_LENGTH )); then
  # Valid - include in output
  echo "✅ Line $LINE_NUM is valid"
fi
```

**Reference**: See `.claude/skills/code-quality-review/references/line-number-extraction.md` for complete guide.

**Output Requirements**:
- ✅ Use `line_number` field (not `line`)
- ✅ Include `line_reference: "NEW_FILE"`
- ✅ Include `commit_sha` from PR HEAD
- ❌ Never use diff positions

---

### Step 3: Fetch API Documentation

**Option A: Use Existing Spec** (Fast)
```bash
# Check if spec already exists
if [ -f .claude/context/connectors/{name}/spec.md ]; then
  # Use existing spec
  cat .claude/context/connectors/{name}/spec.md
fi
```

**Option B: Invoke research-api-docs Skill** (Fresh validation)
```
# Invoke skill to fetch latest API documentation
Skill("research-api-docs")

# Provide connector name and optional API URL
Connector: {name}
API URL: {detected_or_provided_url}
```

**Option C: Web Search** (Fallback)
```bash
# Search for official API documentation
WebFetch("{connector_name} API documentation")
```

### Step 4: Validate Against API Patterns

#### **Authentication Validation**

Compare implementation against API docs:

**Questions**:
1. Does the connector use the correct auth method?
   - API Key (Header/Query)?
   - OAuth?
   - Basic Auth?
   - Custom auth?

2. Is auth extracted from `connector_auth_type` correctly?

3. Are auth headers/params formatted as per API docs?

**Example Validation**:
```rust
// Implementation
let api_key = match &router_data.connector_auth_type {
    ConnectorAuthType::HeaderKey { api_key } => api_key,
    _ => return Err(Error::InvalidAuthType),
};

// Check against docs
API Documentation says: "Authorization: Bearer {api_key}"

✅ PASS: Matches documentation pattern
❌ FAIL: Implementation uses different auth method
```

---

#### **Endpoint Validation**

**Questions**:
1. Are endpoints correct according to API docs?
2. Is the base URL correct (production/sandbox)?
3. Do path parameters match documentation?

**Example Validation**:
```rust
// Implementation
url = format!("{}/payments/authorize", base_url);

// API docs say
POST /v1/payments

❌ FAIL: Path doesn't match documentation
Expected: /v1/payments
Found: /payments/authorize
```

---

#### **Flow Implementation Validation**

For each implemented flow (Authorize, Capture, etc.):

**Authorize Flow**:
- [ ] Creates a payment authorization
- [ ] Returns transaction ID
- [ ] Includes required fields (amount, currency, payment method)
- [ ] Handles 3DS authentication if applicable
- [ ] Maps status correctly (success → Charged, pending → Pending)

**Capture Flow**:
- [ ] References existing authorization
- [ ] Can capture partial amounts (if supported)
- [ ] Returns final status
- [ ] Updates transaction state

**Void Flow**:
- [ ] Cancels authorization before capture
- [ ] Returns success/failure status
- [ ] Only works on authorized (not captured) payments

**Refund Flow**:
- [ ] References captured payment
- [ ] Supports partial refunds (if API supports)
- [ ] Returns refund ID
- [ ] Maps status correctly (success → Success, partial → Pending)

**Example Validation**:
```
API Documentation:
- Authorize: POST /v1/authorize
  Required: amount, currency, card
  Returns: transaction_id, status

Implementation:
✅ POST /v1/authorize - Correct
✅ Includes amount, currency, card - Correct
✅ Extracts transaction_id from response - Correct
❌ Status mapping: "pending" → Failure (should be Pending)

Result: 1 issue found in Authorize flow
```

---

#### **Amount Converter Validation**

**Questions**:
1. Does the API expect amount as integer (cents) or string?
2. Is the correct converter used in `create_all_prerequisites!`?
3. Are amounts converted correctly in transformers?

**Amount Converter Types**:
- `MinorUnit` - Direct minor unit (cents) as integer
- `StringMinorUnit` - Minor unit as string
- `DecimalAmount` - Decimal representation (e.g., "10.50")

**Example Validation**:
```rust
// Implementation
amount_converters: [amount_converter: StringMinorUnit]

// Transformer
amount: router_data.request.amount.to_string()

// API docs say
"amount": "1000"  (string, minor units)

✅ PASS: StringMinorUnit is correct for this API
```

**Counter-example**:
```rust
// Implementation
amount_converters: [amount_converter: MinorUnit]

// Transformer
amount: router_data.request.amount.get_amount_as_i64()

// API docs say
"amount": "10.50"  (string, decimal)

❌ FAIL: Should use DecimalAmount converter
```

---

#### **Status Mapping Validation**

Validate status mapping against API documentation:

**Payment Status Mapping**:
```rust
// API provides these statuses
"succeeded", "pending", "failed", "requires_action"

// Implementation
status: match api_status {
    "succeeded" => AttemptStatus::Charged,
    "pending" => AttemptStatus::Pending,
    "failed" => AttemptStatus::Failure,
    "requires_action" => AttemptStatus::AuthenticationPending,
    _ => AttemptStatus::Pending,  // Unknown → Pending
}

✅ PASS: Status mapping follows UCS conventions
```

**Refund Status Mapping**:
```rust
// API provides
"succeeded", "pending", "failed"

// Implementation
status: match refund_status {
    "succeeded" => RefundStatus::Success,
    "pending" => RefundStatus::Pending,
    "failed" => RefundStatus::Failure,
    _ => RefundStatus::Pending,
}

✅ PASS: Refund status mapping correct
```

**Common Issues**:
- Mapping unknown statuses to Failure (should be Pending)
- Not handling 3DS statuses (requires_action, etc.)
- Incorrect refund status when partially refunded

---

#### **Request/Response Structure Validation**

**Request Validation**:
- [ ] All required fields from API are included
- [ ] Optional fields handled correctly (skip_serializing_if)
- [ ] Field names match API (or use #[serde(rename)])
- [ ] Nested structures match API format

**Response Validation**:
- [ ] All fields from API response are handled
- [ ] Required fields are not optional
- [ ] Error responses are parsed correctly
- [ ] Unexpected fields don't cause failures (use #[serde(flatten)])

**Example**:
```rust
// API docs
POST /authorize
{
  "amount": "1000",
  "currency": "USD",
  "card": {
    "number": "...",
    "exp_month": "12",
    "exp_year": "2025"
  }
}

// Implementation
#[derive(Serialize)]
struct AuthorizeRequest {
    amount: String,
    currency: String,
    card: CardDetails,
}

#[derive(Serialize)]
struct CardDetails {
    number: String,
    exp_month: String,
    exp_year: String,
}

✅ PASS: Structure matches API documentation
```

---

### Step 5: Validate UCS Compliance

Check against UCS architecture patterns:

#### **Type System Compliance**

- [ ] Uses `RouterDataV2` (not `RouterData`)
- [ ] Uses `ConnectorIntegrationV2` (not `ConnectorIntegration`)
- [ ] Amount fields use `MinorUnit`
- [ ] Flow types from `domain_types::router_flow_type`

#### **Macro Usage**

- [ ] `create_all_prerequisites!` macro present
- [ ] All flows declared in prerequisites
- [ ] `macro_connector_implementation!` for each flow
- [ ] Amount converter declared

#### **Reference ID Handling**

- [ ] Reference ID from `router_data.connector_request_reference_id`
- [ ] No hardcoded reference IDs
- [ ] No mutation of reference IDs
- [ ] Reference ID included in API requests

#### **Error Handling**

- [ ] No `unwrap()` or `expect()`
- [ ] Proper `Result` types
- [ ] Errors propagated with `?`
- [ ] Error types defined

---

### Step 6: Cross-Reference with Existing Connectors

Compare implementation with similar connectors:

**Find Similar Connectors**:
```bash
# If Stripe-like (card payments)
Reference: backend/connector-integration/src/connectors/stripe.rs

# If PayPal-like (wallet payments)
Reference: backend/connector-integration/src/connectors/paypal.rs
```

**Check Consistency**:
- Similar flow implementations
- Comparable transformer patterns
- Consistent error handling

---

## Output

The skill produces a **structured validation report**:

### 1. Summary Section

```yaml
validation_summary:
  connector_name: stripe
  overall_result: PASS_WITH_WARNINGS

  validation_checks:
    api_conformance: PASS
    authentication: PASS
    flow_implementation: WARN  # 1 warning
    amount_conversion: PASS
    status_mapping: WARN  # 1 warning
    ucs_compliance: PASS

  issues_found:
    critical: 0
    warnings: 2
    suggestions: 3
```

### 2. API Conformance Section

```yaml
api_conformance:
  status: PASS
  api_documentation_source: "https://stripe.com/docs/api"
  documentation_version: "2023-10-16"

  checks:
    - name: Endpoints
      status: PASS
      details: "All endpoints match API documentation"

    - name: Request Structure
      status: PASS
      details: "Request structures conform to API schemas"

    - name: Response Parsing
      status: PASS
      details: "Response parsing handles all documented fields"
```

### 3. Authentication Section

```yaml
authentication:
  status: PASS
  method_used: "HeaderKey"
  api_documented_method: "Bearer token in Authorization header"

  validation:
    - Correct auth type extraction: PASS
    - Auth header format: PASS
    - No hardcoded credentials: PASS
```

### 4. Flow Validation Section

```yaml
flows_validated:
  - flow: Authorize
    status: PASS
    issues: []

  - flow: Capture
    status: PASS
    issues: []

  - flow: Void
    status: PASS
    issues: []

  - flow: Refund
    status: WARN
    issues:
      - severity: WARNING
        category: Status Mapping
        issue: "Unknown refund status maps to Failure (should be Pending)"
        file: backend/connector-integration/src/connectors/stripe/transformers.rs
        line_number: 245              # NEW: Line in NEW file
        line_reference: "NEW_FILE"     # NEW: Explicit reference
        commit_sha: "abc123def456..."  # NEW: PR HEAD commit
        current_code: |
          _ => RefundStatus::Failure
        suggested_fix: |
          _ => RefundStatus::Pending  // Unknown → Pending per UCS convention
```

### 5. Amount Conversion Section

```yaml
amount_conversion:
  status: PASS
  converter_used: StringMinorUnit
  api_requirement: "String representation of minor units"
  validation: "Converter matches API requirement"
```

### 6. Status Mapping Section

```yaml
status_mapping:
  payment_status:
    status: PASS
    mappings:
      "succeeded": AttemptStatus::Charged  # Correct
      "pending": AttemptStatus::Pending  # Correct
      "failed": AttemptStatus::Failure  # Correct
      "unknown": AttemptStatus::Pending  # Correct

  refund_status:
    status: WARN
    issues:
      - Unknown status handling (see Flow Validation)
```

### 7. UCS Compliance Section

```yaml
ucs_compliance:
  status: PASS
  checks:
    - RouterDataV2 usage: PASS
    - ConnectorIntegrationV2 usage: PASS
    - MinorUnit for amounts: PASS
    - Macro usage: PASS
    - Reference ID handling: PASS
    - Error handling: PASS
```

### 8. Recommendations Section

```yaml
recommendations:
  - priority: MEDIUM
    category: Status Mapping
    suggestion: "Update unknown refund status to map to Pending"
    file: transformers.rs:245

  - priority: LOW
    category: Documentation
    suggestion: "Add doc comment explaining 3DS flow"
    file: stripe.rs:120

  - priority: LOW
    category: Testing
    suggestion: "Add test case for partial refund scenario"
```

---

## Integration with Other Skills

### Upstream Skills (Providers)

**1. pr-analysis**
- Provides connector name from file changes
- Identifies scope as connector_integration
- Supplies changed files list

**2. research-api-docs** (invoked if needed)
- Fetches latest API documentation
- Provides spec for validation
- Returns structured API information

### Downstream Skills (Consumers)

**1. github-review-publisher**
- Uses validation issues to create line-level comments
- Formats recommendations as review suggestions
- Maps issues to file paths and line numbers

### Parallel Skills

**code-quality-review** (runs in parallel)
- Generic code quality (this skill is connector-specific)
- Complement each other for complete review

---

## Reference Files

### 1. `ucs-validation-rules.md`
UCS architecture validation rules:
- Type system requirements
- Macro usage patterns
- Reference ID handling rules
- Status mapping conventions

### 2. `connector-patterns.md`
Common connector implementation patterns:
- Authentication patterns by type
- Flow implementation templates
- Transformer patterns
- Error handling patterns

---

## Error Handling

### Connector Not Found
```
Error: Could not identify connector from PR changes

Solution: Provide connector name explicitly or check file paths
```

### API Documentation Not Available
```
Warning: Could not fetch API documentation for {connector}

Proceeding with code-only validation (limited checks)
```

### Spec Parsing Failed
```
Error: Could not parse API specification

Solution: Verify spec format or provide alternative documentation URL
```

---

## Examples

### Example 1: Full Validation (PASS)

**Input**: "Validate Stripe connector in PR #238"

**Process**:
1. Identify connector: "stripe"
2. Read implementation files
3. Fetch API docs (existing spec)
4. Validate all aspects

**Output**:
```
✅ Connector Validation: Stripe (PASS)

**Summary**:
- API Conformance: ✅ PASS
- Authentication: ✅ PASS
- Flow Implementation: ✅ PASS (4 flows)
- Amount Conversion: ✅ PASS
- Status Mapping: ✅ PASS
- UCS Compliance: ✅ PASS

**Issues**: 0 critical, 0 warnings, 2 suggestions

**Recommendations**:
1. Add doc comment for 3DS flow handling (Low priority)
2. Consider adding test for partial capture scenario (Low priority)

**Overall**: Connector implementation is production-ready ✨
```

### Example 2: Validation with Warnings

**Input**: "Validate backend/connector-integration/src/connectors/newpay.rs"

**Output**:
```
⚠️  Connector Validation: NewPay (PASS WITH WARNINGS)

**Summary**:
- API Conformance: ✅ PASS
- Authentication: ✅ PASS
- Flow Implementation: ⚠️  WARN (1 issue)
- Amount Conversion: ✅ PASS
- Status Mapping: ⚠️  WARN (1 issue)
- UCS Compliance: ✅ PASS

**Warnings** (2):

1. **Status Mapping Issue** (Refund Flow)
   File: transformers.rs:245

   Issue: Unknown refund status maps to Failure

   Current:
   ```rust
   _ => RefundStatus::Failure
   ```

   Recommended:
   ```rust
   _ => RefundStatus::Pending  // Unknown → Pending per UCS convention
   ```

2. **Flow Implementation** (Capture)
   File: transformers.rs:180

   Issue: Partial capture handling not verified against API docs

   Recommendation: Verify API supports partial captures

**Suggestions** (1):
- Add integration test for each flow

**Overall**: Connector is functional but should address warnings before production
```

### Example 3: Critical Issues

**Input**: "Validate connector changes"

**Output**:
```
❌ Connector Validation: TestPay (FAIL)

**Summary**:
- API Conformance: ❌ FAIL (endpoint mismatch)
- Authentication: ✅ PASS
- Flow Implementation: ✅ PASS
- Amount Conversion: ❌ FAIL (wrong converter)
- Status Mapping: ✅ PASS
- UCS Compliance: ✅ PASS

**CRITICAL ISSUES** (2):

1. **API Conformance - Endpoint Mismatch**
   File: testpay.rs:95

   Issue: Authorize endpoint doesn't match API documentation

   Current:
   ```rust
   url = format!("{}/payment/authorize", base_url)
   ```

   API Documentation says:
   ```
   POST /v1/payments/create
   ```

   Fix:
   ```rust
   url = format!("{}/v1/payments/create", base_url)
   ```

2. **Amount Conversion - Wrong Converter**
   File: testpay.rs:45

   Issue: Using MinorUnit but API expects decimal string

   Current:
   ```rust
   amount_converters: [amount_converter: MinorUnit]
   ```

   API Documentation says:
   ```
   "amount": "10.50" (decimal string, e.g., $10.50)
   ```

   Fix:
   ```rust
   amount_converters: [amount_converter: DecimalAmount]
   ```

**Overall**: Critical issues must be fixed before merge ❌
```

---

## Performance Considerations

- **Spec Caching**: Reuse existing specs when available (fast path)
- **Parallel Checks**: Run independent validations in parallel
- **Selective Validation**: Focus on changed flows only (for incremental updates)

---

## Version History

- **1.0.0** (2025-12-09): Initial skill creation
  - API documentation validation
  - Authentication pattern checking
  - Flow implementation validation
  - Amount converter verification
  - Status mapping validation
  - UCS compliance checking
