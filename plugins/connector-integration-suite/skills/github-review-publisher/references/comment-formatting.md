# Comment Formatting Reference

**Version**: 1.0.0
**Purpose**: Guidelines for formatting GitHub PR review comments

---

## Comment Structure

### Standard Format

```markdown
{severity_emoji} **{severity}** - {category}

{issue_description}

**Current**:
```{language}
{current_code}
```

**Suggested Fix**:
```{language}
{suggested_fix}
```

{additional_context}
```

---

## Severity Indicators

### Emoji and Labels

| Severity | Emoji | Label | Usage |
|----------|-------|-------|-------|
| Critical | 🔴 | Critical | Security vulnerabilities, type safety violations, breaking changes |
| Warning | 🟡 | Important | Code quality issues, incorrect patterns, missing validations |
| Suggestion | 🟢 | Suggestion | Minor improvements, documentation, code style |

### Examples

**Critical**:
```markdown
🔴 **Critical** - Security

SQL injection vulnerability detected. Never concatenate user input into SQL queries.
```

**Warning**:
```markdown
🟡 **Important** - Code Quality

Status mapping may be incorrect. Unknown statuses should map to Pending, not Failure.
```

**Suggestion**:
```markdown
🟢 **Suggestion** - Documentation

Consider adding a doc comment explaining the purpose of this function.
```

---

## Categories

### Common Categories

| Category | Description | Example Issues |
|----------|-------------|----------------|
| Type Safety | Type system violations | Using RouterData instead of RouterDataV2 |
| Security | Security vulnerabilities | SQL injection, XSS, hardcoded secrets |
| Error Handling | Improper error handling | Using unwrap/expect instead of ? |
| Code Quality | Code quality issues | Code duplication, complex logic |
| Performance | Performance concerns | Inefficient algorithms, unnecessary allocations |
| Best Practices | Project conventions | Naming, organization, patterns |
| Documentation | Missing or unclear docs | No doc comments, unclear explanations |
| UCS Compliance | UCS architecture violations | Wrong macro usage, missing prerequisites |
| API Conformance | Doesn't match API docs | Wrong endpoint, incorrect request structure |

---

## Code Block Formatting

### Single-Line Code

**Use inline code** for short snippets:

```markdown
Change `unwrap()` to use the `?` operator for proper error handling.
```

**Rendered**: Change `unwrap()` to use the `?` operator for proper error handling.

---

### Multi-Line Code Blocks

**Always specify language** for syntax highlighting:

````markdown
**Current**:
```rust
let data = fetch().unwrap();
```

**Suggested Fix**:
```rust
let data = fetch()?;
```
````

**Supported Languages**:
- `rust` - Rust code
- `json` - JSON data
- `yaml` - YAML configuration
- `bash` - Shell commands
- `toml` - Cargo.toml, config files

---

### Side-by-Side Comparison

For changes, show before and after:

````markdown
**Current**:
```rust
use hyperswitch_domain_models::RouterData;
```

**Suggested Fix**:
```rust
use domain_types::router_data_v2::RouterDataV2;
```
````

---

### Code with Context

Include surrounding code when helpful:

````markdown
**Current**:
```rust
fn process() {
    let data = fetch().unwrap();  // ← This line
    transform(data)
}
```

**Suggested Fix**:
```rust
fn process() -> Result<(), Error> {
    let data = fetch()?;  // ← Use ? for error propagation
    transform(data)
}
```
````

---

## Issue Description Patterns

### Be Specific

**Bad** ❌:
```markdown
This is wrong.
```

**Good** ✅:
```markdown
Using deprecated RouterData instead of RouterDataV2 breaks UCS architecture compatibility.
```

---

### Explain the Impact

**Pattern**:
```markdown
{What's wrong} + {Why it matters} + {What will happen}
```

**Example**:
```markdown
Hardcoded reference ID detected. Reference IDs must come from router_data to ensure proper payment tracking. Using hardcoded values will cause payment failures in production.
```

---

### Provide Context

**Good examples include**:
- Link to documentation
- Reference to similar code
- Explanation of the correct pattern

```markdown
Status mapping incorrect. According to UCS conventions (see .claude/knowledge/patterns/status-mapping.md), unknown statuses should map to `Pending`, not `Failure`, because they represent temporary states.
```

---

## Suggested Fix Patterns

### Show the Exact Fix

**Bad** ❌:
```markdown
Use the correct type.
```

**Good** ✅:
````markdown
**Suggested Fix**:
```rust
use domain_types::router_data_v2::RouterDataV2;
```
````

---

### Multiple Options

If multiple approaches are valid:

````markdown
**Suggested Fix (Option 1)**: Use error propagation
```rust
let data = fetch()?;
```

**Suggested Fix (Option 2)**: Handle error explicitly
```rust
let data = match fetch() {
    Ok(d) => d,
    Err(e) => return Err(Error::FetchFailed(e)),
};
```
````

---

### Step-by-Step Fixes

For complex fixes:

````markdown
**Suggested Fix**:

1. Update the import:
```rust
use domain_types::router_data_v2::RouterDataV2;
```

2. Update the type signature:
```rust
impl ConnectorIntegrationV2<Authorize, ...> for Stripe<Authorize>
```

3. Update the function parameter:
```rust
fn build_request(router_data: &RouterDataV2<...>) -> Result<Request, Error>
```
````

