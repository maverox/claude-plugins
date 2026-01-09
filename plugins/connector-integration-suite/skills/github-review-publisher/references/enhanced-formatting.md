# Enhanced Comment Formatting Guide

This guide documents best practices for formatting GitHub PR review comments created by the `github-review-publisher` skill.

## Visual Hierarchy Principles

### 1. Header Structure

Use markdown headers to create clear visual hierarchy:

```markdown
## 🔴 CRITICAL: Category Name          ← Level 2 header with emoji
### Current Implementation             ← Level 3 subsection
### Suggested Fix                      ← Level 3 subsection
### Why This Matters                   ← Level 3 subsection
### Impact Assessment                  ← Level 3 subsection
```

**Why**: GitHub renders these with distinct sizes and styling, making comments scannable.

### 2. Severity Indicators

Always use emoji + capitalized severity:

| Severity | Emoji + Format | Usage |
|----------|---|---|
| Critical | `## 🔴 CRITICAL:` | Blocks merge, must fix |
| Important | `## 🟡 IMPORTANT:` | Should fix before merge |
| Suggestion | `## 🟢 SUGGESTION:` | Nice to have |

**Why**: Visual scanning + platform accessibility (emoji + text)

### 3. Status Indicators

Use status symbols consistently:

- ❌ = Problem, wrong, broken
- ✅ = Solution, correct, good
- ⚠️ = Warning, caution, important
- 💡 = Idea, suggestion, thought

**Placement**: Directly after code blocks and statements

## Code Block Enhancement

### 1. Language Specification

Always specify the language for syntax highlighting:

```rust
// ✅ CORRECT
fn main() { }
```

```
// ❌ WRONG - No language specified
fn main() { }
```

**Supported languages**:
- `rust` - Rust code
- `yaml` - Configuration files
- `bash` / `sh` - Shell scripts
- `json` - JSON data
- `sql` - SQL queries
- `javascript` / `typescript` - JavaScript/TypeScript
- `python` - Python code

### 2. Inline Annotations

Add comments in code blocks to explain the problem/solution:

```rust
// ❌ AVOID: Unnecessary clone creates overhead
let status = code.clone().into();

// ✅ PREFER: Direct consumption is more efficient
let status = code.into();
```

### 3. Before/After Formatting

For side-by-side comparisons, use clear labels:

**Current (Wrong)**:
```rust
match status {
    "success" => Ok(Paid),
    _ => Ok(Failure),  // ❌ Wrong default
}
```

**Suggested Fix**:
```rust
match status {
    "success" => Ok(Paid),
    _ => Ok(Pending),  // ✅ Correct default
}
```

## Impact Assessment Template

Every comment must include an impact assessment with consistent fields:

### For Critical Issues

```markdown
### Impact Assessment
- **Severity**: Critical (P0 - Blocks Merge)
- **Failure Mode**: {Describe what breaks and when}
- **Effort to Fix**: {Low|Medium|High}
- **Testing Required**: {Which tests to run}
```

**Example**:
```markdown
### Impact Assessment
- **Severity**: Critical (P0 - Blocks Merge)
- **Failure Mode**: Compilation fails in UCS builds due to missing type
- **Effort to Fix**: Low (single line import change)
- **Testing Required**: Full connector integration tests (authorize, capture, refund)
```

### For Important Issues

```markdown
### Impact Assessment
- **Severity**: Important (P1 - Should Fix)
- **Code Quality Impact**: {Impact on maintainability|performance|security}
- **Effort to Fix**: {Low|Medium|High}
- **Testing Required**: {Which tests to run}
```

**Example**:
```markdown
### Impact Assessment
- **Severity**: Important (P1 - Should Fix)
- **Code Quality Impact**: Correctness of payment status reporting
- **Effort to Fix**: Low (one line change)
- **Testing Required**: Unit tests for status mapping edge cases
```

### For Suggestions

```markdown
### Impact Assessment
- **Severity**: Suggestion (P2 - Nice to Have)
- **Benefit**: {Description of improvement}
- **Effort to Fix**: {Low|Medium|High}
```

**Example**:
```markdown
### Impact Assessment
- **Severity**: Suggestion (P2 - Nice to Have)
- **Benefit**: Improved code readability and testability through better separation of concerns
- **Effort to Fix**: Low (straightforward refactoring)
```

