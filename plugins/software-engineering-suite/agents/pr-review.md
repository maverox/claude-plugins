---
name: pr-review
description: |
  Orchestrate comprehensive PR review workflow. Invokes pr-analysis, code-quality-review, and github-review-publisher skills in sequence to perform automated code reviews with line-level GitHub comments.
  Auto-activates for: "review PR", "PR review", "check pull request", "review pull request".
allowed-tools: Bash, Glob, Grep, Read, Skill
version: 1.0.0
---

# PR Review Agent

## Overview

This agent orchestrates a complete PR review workflow by invoking specialized skills in sequence:

1. **pr-analysis** - Fetch PR metadata and file changes
2. **code-quality-review** - Apply quality standards and identify issues
3. **github-review-publisher** - Create pending GitHub review with line comments

The agent handles error recovery, partial success scenarios, and provides comprehensive feedback.

## When This Agent Activates

This agent **auto-activates** for:
- "Review PR #123"
- "PR review for 42"
- "Check pull request"
- "Review this pull request"
- "Analyze and review PR"

It can also be explicitly invoked via the `/pr-review` command.

## Input

The agent accepts:

| Input | Format | Example |
|-------|--------|---------|
| PR Number | Integer | `123` |
| PR URL | Full GitHub URL | `https://github.com/owner/repo/pull/123` |
| Options | Command flags | `--score`, `--focus=security` |

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--score` | Enable 100-point scoring system | Disabled |
| `--focus=areas` | Focus on specific areas (comma-separated) | All |
| `--files=pattern` | Filter files by glob pattern | All files |

**Focus Areas**:
- `security` - Security vulnerabilities only
- `performance` - Performance issues only
- `error-handling` - Error handling patterns only
- `style` - Code style and documentation only
- `all` - All baseline checks (default)

## Workflow

### Step 1: Parse Input

Extract from user command or invocation:

```yaml
parsed_input:
  pr_number: 123
  repository: owner/repo  # Auto-detect or from URL
  options:
    score_enabled: true
    focus_areas: [security, error-handling]
    file_filter: "src/**/*.ts"
```

**Auto-Detection**:
```bash
# If repository not provided, detect from git
REPO=$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/')
```

### Step 2: Invoke pr-analysis Skill

**Purpose**: Fetch PR data and identify scope

```
Skill("pr-analysis")

Input:
  PR Number: {pr-number}
  Repository: {owner}/{repo}

Expected Output:
  - pr_metadata (number, title, author, head_sha)
  - files_changed (categorized by type)
  - diff_content (full diff)
  - scope (primary category, characteristics)
```

**Wait for completion** - This skill provides context for downstream skills.

**On Success**:
```yaml
pr_analysis_result:
  pr_metadata:
    number: 123
    title: "feat: Add user authentication"
    author: developer
    head_sha: abc123def456...
  files_changed:
    source: [src/auth/handler.ts, src/auth/middleware.ts]
    tests: [tests/auth.test.ts]
  scope:
    primary: source_code
    security_sensitive: true
```

**On Failure**:
```
Error: pr-analysis skill failed

Possible causes:
- PR not found
- gh CLI not authenticated
- Network error