---

## Additional Context Patterns

### Link to Documentation

```markdown
**Reference**: See [UCS Architecture Guide](.claude/knowledge/ucs-architecture.md) for details on RouterDataV2 usage.
```

---

### Example from Existing Code

```markdown
**Example**: See how Stripe connector handles this:
```rust
// backend/connector-integration/src/connectors/stripe.rs:45
reference_id: router_data.connector_request_reference_id.clone()
```
```

---

### Impact Statement

```markdown
**Impact**: This prevents the connector from working with the UCS architecture and will cause compilation errors.
```

```markdown
**Security Impact**: This vulnerability could allow attackers to execute arbitrary SQL commands, potentially exposing sensitive payment data.
```

---

## Tone and Style

### Be Professional

**Bad** ❌:
```markdown
This is terrible code. Who wrote this?
```

**Good** ✅:
```markdown
This implementation has a security vulnerability that should be addressed.
```

---

### Be Helpful, Not Prescriptive

**Bad** ❌:
```markdown
You MUST change this immediately!
```

**Good** ✅:
```markdown
Consider using the ? operator for more idiomatic error handling.
```

---

### Use Active Voice

**Bad** ❌:
```markdown
The ? operator should be used here.
```

**Good** ✅:
```markdown
Use the ? operator for error propagation.
```

---

## Complete Comment Examples

### Example 1: Critical Type Safety Issue

````markdown
🔴 **Critical** - Type Safety

Using deprecated `RouterData` instead of `RouterDataV2` breaks UCS architecture compatibility.

**Current**:
```rust
use hyperswitch_domain_models::RouterData;
```

**Suggested Fix**:
```rust
use domain_types::router_data_v2::RouterDataV2;
```

**Impact**: This prevents the connector from integrating with the UCS architecture. All connectors must use RouterDataV2 for compatibility.

**Reference**: See `.claude/knowledge/ucs-architecture.md` for migration guide.
````

---

### Example 2: Security Vulnerability

````markdown
🔴 **Critical** - Security

Hardcoded API credentials detected. Credentials must never be committed to source code.

**Current**:
```rust
const API_KEY: &str = "sk_live_abc123...";
```

**Suggested Fix**:
```rust
// Extract from connector_auth_type
let api_key = match &router_data.connector_auth_type {
    ConnectorAuthType::HeaderKey { api_key } => api_key,
    _ => return Err(errors::ConnectorError::InvalidAuthType)?,
};
```

**Security Impact**: Hardcoded credentials in source code can be exposed if the repository is compromised, leading to unauthorized access to payment systems.
````

---

### Example 3: Code Quality Warning

````markdown
🟡 **Important** - Code Quality

Status mapping may be incorrect. Unknown statuses should map to `Pending` (not `Failure`) per UCS conventions.

**Current**:
```rust
_ => AttemptStatus::Failure
```

**Suggested Fix**:
```rust
_ => AttemptStatus::Pending  // Unknown statuses are temporary states
```

**Rationale**: Unknown statuses represent temporary or unexpected states, not definitive failures. Mapping them to `Pending` allows for proper status resolution.
````

---

### Example 4: Documentation Suggestion

````markdown
🟢 **Suggestion** - Documentation

Consider adding a doc comment explaining the 3DS authentication flow.

**Suggested Addition**:
```rust
/// Handles 3D Secure authentication flow
///
/// If the payment requires 3DS authentication, this function
/// returns `AuthenticationPending` status with a redirect URL
/// for the cardholder to complete authentication.
///
/// # Returns
/// - `Charged` if payment succeeds without 3DS
/// - `AuthenticationPending` if 3DS required
/// - `Failure` if authentication fails
pub fn handle_3ds_flow(...) -> Result<...> {
```
````

---

### Example 5: Multi-Line Issue

````markdown
🟡 **Important** - Error Handling

This entire function lacks proper error handling. Using `unwrap()` will cause panics in production.

**Current** (lines 45-50):
```rust
fn process_payment(data: PaymentData) -> Payment {
    let validated = validate(data).unwrap();
    let authorized = authorize(validated).unwrap();
    let captured = capture(authorized).unwrap();
    record(captured).unwrap()
}
```

**Suggested Fix**:
```rust
fn process_payment(data: PaymentData) -> Result<Payment, Error> {
    let validated = validate(data)?;
    let authorized = authorize(validated)?;
    let captured = capture(authorized)?;
    record(captured)
}
```

**Impact**: Current implementation will crash the application if any step fails. Proper error handling ensures graceful failure recovery.
````

---

## Formatting Checklist

Before publishing comments:

- [ ] Severity emoji present (🔴/🟡/🟢)
- [ ] Category specified
- [ ] Issue clearly described
- [ ] Impact/rationale explained
- [ ] Current code shown (if applicable)
- [ ] Suggested fix provided with code blocks
- [ ] Language specified for code blocks
- [ ] Professional tone used
- [ ] No personal attacks
- [ ] Actionable feedback
- [ ] Additional context provided where helpful

---

## Version History

- **1.0.0** (2025-12-09): Initial formatting guidelines
  - Comment structure templates
  - Severity indicators
  - Category definitions
  - Code block formatting
  - Complete examples
  - Tone and style guidelines
