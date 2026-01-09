---
name: code-quality-review
description: |
  Comprehensive code quality review applying baseline standards (security, error handling, code style, performance) plus project-specific rules from Claude rules. Auto-activates for: "review code", "check code quality", "find issues", "code review".
allowed-tools: Bash, Read, Grep, Glob, Write
version: 1.0.0
---

# Code Quality Review Skill

## Overview

This skill performs comprehensive code quality reviews by applying:
1. **Baseline Standards** - Built-in checks for security, error handling, code style, and performance
2. **Project Rules** - Dynamic rules from `.claude/rules/*.md` and `.claude/CLAUDE.md`
3. **Configurable Scoring** - Optional 100-point scoring system

This is a **generic skill** that works with any language and any project structure.

## When to Use This Skill

This skill **auto-activates** when users request:
- "Review this code"
- "Check code quality"
- "Find security issues"
- "Analyze code for bugs"
- "Review my changes"
- "Check for code smells"

The skill can also be invoked as part of `/pr-review` workflow.

## Input Context

The skill expects:

1. **From pr-analysis skill** (recommended):
   ```yaml
   pr_metadata:
     head_sha: abc123...  # CRITICAL for line extraction
   files_changed:
     source: [file1.ts, file2.ts]
   diff_content: |
     ...full diff...
   ```

2. **Direct file paths**:
   ```
   User: "Review src/api/handler.ts"
   ```

3. **Git diff**:
   ```
   User: "Review my staged changes"
   -> Uses: git diff --staged
   ```

## Baseline Standards

### 1. Security (OWASP Top 10)

**Critical Issues** (auto-block merge):

| Check | Pattern | Languages |
|-------|---------|-----------|
| SQL Injection | String concatenation in queries | All |
| Command Injection | `exec()`, `system()`, `eval()` with user input | All |
| XSS | Unescaped user input in HTML | JS/TS, Python, Ruby |
| Hardcoded Secrets | API keys, passwords in code | All |
| Insecure Deserialization | `pickle.loads()`, `eval()` on untrusted data | Python, JS |
| Path Traversal | User input in file paths without validation | All |
| SSRF | User-controlled URLs in requests | All |

**Reference**: `references/security-patterns.md`

### 2. Error Handling

**Warning Issues** (should fix):

| Check | Pattern | Languages |
|-------|---------|-----------|
| Empty Catch | `catch (e) { }` | JS/TS, Java, Python |
| Swallowed Exceptions | Catch without re-throw or logging | All |
| Panic/Crash | `unwrap()`, `expect()` without context | Rust |
| Generic Errors | Throwing generic `Error` instead of specific types | All |
| Missing Error Context | Errors without stack trace or context | All |

**Reference**: `references/error-handling-patterns.md`

### 3. Code Style

**Suggestion Issues** (nice to have):

| Check | Pattern | Languages |
|-------|---------|-----------|
| Dead Code | Unreachable code, unused variables | All |
| Unused Imports | Imported but never used | All |
| Inconsistent Naming | Mixing camelCase/snake_case | All |
| Missing Documentation | Public APIs without docs | All |
| Magic Numbers | Hardcoded values without constants | All |
| Long Functions | Functions >50 lines | All |
| Deep Nesting | >3 levels of nesting | All |

**Reference**: `references/code-style-guide.md`

### 4. Performance

**Warning Issues** (should fix):

| Check | Pattern | Languages |
|-------|---------|-----------|
| N+1 Queries | Loop with database call inside | All |
| Unnecessary Clones | `.clone()` when borrow would work | Rust |
| Blocking in Async | Sync I/O in async context | JS/TS, Python, Rust |
| Memory Leaks | Event listeners not removed | JS/TS |
| Inefficient Loops | Creating objects in loops unnecessarily | All |
| Missing Indexes | Queries on non-indexed fields | SQL |

**Reference**: `references/performance-patterns.md`

## Process

