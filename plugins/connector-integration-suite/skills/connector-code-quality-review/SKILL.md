---
name: connector-code-quality-review
description: |
  Review connector implementation code changes against strict UCS architecture standards, security best practices, and project conventions. Identifies critical issues related to connector integration. Auto-activates for: "review connector", "check connector quality", "validate connector".
allowed-tools: Read, Grep, Glob, Bash, Write
version: 1.0.0
---

# Code Quality Review Skill

## Overview

This skill performs comprehensive code quality reviews on changes, applying project-specific standards, security best practices, and industry conventions. It identifies issues categorized by severity (Critical, Warning, Suggestion) and provides actionable feedback with code examples.

## When to Use This Skill

This skill **auto-activates** when users request:

- "Review this code"
- "Check code quality"
- "Find security issues in this PR"
- "Validate best practices"
- "Review my changes"
- "Check for code smells"
- "Analyze code for bugs"

The skill can also be invoked as part of `/pr-review` workflow to review all changes in a pull request.

## Input Context

The skill expects one of the following:

1. **PR Number** (reviews all changes in PR):

   ```
   User: "Review code in PR #238"
   → Reviews all changed files
   ```

2. **Specific Files** (targeted review):

   ```
   User: "Review backend/connectors/stripe.rs"
   → Reviews only specified file
   ```

3. **Diff Content** (inline review):

   ```
   User: "Review this code: [paste diff]"
   → Reviews provided diff
   ```

4. **PR Analysis Output** (from pr-analysis skill):
   ```
   User: pr-analysis skill completed
   → Uses file list and scope from pr-analysis
   ```

## Process

### Step 1: Scope Identification

Determine what needs to be reviewed:

**From PR**:

- Get file list from PR diff
- Prioritize by file type (connectors > core > tests)
- Identify review focus areas

**From File Paths**:

- Read file content directly
- Apply relevant quality standards

**From Diff**:

- Extract changed lines only
- Review additions/modifications

---

### Step 1.5: Extract Line Numbers from NEW File

**CRITICAL**: Always extract line numbers from the **NEW file version** (PR HEAD commit) for GitHub API compatibility.

**Why This Matters**:

- GitHub API requires line numbers from the NEW file (after PR changes)
- Diff output line numbers are positional and don't match actual file lines
- Example: Line 22 in diff output might be line 5 in the actual file

**Process**:

#### A. Get PR HEAD Commit SHA

```bash
# Get the HEAD commit SHA of the PR branch
HEAD_SHA=$(gh pr view {pr-number} --repo {owner}/{repo} --json headRefOid -q '.headRefOid')

echo "PR HEAD commit: $HEAD_SHA"
```

#### B. Fetch File Content at HEAD Commit

For each file being reviewed:

```bash
# Fetch file content at the specific commit
gh api repos/{owner}/{repo}/contents/{file-path}?ref=$HEAD_SHA \
  --jq '.content' | base64 -d > /tmp/file_at_head.rs
```

**Important**: This gives you the file as it exists AFTER all PR changes, which is what GitHub API expects.

#### C. Find Line Numbers in NEW File

When identifying an issue, extract the line number from the NEW file:

```bash
# Find the exact line number using grep
LINE_NUM=$(grep -n "{pattern}" /tmp/file_at_head.rs | head -1 | cut -d: -f1)

# Extract the code at that line
CODE=$(sed -n "${LINE_NUM}p" /tmp/file_at_head.rs)
```

#### D. Validate Line Number

```bash
# Ensure line number is valid
FILE_LENGTH=$(wc -l < /tmp/file_at_head.rs)

if (( LINE_NUM > 0 && LINE_NUM <= FILE_LENGTH )); then
  echo "✅ Line $LINE_NUM is valid"
else
  echo "❌ Line $LINE_NUM is invalid (file has $FILE_LENGTH lines)"
  # Skip this issue
fi
```

**Reference**: See `.claude/skills/code-quality-review/references/line-number-extraction.md` for detailed extraction methods and edge cases.

**Key Rules**:

1. ✅ Always use NEW file (PR HEAD commit)
2. ✅ Include `line_reference: "NEW_FILE"` in output
3. ✅ Include `commit_sha` for validation
4. ❌ Never use diff positions (line numbers from diff output)
5. ❌ Never use local file line numbers (might differ from PR HEAD)

#### E. Anti-Patterns to AVOID

**NEVER** extract line numbers from these sources:

1. ❌ Diff output line numbers
   ```bash
   # WRONG - This gives diff position, not file line number
   gh pr diff 123 | grep -n "pattern"  # -n shows diff line, not file line!
   ```

2. ❌ Visual inspection of diff view
   - "I saw it on line 22 of the diff" ❌
   - Must fetch actual file and grep for line number ✅