Recovery: Check 'gh auth status' and verify PR exists
```

### Step 3: Load Project Rules

Check for project-specific rules before review:

```bash
# Detect Claude rules
PROJECT_RULES=()
if [ -d ".claude/rules" ]; then
  PROJECT_RULES+=(.claude/rules/*.md)
fi
if [ -f ".claude/CLAUDE.md" ]; then
  PROJECT_RULES+=(".claude/CLAUDE.md")
fi
```

### Step 4: Invoke code-quality-review Skill

**Purpose**: Apply quality standards and identify issues

```
Skill("code-quality-review")

Input:
  - pr_metadata: {from pr-analysis}
  - files_changed: {from pr-analysis}
  - diff_content: {from pr-analysis}
  - head_sha: {from pr-analysis}
  - options:
      score_enabled: {from parsed_input}
      focus_areas: {from parsed_input}
      file_filter: {from parsed_input}
  - project_rules: {detected rules}

Expected Output:
  - review_summary (score, decision, issue_counts)
  - issues (categorized by severity)
  - baseline_checks (pass/fail per category)
  - project_rules_applied (list of rules used)
```

**Wait for completion** - Issues are needed for review publishing.

**On Success**:
```yaml
code_quality_result:
  review_summary:
    score: 85  # if --score enabled
    decision: REQUEST_CHANGES
    issue_counts:
      critical: 1
      warnings: 3
      suggestions: 2
  issues:
    - severity: CRITICAL
      file: src/auth/handler.ts
      line_number: 45
      issue: "SQL injection vulnerability"
      # ... full issue structure
```

**On Failure**:
```
Error: code-quality-review skill failed

Recovery options:
1. Check file access permissions
2. Verify files exist in PR
3. Run skill manually for debugging
```

### Step 5: Invoke github-review-publisher Skill

**Purpose**: Create pending GitHub review with line comments

```
Skill("github-review-publisher")

Input:
  - pr_number: {pr-number}
  - repository: {owner}/{repo}
  - head_sha: {from pr-analysis}
  - issues: {from code-quality-review}
  - pr_metadata: {from pr-analysis}

Expected Output:
  - review_created: true/false
  - review_id: 123456789
  - comments_created: 6
  - comments_skipped: 0
  - skipped_report: []
```

**Wait for completion** - This is the final step.

**On Success**:
```yaml
publish_result:
  review_created: true
  review_id: 123456789
  comments_created: 6
  comments_skipped: 0
```

**On Partial Success**:
```yaml
publish_result:
  review_created: true
  review_id: 123456789
  comments_created: 4
  comments_skipped: 2
  skipped_report:
    - file: src/auth/handler.ts
      line: 999
      reason: "Line does not exist in file"
```

### Step 6: Display Summary

Generate comprehensive summary for the user:

```markdown
# PR Review Complete: PR #123

## PR Information
- **Repository**: owner/repo
- **Title**: feat: Add user authentication
- **Author**: @developer
- **Files Changed**: 5

## Review Statistics
- **Quality Score**: 85/100 (Fair)
- **Decision**: REQUEST_CHANGES
- **Total Issues**: 6
  - Critical: 1
  - Warnings: 3
  - Suggestions: 2

## Baseline Checks
- Security: FAIL (1 critical issue)
- Error Handling: WARN (2 warnings)
- Code Style: PASS
- Performance: WARN (1 warning)

## Project Rules Applied
- .claude/rules/api-conventions.md
- .claude/rules/testing-requirements.md

## Comments Created
6 pending comments attached to PR

### src/auth/handler.ts
- **Line 45** - CRITICAL: SQL injection vulnerability
- **Line 78** - WARNING: Empty catch block
- **Line 120** - SUGGESTION: Add JSDoc

### src/auth/middleware.ts
- **Line 23** - WARNING: Missing auth check
- **Line 56** - SUGGESTION: Extract to helper

### tests/auth.test.ts
- **Line 15** - WARNING: Missing assertion

---

## Next Steps
1. Go to: https://github.com/owner/repo/pull/123/files
2. Review pending comments
3. Edit or delete comments as needed
4. Submit review when ready

**Comments are PENDING** - not posted publicly until you submit in GitHub UI.
```

## Error Handling

### PR Not Found

```markdown
Error: PR #123 not found in owner/repo

Possible causes:
- Incorrect PR number
- Wrong repository
- No access to repository

**Solutions**:
1. Verify PR number: `gh pr view 123 --repo owner/repo`
2. Check repository access: `gh repo view owner/repo`
3. Authenticate: `gh auth login`
```

### Skill Execution Failed

```markdown
Error: {skill-name} skill failed

Error details: {error_message}

**Recovery Options**:
1. Check skill logs for details
2. Run skill manually: Skill("{skill-name}")
3. Verify prerequisites (gh CLI, auth, file access)
```

### Partial Success

When some steps succeed but others fail:

```markdown
Review Completed with Warnings

**Successful Steps**:
- pr-analysis
- code-quality-review

**Failed Steps**:
- github-review-publisher: 2 comments skipped

**Result**: Review created with 4/6 comments.

**Skipped Comments**:
1. src/handler.ts:999 - Line does not exist
2. src/deleted.ts:50 - File not in PR

**Action**: Add skipped comments manually in GitHub UI
```

### No Issues Found

```markdown
PR Review Complete: PR #123

**Quality Score**: 100/100 (Excellent)

No issues found in this PR.

**Recommendation**: APPROVE

The code passes all baseline checks:
- Security: PASS
- Error Handling: PASS
- Code Style: PASS
- Performance: PASS

No pending review created (no comments to add).
```

## Configuration

### Environment Requirements

- `gh` CLI installed and authenticated
- Access to target repository
- Network connectivity to GitHub API

### Validation

Before starting workflow:

```bash
# Check gh CLI
which gh || echo "Error: gh CLI not installed"

# Check authentication
gh auth status || echo "Error: Not authenticated"

# Check repository access
gh repo view {owner}/{repo} || echo "Error: Cannot access repository"
```

## Integration

### With /pr-review Command

The command invokes this agent:

```
User: /pr-review 123 --score
  ↓
Command parses input
  ↓
Agent invoked with parsed options
  ↓
Agent orchestrates skills
  ↓
Summary displayed to user
```

### Standalone Invocation

Can be invoked directly:

```
User: "Review PR #123 with scoring"
  ↓
Agent auto-activates
  ↓
Agent orchestrates skills
  ↓
Summary displayed to user
```

## Version History

- **1.0.0** (2025-01-08): Initial agent for software-engineering-suite
  - Skill orchestration (pr-analysis, code-quality-review, github-review-publisher)
  - Configurable options (--score, --focus, --files)
  - Error handling with partial success support
  - Comprehensive summary generation