### Step 1: Gather Context

```bash
# If PR context provided (from pr-analysis)
HEAD_SHA={from pr-analysis}
FILES={from files_changed}
DIFF={from diff_content}

# If direct file provided
git diff HEAD -- {file}

# If staged changes
git diff --staged
```

### Step 2: Load Project Rules

**Auto-detect project-specific rules:**

```bash
# Check for Claude rules directory
if [ -d ".claude/rules" ]; then
  for rule_file in .claude/rules/*.md; do
    # Parse rule file for patterns
    parse_rule "$rule_file"
  done
fi

# Check for project CLAUDE.md
if [ -f ".claude/CLAUDE.md" ]; then
  parse_project_instructions ".claude/CLAUDE.md"
fi
```

**Rule Parsing**:
- Extract patterns, anti-patterns, requirements
- Project rules **override** baseline when conflicting
- Rules are reported in output

### Step 3: Identify Files to Review

Based on input, determine scope:

```yaml
review_scope:
  files:
    - src/api/handler.ts
    - src/utils/crypto.ts
    - tests/handler.test.ts
  languages:
    - typescript
  focus_areas: [security, error_handling]  # if --focus specified
```

### Step 4: Extract Line Numbers (CRITICAL)

**IMPORTANT**: Always extract line numbers from the **NEW file version** (PR HEAD commit).

```bash
# Get PR HEAD commit SHA
HEAD_SHA=$(gh pr view {pr} --json headRefOid -q '.headRefOid')

# Fetch file content at HEAD commit
gh api repos/{owner}/{repo}/contents/{path}?ref=$HEAD_SHA | jq -r '.content' | base64 -d > /tmp/file_content

# Find line number for specific pattern
grep -n "pattern" /tmp/file_content | head -1 | cut -d: -f1
```

**Reference**: `references/line-number-extraction.md`

### Step 5: Apply Quality Standards

For each file, run baseline checks:

```
For each file in review_scope:
  1. Determine language from extension
  2. Apply security checks (OWASP patterns)
  3. Apply error handling checks
  4. Apply code style checks
  5. Apply performance checks
  6. Apply project-specific rules
  7. Extract line numbers for issues
  8. Categorize by severity
```

### Step 6: Calculate Score (Optional)

If `--score` flag is enabled:

```
Score = 100 - (Critical × 20) - (Warning × 5) - (Suggestion × 1)

Interpretation:
  95-100: Excellent - Auto-approve
  90-94:  Good - Approve
  80-89:  Fair - Request changes
  60-79:  Poor - Block merge
  0-59:   Critical - Block merge
```

### Step 7: Generate Output

Structure findings for downstream consumption (github-review-publisher).

## Output Format

### Issue Structure

Each issue MUST include:

```yaml
- severity: CRITICAL|WARNING|SUGGESTION
  category: Security|Error Handling|Code Style|Performance|Project Rule
  file: src/api/handler.ts
  line_number: 45                    # From NEW file
  line_reference: "NEW_FILE"         # Always NEW_FILE
  commit_sha: "abc123def456..."      # PR HEAD commit
  code_at_line: "eval(userInput)"    # For validation
  issue: "Potential code injection via eval()"
  current_code: |
    const result = eval(userInput);
  suggested_fix: |
    const result = JSON.parse(userInput);
  impact: "Remote code execution vulnerability"
  baseline_or_rule: "security-patterns.md"  # Source of rule
```

### Complete Output