3. ❌ `@@ ... @@` hunk positions
   - These are diff hunks, not file line numbers ❌
   - Always use NEW file line numbers ✅

---

### Step 1.6: Self-Validate Extracted Line Numbers

**Purpose**: Prevent line number errors BEFORE passing to github-review-publisher.

**Mandatory Process** for EVERY issue:

#### A. Checksum Validation

For each issue identified, validate the line number matches the code:

```bash
validate_issue_line() {
  local file="$1"
  local line_num="$2"
  local expected_code_snippet="$3"  # From issue context
  local head_sha="$4"

  # Fetch file content at PR HEAD
  gh api "repos/{owner}/{repo}/contents/$file?ref=$head_sha" \
    --jq '.content' | base64 -d > /tmp/validate_file.txt

  # Get actual code at the line
  local actual_code=$(sed -n "${line_num}p" /tmp/validate_file.txt)

  # Fuzzy match (ignoring whitespace)
  local norm_actual=$(echo "$actual_code" | tr -d '[:space:]')
  local norm_expected=$(echo "$expected_code_snippet" | tr -d '[:space:]')

  if [[ "$norm_actual" == *"$norm_expected"* ]]; then
    echo "✅ Line $line_num VALIDATED: matches expected code"
    return 0
  else
    echo "❌ Line $line_num FAILED VALIDATION"
    echo "   Expected: $expected_code_snippet"
    echo "   Actual:   $actual_code"
    return 1
  fi
}
```

#### B. Enhanced Output Format

Every issue MUST include validation field:

```yaml
- severity: CRITICAL
  file: backend/connectors/revolut.rs
  line_number: 617
  line_reference: "NEW_FILE"
  commit_sha: "abc123def456..."
  code_at_line: "let x = y.clone();"  # NEW: Checksum for validation
  issue: "Unnecessary clone operation"
  current_code: |
    let x = y.clone();
  suggested_fix: |
    let x = y;
```

#### C. Critical Checkpoint

**⚠️ CRITICAL CHECKPOINT**: Before proceeding to Step 2, verify that ALL issues in your list:
1. Have line numbers extracted from NEW file (not diff)
2. Include `code_at_line` validation field
3. Have been validated against actual file content

If any issue failed validation, DO NOT include it in the review. Report failed issues to the user with details on what was expected vs. actual.

---

### Step 2: Apply Quality Standards

Review against project-specific standards:

#### **Connector Integration Standards**

For files in `backend/connector-integration/src/connectors/`:

**Critical Checks** (Auto-fail):

1. ✅ Uses `RouterDataV2` (NOT `RouterData`)
2. ✅ Uses `ConnectorIntegrationV2` (NOT `ConnectorIntegration`)
3. ✅ Amount fields use `MinorUnit` (NOT `i64`, `f64`, `String`)
4. ✅ No hardcoded reference IDs
5. ✅ No mutation of reference IDs
6. ✅ No unsafe code blocks
7. ✅ Proper error handling (no `unwrap()`, `expect()`)
8. ✅ Authentication from `auth_type` field

**Warning Checks**:

1. Status mapping correctness
   - Unknown statuses → `Pending`
   - Refund statuses → `Charged` when appropriate
2. Enum usage for limited value sets (not strings)
3. Required field validation at correct layer
4. Proper macro usage (`create_all_prerequisites!`, `macro_connector_implementation!`)

**Suggestion Checks**:

1. Code duplication
2. Naming conventions
3. Documentation completeness
4. Test coverage

#### **Core Domain Standards**

For files in `backend/domain_types/`:

**Critical Checks**:

1. Type safety (no `Any`, minimal `Dynamic`)
2. Proper serialization/deserialization
3. Validation logic placement
4. No business logic in domain types

**Warning Checks**:

1. Missing field documentation
2. Overly complex types
3. Inconsistent naming

#### **Security Standards** (All Files)

**Critical Checks**:

1. ❌ No SQL injection vulnerabilities
2. ❌ No command injection
3. ❌ No XSS vulnerabilities
4. ❌ No hardcoded secrets/credentials
5. ❌ No unsafe deserialization
6. ❌ Proper input validation

**Warning Checks**:

1. Sensitive data logging
2. Error message information disclosure
3. Missing rate limiting (where applicable)

### Step 3: Code Analysis

**Static Analysis**:

```bash
# Run cargo clippy for Rust code
cargo clippy --all-targets -- -D warnings

# Check formatting
cargo fmt --check

# Run tests
cargo test --package <relevant-package>
```

**Pattern Matching**:

- Grep for anti-patterns (e.g., `unwrap()`, `expect()`, `TODO`, `FIXME`)
- Check for hardcoded values
- Identify duplicated code blocks