## Complete Examples

### Example 1: Critical Type Safety Issue

```markdown
## 🔴 CRITICAL: Type Safety Violation

**Issue**: Using deprecated `RouterData` instead of `RouterDataV2`

### Current Implementation
```rust
use hyperswitch_domain_models::RouterData;

fn process_payment(data: RouterData) -> Result<()> {
    // Process payment with legacy type
    let amount = data.request.amount;  // ❌ Missing fields in legacy type
    Ok(())
}
```
❌ This breaks UCS architecture compatibility

### Suggested Fix
```rust
use domain_types::router_data_v2::RouterDataV2;

fn process_payment(data: RouterDataV2) -> Result<()> {
    // Process payment with correct type
    let amount = data.request.amount_in_minor_units;  // ✅ Proper field
    Ok(())
}
```
✅ Correct import for UCS architecture

### Why This Matters

The UCS (Unified Commerce Stack) architecture requires `RouterDataV2` for proper connector integration. The legacy `RouterData` type:
- Lacks critical fields for amount handling
- Missing currency information
- No support for 3D Secure authentication
- Will cause compilation errors in UCS builds

All new connectors must use V2 types for compatibility.

### Impact Assessment
- **Severity**: Critical (P0 - Blocks Merge)
- **Failure Mode**: Compilation failure when building with UCS
- **Effort to Fix**: Low (import and type references change)
- **Testing Required**: Full connector flow testing (authorize, capture, void, refund)

---
*Auto-generated by connector-code-quality-review | Line 42 | Commit abc123d4*
```

### Example 2: Important Status Mapping Issue

```markdown
## 🟡 IMPORTANT: Status Mapping Correctness

**Issue**: Unmapped refund statuses incorrectly default to `Failure`

### Current Implementation
```rust
let refund_status = match vendor_response.status.as_str() {
    "refunded" => RefundStatus::Charged,
    "failed" => RefundStatus::Failure,
    "pending" => RefundStatus::Pending,
    _ => RefundStatus::Failure,  // ❌ Wrong: unknown statuses marked failed
};
```
⚠️ Will report pending refunds as failed, causing settlement errors

### Suggested Fix
```rust
let refund_status = match vendor_response.status.as_str() {
    "refunded" => RefundStatus::Charged,
    "failed" => RefundStatus::Failure,
    "pending" => RefundStatus::Pending,
    _ => RefundStatus::Pending,  // ✅ Correct: unknown statuses as pending
};
```
✅ Proper handling of unknown/in-progress statuses

### Why This Matters

Refund status mapping is critical for accurate settlement reconciliation:
- Unknown/unmapped statuses likely represent in-progress refunds
- Marking them as `Failure` causes incorrect settlement reporting
- This leads to revenue reconciliation errors and merchant disputes

The correct approach:
1. Map known failure cases explicitly
2. Default unknown cases to `Pending` (safest assumption)
3. Log unknown statuses for monitoring

### Impact Assessment
- **Severity**: Important (P1 - Should Fix)
- **Code Quality Impact**: Correctness of refund status reporting in settlement
- **Effort to Fix**: Low (single line change)
- **Testing Required**: Unit tests for all status mapping edge cases

---
*Auto-generated by connector-integration-validator | Line 156 | Commit def456g7*
```

### Example 3: Suggestion for Code Organization

```markdown
## 🟢 SUGGESTION: Extract Request Builder

**Issue**: Request building logic mixed with validation logic

### Current Implementation
```rust
fn create_payment_request(config: &Config) -> Result<Request> {
    // 30 lines of configuration and setup
    let mut req = PaymentRequest::new();
    req.merchant_id = config.merchant_id;
    req.api_key = config.api_key;

    // 20 lines of validation logic
    if req.amount <= 0 {
        return Err("Invalid amount");
    }

    // 15 lines of transformation logic
    Ok(req.build())
}
```
💡 Multiple concerns mixed in single function

### Suggested Fix
```rust
fn build_payment_request(config: &Config) -> PaymentRequest {
    // 30 lines of configuration and setup
    let mut req = PaymentRequest::new();
    req.merchant_id = config.merchant_id;
    req.api_key = config.api_key;
    req
}

