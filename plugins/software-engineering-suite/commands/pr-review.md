---
description: Review a pull request using the pr-review agent with baseline quality standards and optional scoring
---

# PR Review Command

Automatically review a pull request using comprehensive quality standards and create pending GitHub review comments.

## Syntax

```bash
/pr-review <pr-number|url> [options]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `<pr-number>` | Yes* | PR number (e.g., `123`) |
| `<url>` | Yes* | Full PR URL (e.g., `https://github.com/owner/repo/pull/123`) |

*One of `pr-number` or `url` is required.

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--score` | Enable 100-point quality scoring | Disabled |
| `--focus=<areas>` | Focus on specific areas (comma-separated) | All areas |
| `--files=<pattern>` | Filter files by glob pattern | All files |

### Focus Areas

- `security` - Security vulnerabilities (OWASP Top 10)
- `performance` - Performance anti-patterns
- `error-handling` - Error handling patterns
- `style` - Code style and documentation
- `all` - All baseline checks (default)

## Examples

### Basic Review

```bash
/pr-review 123
```

Reviews PR #123 with all baseline checks, no scoring.

### Review with Scoring

```bash
/pr-review 123 --score
```

Reviews PR #123 and calculates a 100-point quality score.

### Review from URL

```bash
/pr-review https://github.com/owner/repo/pull/123
```

Reviews PR from full URL (useful when not in repo directory).

### Security-Focused Review

```bash
/pr-review 123 --focus=security
```

Reviews only security-related issues (SQL injection, XSS, secrets, etc.)

### Multiple Focus Areas

```bash
/pr-review 123 --focus=security,error-handling
```

Reviews security and error handling issues only.

### Review Specific Files

```bash
/pr-review 123 --files="src/**/*.ts"
```

Reviews only TypeScript files in src/ directory.

### Full Options

```bash
/pr-review 123 --score --focus=security,performance --files="src/**"
```

## What It Does

This command invokes the **pr-review agent** which orchestrates three skills:

```
/pr-review 123 --score
    ↓
┌─────────────────────────────────────────┐
│ 1. pr-analysis                          │
│    - Fetch PR metadata                   │
│    - Get file changes                    │
│    - Identify scope                      │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│ 2. code-quality-review                  │
│    - Apply baseline standards            │
│    - Apply project rules                 │
│    - Calculate score (if enabled)        │
│    - Categorize issues                   │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│ 3. github-review-publisher              │
│    - Validate line numbers               │
│    - Create pending review               │
│    - Attach line-level comments          │
└─────────────────────────────────────────┘
```

## Quality Standards

### Baseline Checks (Always Applied)

| Category | What It Checks |
|----------|----------------|
| **Security** | SQL injection, XSS, hardcoded secrets, command injection, SSRF |
| **Error Handling** | Empty catch blocks, swallowed exceptions, missing error context |
| **Code Style** | Dead code, unused imports, naming conventions, documentation |
| **Performance** | N+1 queries, unnecessary allocations, blocking in async |

### Project Rules (Auto-Detected)

The command automatically incorporates rules from:
- `.claude/rules/*.md` - Project-specific patterns
- `.claude/CLAUDE.md` - Project instructions

Project rules **override** baseline standards when conflicting.

## Scoring System

When `--score` is enabled:

```
Score = 100 - (Critical × 20) - (Warning × 5) - (Suggestion × 1)

95-100: Excellent - Auto-approve recommendation
90-94:  Good - Approve recommendation
80-89:  Fair - Request changes recommendation
60-79:  Poor - Block merge recommendation
0-59:   Critical - Block merge recommendation
```

## Output

### Summary in Chat

```markdown
# PR Review Complete: PR #123

## PR Information
- **Repository**: owner/repo
- **Title**: feat: Add user authentication
- **Author**: @developer

## Review Statistics
- **Quality Score**: 85/100 (Fair)
- **Decision**: REQUEST_CHANGES
- **Total Issues**: 6
  - Critical: 1
  - Warning: 3
  - Suggestions: 2

## Next Steps
1. Go to: https://github.com/owner/repo/pull/123/files
2. Review pending comments
3. Submit review when ready
```

### GitHub Pending Review

- Line-level comments attached to specific lines
- Formatted with severity indicators
- Includes suggested fixes and explanations
- **PENDING** - requires manual submission

## Prerequisites

- `gh` CLI installed (`brew install gh`)
- Authenticated with GitHub (`gh auth login`)
- Access to target repository

## Error Handling

### PR Not Found

```
Error: PR #123 not found

Verify:
- PR number is correct
- Repository is accessible
- Run: gh pr view 123
```

### Authentication Error

```
Error: gh CLI not authenticated

Solution: Run 'gh auth login'
```

### No Changes to Review

```
PR #123 has no reviewable changes

The PR contains only:
- Documentation changes
- Configuration changes

No code quality review needed.
```

## Tips

1. **Start without scoring** to see all issues first
2. **Use `--focus`** for targeted reviews (e.g., security audit)
3. **Check pending comments** in GitHub before submitting
4. **Edit comments** in GitHub UI if needed
5. **Re-run** after fixes to verify improvements

## Related

- **pr-analysis skill** - Standalone PR data fetching
- **code-quality-review skill** - Standalone code review
- **github-review-publisher skill** - Standalone review publishing

## Version

- **1.0.0** (2025-01-08): Initial command for software-engineering-suite