**Type Checking**:

- Verify correct type usage (especially `MinorUnit`, `RouterDataV2`)
- Check trait implementations
- Validate generic constraints

### Step 4: Categorize Issues

Group findings by severity:

**Critical Issues** (Score: -20 points each):

- Security vulnerabilities
- Type safety violations
- Hardcoded/mutated reference IDs
- Unsafe code
- Missing error handling

**Warnings** (Score: -5 points each):

- Incorrect status mapping
- Missing required fields validation
- Improper enum usage
- Code duplication
- Linter warnings

**Suggestions** (Score: -1 point each):

- Naming improvements
- Documentation additions
- Minor refactoring opportunities
- Code organization

### Step 5: Generate Quality Score

```
Score = 100 - (Critical × 20) - (Warnings × 5) - (Suggestions × 1)
```

**Score Interpretation**:

- **95-100**: Excellent ✨ - Auto-approve
- **90-94**: Good ✅ - Approve
- **80-89**: Fair ⚠️ - Request changes
- **60-79**: Poor ❌ - Block merge
- **0-59**: Critical 🚨 - Block merge

## Output

The skill produces a **structured quality review report**:

### 1. Summary Section

```yaml
review_summary:
  score: 92
  rating: "Good ✅"
  decision: "APPROVE"

  issue_counts:
    critical: 0
    warnings: 1
    suggestions: 3

  files_reviewed: 5
  lines_reviewed: 1247
```

### 2. Critical Issues Section

```yaml
critical_issues: [] # Empty if score >= 90
```

**If critical issues exist**:

```yaml
critical_issues:
  - severity: CRITICAL
    category: Type Safety
    file: backend/connector-integration/src/connectors/stripe.rs
    line_number: 45 # NEW: Line in NEW file (not diff position)
    line_reference: "NEW_FILE" # NEW: Explicit reference type
    commit_sha: "abc123def456..." # NEW: PR HEAD commit SHA
    issue: "Using RouterData instead of RouterDataV2"
    current_code: |
      use hyperswitch_domain_models::RouterData;
    suggested_fix: |
      use domain_types::router_data_v2::RouterDataV2;
    impact: "Breaks UCS architecture compatibility"
```

### 3. Warnings Section

```yaml
warnings:
  - severity: WARNING
    category: Code Quality
    file: backend/connector-integration/src/connectors/stripe/transformers.rs
    line_number: 78
    line_reference: "NEW_FILE"
    commit_sha: "abc123def456..."
    issue: "Status mapping may be incorrect"
    current_code: |
      status: match api_status {
          "unknown" => AttemptStatus::Failure,
          ...
      }
    suggested_fix: |
      status: match api_status {
          "unknown" => AttemptStatus::Pending,
          ...
      }
    reasoning: "Unknown statuses should map to Pending, not Failure"
```

### 4. Suggestions Section

```yaml
suggestions:
  - severity: SUGGESTION
    category: Documentation
    file: backend/connector-integration/src/connectors/stripe.rs
    line_number: 25
    line_reference: "NEW_FILE"
    commit_sha: "abc123def456..."
    issue: "Missing doc comment for public struct"
    suggested_fix: |
      /// Stripe connector implementation for payment processing
      pub struct Stripe<T> { ... }
```

### 5. Detailed Analysis

```yaml
detailed_analysis:
  security_check:
    status: PASS
    issues_found: 0
    notes: "No security vulnerabilities detected"

  type_safety:
    status: PASS
    issues_found: 0
    notes: "All types correctly used"

  error_handling:
    status: PASS
    issues_found: 0
    notes: "Proper error propagation with ? operator"

  best_practices:
    status: WARN
    issues_found: 1
    notes: "Minor naming convention deviation"

  test_coverage:
    status: PASS
    estimated_coverage: "85%"
    notes: "Core flows have test coverage"
```

## Integration with Other Skills

### Upstream Skills (Providers)

**1. pr-analysis**

- Provides file list and scope
- Supplies diff content
- Identifies change categories

### Downstream Skills (Consumers)

**1. github-review-publisher**

- Uses categorized issues to create review comments
- Maps issues to line-level comments
- Formats with severity indicators

**2. connector-integration-validator** (parallel)

- Both skills run in parallel for connector PRs
- code-quality-review: Generic code quality
- connector-integration-validator: Connector-specific validation

### Standalone Usage

Can be used independently for:

- Pre-commit code review
- Local quality checks before pushing
- Reviewing code snippets in chat
- Quick quality assessment without full PR context

## Reference Files

### 1. `quality-standards.md`

Project-specific quality standards:

- UCS architecture requirements
- Connector integration rules
- Domain type conventions
- Error handling patterns
- Testing requirements