```yaml
review_summary:
  score: 85                    # Only if --score enabled
  rating: "Fair"               # Only if --score enabled
  decision: "REQUEST_CHANGES"

  issue_counts:
    critical: 1
    warnings: 3
    suggestions: 4

  files_reviewed: 5
  lines_reviewed: 847

issues:
  - severity: CRITICAL
    category: Security
    file: src/api/handler.ts
    line_number: 45
    line_reference: "NEW_FILE"
    commit_sha: "abc123..."
    code_at_line: "eval(userInput)"
    issue: "Code injection vulnerability"
    current_code: |
      const result = eval(userInput);
    suggested_fix: |
      const result = JSON.parse(userInput);
    impact: "Remote code execution"
    baseline_or_rule: "security-patterns.md"

  - severity: WARNING
    category: Error Handling
    file: src/api/handler.ts
    line_number: 78
    line_reference: "NEW_FILE"
    commit_sha: "abc123..."
    code_at_line: "catch (e) { }"
    issue: "Empty catch block"
    current_code: |
      catch (e) { }
    suggested_fix: |
      catch (e) {
        logger.error('Failed', { error: e });
        throw e;
      }
    impact: "Errors silently swallowed"
    baseline_or_rule: "error-handling-patterns.md"

  # ... more issues

baseline_checks:
  security: FAIL (1 critical)
  error_handling: WARN (2 warnings)
  code_style: PASS
  performance: WARN (1 warning)

project_rules_applied:
  - ".claude/rules/api-conventions.md"
  - ".claude/rules/testing-requirements.md"
```

## Language-Specific Patterns

### TypeScript/JavaScript

```typescript
// Security - eval injection
// CRITICAL
eval(userInput)           // Bad
new Function(userInput)() // Bad
JSON.parse(userInput)     // Good (for JSON)

// Error handling - empty catch
// WARNING
catch (e) { }                    // Bad
catch (e) { console.log(e) }     // Better
catch (e) { logger.error(e); throw e } // Good

// Performance - blocking in async
// WARNING
const data = fs.readFileSync(path)  // Bad in async context
const data = await fs.promises.readFile(path) // Good
```

### Python

```python
# Security - pickle deserialization
# CRITICAL
pickle.loads(user_data)    # Bad
json.loads(user_data)      # Good

# Security - SQL injection
# CRITICAL
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")  # Bad
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))  # Good

# Error handling - bare except
# WARNING
except:           # Bad
except Exception: # Better
except ValueError as e: # Good
```

### Rust

```rust
// Error handling - unwrap without context
// WARNING
let value = result.unwrap();           // Bad
let value = result.expect("msg");      // Better
let value = result?;                   // Good
let value = result.context("msg")?;    // Best

// Performance - unnecessary clone
// WARNING
let s = string.clone();   // Bad if borrow would work
let s = &string;          // Good
```

### Go

```go
// Error handling - ignored error
// WARNING
result, _ := doSomething()    // Bad
result, err := doSomething()  // Good
if err != nil { ... }

// Security - SQL injection
// CRITICAL
db.Query("SELECT * FROM users WHERE id = " + userId)  // Bad
db.Query("SELECT * FROM users WHERE id = ?", userId)  // Good
```

## Integration with Project Rules

### How Rules are Applied

1. **Detection**:
   ```bash
   ls .claude/rules/*.md
   cat .claude/CLAUDE.md
   ```

2. **Parsing**:
   - Extract `# Rule:` headers
   - Extract `Pattern:` and `Anti-pattern:` sections
   - Extract severity levels

3. **Priority**:
   - Project rules override baseline when conflicting
   - More specific rules override general rules

### Example Project Rule

`.claude/rules/api-conventions.md`:
```markdown
# Rule: API Response Format

## Severity: WARNING

## Pattern
All API endpoints must return responses in this format:
```typescript
{
  success: boolean,
  data?: T,
  error?: { code: string, message: string }
}
```

## Anti-pattern
```typescript
// Bad: Inconsistent response format
res.json({ user: user })
res.json({ error: "Not found" })
```

## Good Pattern
```typescript
// Good: Consistent response format
res.json({ success: true, data: { user } })
res.json({ success: false, error: { code: "NOT_FOUND", message: "User not found" } })
```
```

## Integration with Other Skills

### Upstream Skills (Providers)