fn validate_payment_request(req: &PaymentRequest) -> Result<()> {
    // 20 lines of validation logic
    if req.amount <= 0 {
        return Err("Invalid amount");
    }
    Ok(())
}

fn create_payment_request(config: &Config) -> Result<Request> {
    let req = build_payment_request(config);
    validate_payment_request(&req)?;
    Ok(req.build())
}
```
✅ Clear separation of concerns

### Why This Matters

Separating concerns improves:
- **Testability**: Can test building and validation independently
- **Readability**: Each function has a single, clear purpose
- **Reusability**: Can use `build_payment_request` without validation
- **Maintainability**: Easier to locate and modify specific logic

This is especially important in payment processing where validation logic is critical.

### Impact Assessment
- **Severity**: Suggestion (P2 - Nice to Have)
- **Benefit**: Improved code readability, testability, and reusability
- **Effort to Fix**: Low (straightforward refactoring)

---
*Auto-generated by connector-code-quality-review | Line 78 | Commit ghi789j0*
```

## Accessibility Guidelines

### 1. Don't Rely Solely on Emoji

Always pair emoji with text:

```markdown
❌ WRONG: 🔴  # Users relying on screen readers won't understand

✅ CORRECT: 🔴 CRITICAL  # Clear even without emoji
```

### 2. Use Semantic HTML When Possible

Prefer markdown over raw HTML for better rendering consistency:

```markdown
✅ CORRECT:
### Suggested Fix

❌ WRONG:
<h3>Suggested Fix</h3>
```

### 3. Adequate Color Contrast

GitHub comments use good contrast, but avoid relying on color alone for meaning. Always use text + emoji.

## Mobile View Considerations

### 1. Code Block Width

Keep code examples reasonably sized for mobile devices:

```rust
// ✅ GOOD: Fits on mobile
let status = code.into();

// ❌ POOR: Doesn't fit on mobile
let very_long_variable_name = some_function_call_with_many_parameters().into().do_something_else();
```

### 2. Table Formatting

Simple tables render better on mobile:

```markdown
✅ GOOD:
- **Severity**: Critical
- **Effort**: Low

❌ POOR:
| Category | Value | Additional Info | Notes |
|----------|-------|-----------------|-------|
```

### 3. Nested Structure

Avoid deep nesting, keep headers at 2-3 levels maximum.

## Performance Guidelines

### 1. Comment Length

GitHub handles long comments well, but consider:
- Keep individual comments under 2000 characters when possible
- Break very long reviews into multiple comments if > 5 issues
- Use reference files for very detailed documentation

### 2. Code Block Size

Limit code examples to ~15 lines:

```rust
// ✅ GOOD: Concise, focused example
fn process(data: RouterDataV2) {
    let amount = data.request.amount;
    api.call(amount).await
}

// ❌ POOR: Too large, loses focus
fn process(data: RouterDataV2) {
    let amount = data.request.amount;
    let currency = data.request.currency;
    let merchant = data.merchant_id;
    // ... 20 more lines
}
```

## Emoji Reference

**Severity**:
- 🔴 = Critical/Error (P0)
- 🟡 = Important/Warning (P1)
- 🟢 = Suggestion/Good (P2)

**Status**:
- ✅ = Good, correct, solution
- ❌ = Bad, wrong, problem
- ⚠️ = Warning, caution
- 💡 = Idea, thought, suggestion
- 🔗 = Link, reference
- 📝 = Note, documentation
- 🧪 = Testing
- 📊 = Metrics, statistics

## Common Mistakes to Avoid

1. **Missing language in code blocks** - Always specify rust, bash, yaml, etc.
2. **No impact assessment** - Every issue needs severity and effort context
3. **Vague "why this matters"** - Explain real impact on functionality, not just style
4. **Too much code** - Keep examples focused and concise
5. **Inconsistent formatting** - Follow the template for all issues
6. **Unclear suggested fix** - Show exact change needed, not general direction
7. **No metadata footer** - Include skill name, line, and commit hash

## Summary

Good comment formatting:
1. Uses clear visual hierarchy (headers, emoji, text)
2. Shows before/after code clearly
3. Explains impact and failure modes
4. Provides specific, actionable fixes
5. Works on mobile and with screen readers
6. Is consistent across all comments