### 2. `security-patterns.md`

Security validation rules:

- OWASP Top 10 checks
- Rust-specific security issues
- Payment data handling
- Secrets management
- Input validation requirements

### 3. `best-practices.md`

Project conventions:

- Naming conventions
- Code organization
- Documentation standards
- Macro usage patterns
- Module structure

## Error Handling

### File Read Failure

```
Error: Could not read file: {path}

Possible causes:
- File doesn't exist
- Permission denied
- File was deleted in PR

Solution: Verify file path is correct
```

### Clippy Failures

```
Error: cargo clippy failed with errors

Output: {clippy_output}

Solution: Fix clippy warnings before review
```

### Parse Errors

```
Error: Could not parse diff for file: {path}

Solution: Verify diff format is valid unified diff
```

## Examples

### Example 1: Excellent Code Review

**Input**: "Review backend/connector-integration/src/connectors/stripe.rs"

**Process**:

1. Read file content
2. Identify as connector integration
3. Apply connector standards
4. Run clippy
5. Check for anti-patterns

**Output**:

```
✨ Code Quality Review: Excellent (Score: 98/100)

**Files Reviewed**: 1
**Score**: 98/100

**Issue Summary**:
- Critical: 0
- Warnings: 0
- Suggestions: 2

**Decision**: ✅ APPROVE

---

**Suggestions**:

1. **Documentation** (Line 45)
   Consider adding doc comment for `AuthorizeRequest` struct

2. **Code Organization** (Line 120)
   Minor: Group related imports together

---

**Analysis**:
✅ Security: PASS
✅ Type Safety: PASS
✅ Error Handling: PASS
✅ Best Practices: PASS
✅ Test Coverage: PASS

**Recommendation**: Code meets all quality standards. Ready to merge.
```

### Example 2: Critical Issues Found

**Input**: "Review PR #238"

**Output**:

````
🚨 Code Quality Review: Poor (Score: 55/100)

**Files Reviewed**: 3
**Score**: 55/100

**Issue Summary**:
- Critical: 2 ❌
- Warnings: 3 ⚠️
- Suggestions: 5

**Decision**: ❌ BLOCK MERGE

---

**CRITICAL ISSUES** (Must Fix):

1. **Type Safety Violation**
   File: `backend/connector-integration/src/connectors/newpay.rs`
   Line: 25

   Issue: Using deprecated RouterData instead of RouterDataV2

   Current:
   ```rust
   use hyperswitch_domain_models::RouterData;
````

Fix:

```rust
use domain_types::router_data_v2::RouterDataV2;
```

Impact: Breaks UCS architecture compatibility

2. **Security Risk**
   File: `backend/connector-integration/src/connectors/newpay/transformers.rs`
   Line: 67

   Issue: Hardcoded reference ID

   Current:

   ```rust
   reference_id: "TEST123".to_string()
   ```

   Fix:

   ```rust
   reference_id: router_data.connector_request_reference_id.clone()
   ```

   Impact: Payment tracking failure in production

---

**Recommendation**: Fix critical issues before re-review.

```

### Example 3: Targeted File Review

**Input**: "Check security in backend/api/src/auth.rs"

**Output**:
```

🔒 Security Review: auth.rs

**Score**: 90/100 (Good ✅)

**Security Checks**:
✅ No SQL injection vulnerabilities
✅ No command injection
✅ No XSS vulnerabilities
✅ No hardcoded credentials
✅ Proper input validation

**Warnings** (1):

1. **Information Disclosure**
   Line: 145

   Issue: Error message may expose sensitive information

   Current:

   ```rust
   Err(format!("Authentication failed for user {}", user_id))
   ```

   Fix:

   ```rust
   Err("Authentication failed".to_string())  // Don't leak user_id
   ```

**Recommendation**: Address warning to improve security posture.

```

## Performance Considerations

- **Large Files**: For files >2000 lines, focus on changed regions only
- **Clippy Runs**: Cache clippy results for unchanged files
- **Pattern Matching**: Use efficient grep patterns with context limits
- **Parallel Review**: Review independent files in parallel

## Integration with Existing Systems

### With code-change-reviewer Agent

This skill can work alongside or eventually replace the existing `code-change-reviewer` agent:

**Current State**: Both can coexist
**Migration Path**: Gradually shift to skill-based approach
**Compatibility**: Shares same quality standards

### With CI/CD

This skill's checks complement (not replace) CI/CD:
- **CI/CD**: Automated tests, builds, deployments
- **This Skill**: Code quality, architecture compliance, security review

## Version History

- **1.0.0** (2025-12-09): Initial skill creation
  - UCS architecture standards enforcement
  - Security vulnerability detection
  - Quality scoring system
  - Actionable feedback generation
```