**pr-analysis**
- Provides `head_sha` (CRITICAL)
- Provides file list and diff
- Provides scope analysis

### Downstream Skills (Consumers)

**github-review-publisher**
- Receives issues in structured format
- Creates line-level GitHub comments
- Uses `line_number`, `commit_sha`, `line_reference`

## Command Line Options

When invoked via `/pr-review`:

| Option | Description | Default |
|--------|-------------|---------|
| `--score` | Enable 100-point scoring | Disabled |
| `--focus=areas` | Focus on specific areas | All areas |
| `--files=pattern` | Filter files by glob | All files |

**Focus Areas**:
- `security` - Security vulnerabilities only
- `performance` - Performance issues only
- `error-handling` - Error handling patterns
- `style` - Code style and documentation
- `all` - All baseline checks (default)

**Examples**:
```bash
# Full review with scoring
/pr-review 42 --score

# Security-focused review
/pr-review 42 --focus=security

# Review specific files
/pr-review 42 --files="src/**/*.ts"
```

## Error Handling

### File Not Found
```
Warning: Could not read file {path}

Cause: File doesn't exist or isn't accessible

Action: Verify file path is correct
```

### Line Extraction Failed
```
Warning: Could not extract line number for pattern "{pattern}"

Cause: Pattern not found in file at HEAD commit

Action: Issue will be reported without line number
```

### Project Rules Parse Error
```
Warning: Could not parse rule file {path}

Cause: Invalid rule format

Action: Review will continue with baseline rules only
```

## Examples

### Example 1: Security Issue Found

**Input**: Review `src/api/handler.ts`

**Finding**:
```typescript
// Line 45
const query = `SELECT * FROM users WHERE id = ${req.params.id}`;
```

**Output**:
```yaml
- severity: CRITICAL
  category: Security
  file: src/api/handler.ts
  line_number: 45
  line_reference: "NEW_FILE"
  commit_sha: "abc123..."
  issue: "SQL injection vulnerability - user input directly interpolated"
  current_code: |
    const query = `SELECT * FROM users WHERE id = ${req.params.id}`;
  suggested_fix: |
    const query = 'SELECT * FROM users WHERE id = ?';
    const result = await db.query(query, [req.params.id]);
  impact: "Attacker can execute arbitrary SQL commands"
  baseline_or_rule: "security-patterns.md"
```

### Example 2: Multiple Issues

**Input**: Review PR #42 with `--score`

**Output**:
```yaml
review_summary:
  score: 72
  rating: "Poor"
  decision: "REQUEST_CHANGES"

  issue_counts:
    critical: 1
    warnings: 4
    suggestions: 3

issues:
  - severity: CRITICAL
    category: Security
    file: src/api/handler.ts
    line_number: 45
    issue: "SQL injection vulnerability"
    ...

  - severity: WARNING
    category: Error Handling
    file: src/api/handler.ts
    line_number: 78
    issue: "Empty catch block"
    ...

  - severity: WARNING
    category: Performance
    file: src/services/user.ts
    line_number: 120
    issue: "N+1 query pattern detected"
    ...

baseline_checks:
  security: FAIL
  error_handling: WARN
  code_style: PASS
  performance: WARN

project_rules_applied:
  - ".claude/rules/api-conventions.md"
```

## Reference Files

### 1. `references/security-patterns.md`
OWASP Top 10 patterns and detection methods

### 2. `references/error-handling-patterns.md`
Error handling anti-patterns and best practices

### 3. `references/code-style-guide.md`
Language-agnostic style guidelines

### 4. `references/performance-patterns.md`
Performance anti-patterns and optimizations

### 5. `references/line-number-extraction.md`
Critical guide for extracting line numbers from NEW file

## Version History

- **1.0.0** (2025-01-08): Initial skill for software-engineering-suite
  - Baseline standards (security, error handling, style, performance)
  - Project rules integration
  - Configurable scoring
  - Multi-language support
  - Line number extraction from NEW file
