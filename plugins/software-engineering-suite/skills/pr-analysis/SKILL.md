---
name: pr-analysis
description: |
  Fetch and analyze pull request data using GitHub CLI. Extracts PR metadata, diff changes, file modifications, and identifies scope of changes. Auto-activates for: "analyze PR", "fetch pull request", "get PR details", "what changed in PR".
allowed-tools: Bash, Read, Grep, Glob, Write, WebFetch
version: 1.0.0
---

# PR Analysis Skill

## Overview

This skill fetches and analyzes pull request data from GitHub repositories using the `gh` CLI tool. It extracts comprehensive PR information including metadata, file changes, diff content, and identifies the scope and nature of changes.

This is a **generic skill** that works with any repository and any language. It provides context for downstream review skills.

## When to Use This Skill

This skill **auto-activates** when users request:
- "Analyze PR #123"
- "Fetch pull request data for #456"
- "Get PR details"
- "What changed in this PR"
- "Show me the diff for PR #789"
- "What files were modified in the pull request"

The skill can also be invoked as part of larger workflows (e.g., `/pr-review`) to provide PR context for downstream skills.

## Input Context

The skill expects one of the following:

1. **PR Number** (repository auto-detected from git):
   ```
   User: "Analyze PR #238"
   -> Detects repo from git remote
   ```

2. **Full PR URL**:
   ```
   User: "Analyze https://github.com/owner/repo/pull/238"
   -> Extracts owner, repo, and PR number
   ```

3. **PR Number + Repository**:
   ```
   User: "Analyze PR #238 in owner/repo"
   -> Uses explicit repository
   ```

## Process

### Step 1: Parse Input

Extract the following from user request:
- **PR Number**: Integer identifier
- **Repository**: Auto-detect from git or extract from URL
  - Format: `owner/repo` (e.g., `facebook/react`)
- **Optional Filters**: Specific files or paths to focus on

**Auto-Detection Logic**:
```bash
# If repository not provided, detect from git remote
git remote get-url origin
# Parse: https://github.com/owner/repo.git -> owner/repo
# Parse: git@github.com:owner/repo.git -> owner/repo
```

### Step 2: Fetch PR Metadata

Use `gh` CLI to fetch comprehensive PR information:

```bash
gh pr view {pr-number} \
  --repo {owner}/{repo} \
  --json number,title,author,state,headRefName,baseRefName,headRefOid,createdAt,updatedAt,changedFiles,additions,deletions,body
```

**Extract**:
- PR number and title
- Author (login and name)
- State (OPEN, CLOSED, MERGED)
- Branch names (head and base)
- HEAD commit SHA (critical for line number extraction)
- Timestamps (created, updated)
- Change statistics (files changed, additions, deletions)
- PR description/body

### Step 3: Fetch File Changes

Get the list of files modified in the PR:

```bash
gh pr diff {pr-number} --repo {owner}/{repo} --name-only
```

**Categorize files by type** (generic categories):

| Category | Patterns |
|----------|----------|
| `source` | `src/**`, `lib/**`, `app/**`, `*.py`, `*.js`, `*.ts`, `*.rs`, `*.go`, `*.java`, `*.rb` |
| `tests` | `test/**`, `tests/**`, `__tests__/**`, `*_test.*`, `*.test.*`, `*.spec.*` |
| `documentation` | `*.md`, `docs/**`, `*.rst`, `*.txt` |
| `configuration` | `*.json`, `*.yaml`, `*.yml`, `*.toml`, `Cargo.toml`, `package.json`, `pyproject.toml` |
| `ci_cd` | `.github/**`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci/**`, `Dockerfile`, `docker-compose.*` |
| `other` | Files not matching above patterns |

### Step 4: Fetch Full Diff

Get the complete diff content:

```bash
gh pr diff {pr-number} --repo {owner}/{repo}
```

**Parse diff** to extract:
- Modified files with line ranges
- Added lines (prefixed with `+`)
- Removed lines (prefixed with `-`)
- Context lines (unchanged)
- Diff hunks (sections of changes)

### Step 5: Identify Change Scope

Analyze the changes to determine:

**Scope Categories**:
- **Source Code**: Changes in application code
- **Tests**: Test file modifications
- **Documentation**: README, docs updates
- **Configuration**: Config file changes
- **CI/CD**: Pipeline, workflow changes
- **Infrastructure**: Docker, deployment configs

**Change Characteristics**:
- `new_feature`: New files added with significant code
- `bug_fix`: Small targeted changes
- `refactoring`: Large changes with balanced add/remove
- `documentation_only`: Only docs changed
- `tests_only`: Only test files changed
- `security_sensitive`: Changes to auth, crypto, secrets handling
- `breaking_changes`: API signature changes, config format changes

### Step 6: Extract Commit Information

Get commit history for context:

```bash
gh pr view {pr-number} --repo {owner}/{repo} --json commits -q '.commits[]|{oid,messageHeadline,author}'
```

**Useful for**:
- Understanding change progression
- Identifying incremental fixes
- Detecting WIP or fixup commits

### Step 7: Get HEAD Commit SHA (Critical)

**This is critical for downstream skills** that need to create line-level comments:

```bash
HEAD_SHA=$(gh pr view {pr-number} --repo {owner}/{repo} --json headRefOid -q '.headRefOid')
```

This SHA is used by `code-quality-review` and `github-review-publisher` to:
- Fetch file content at the correct version
- Create review comments on the correct commit

## Output

The skill produces a **structured PR analysis** containing:

### 1. PR Metadata Section

```yaml
pr_metadata:
  number: 238
  title: "feat: Add new authentication flow"
  author: username
  state: OPEN
  head_branch: feature/new-auth
  base_branch: main
  head_sha: abc123def456789...  # CRITICAL for line comments
  created_at: 2025-12-08T10:30:00Z
  updated_at: 2025-12-09T15:45:00Z
  changed_files: 8
  additions: 547
  deletions: 23
```

### 2. File Changes Section

```yaml
files_changed:
  source:
    - src/auth/handler.ts
    - src/auth/middleware.ts
    - lib/utils/crypto.ts
  tests:
    - tests/auth.test.ts
    - tests/integration/auth.spec.ts
  documentation:
    - README.md
    - docs/authentication.md
  configuration:
    - package.json
  ci_cd: []
  other: []
```

### 3. Change Scope Analysis

```yaml
scope:
  primary: source_code
  categories:
    - source_code
    - tests
    - documentation

  change_characteristics:
    new_feature: true
    bug_fix: false
    refactoring: false
    documentation_only: false
    tests_only: false
    security_sensitive: true  # auth changes detected
    breaking_changes: false
```

### 4. Diff Summary

```yaml
diff_summary:
  total_hunks: 25
  files:
    - path: src/auth/handler.ts
      additions: 156
      deletions: 0
      hunks: 5
    - path: src/auth/middleware.ts
      additions: 234
      deletions: 15
      hunks: 8
```

### 5. Commit History

```yaml
commits:
  - oid: abc123def456
    message: "feat: Add authentication handler"
    author: username
  - oid: def456ghi789
    message: "feat: Add auth middleware"
    author: username
  - oid: ghi789jkl012
    message: "test: Add auth tests"
    author: username
```

### 6. Full Diff Content

```yaml
diff_content: |
  diff --git a/src/auth/handler.ts b/src/auth/handler.ts
  new file mode 100644
  --- /dev/null
  +++ b/src/auth/handler.ts
  @@ -0,0 +1,156 @@
  +import { Request, Response } from 'express';
  ...
```

## Integration with Other Skills

### Downstream Skills (Consumers)

**1. code-quality-review**
- Uses `files_changed` to focus review on relevant files
- Uses `diff_content` to identify review targets
- Uses `scope.change_characteristics` to apply appropriate standards
- Uses `head_sha` for line number extraction

**2. github-review-publisher**
- Uses file paths for line-level comments
- Uses `pr_metadata` for review context
- Uses `head_sha` for review creation (CRITICAL)

### Standalone Usage

Can be used independently for:
- Quick PR summaries in chat
- Understanding PR scope before deep review
- Extracting specific file changes
- Analyzing change patterns across PRs

## Error Handling

### PR Not Found
```
Error: PR #{number} not found in {owner}/{repo}

Possible causes:
- Incorrect PR number
- Wrong repository
- PR doesn't exist
- No read access to repository

Solution: Verify PR number and repository access
```

### Authentication Failure
```
Error: gh CLI not authenticated

Solution: Run 'gh auth login' to authenticate
```

### Repository Auto-Detection Failed
```
Error: Could not detect repository from git remote

Solution: Provide explicit repository (owner/repo) or run from git repository
```

## Examples

### Example 1: Simple Analysis

**Input**: "Analyze PR #42"

**Process**:
1. Detect repo from git: `owner/my-project`
2. Fetch PR metadata via gh CLI
3. Get file changes: 5 files
4. Identify scope: source_code (new feature)
5. Parse diff: 347 additions, 12 deletions

**Output**:
```
PR #42 Analysis

**Title**: feat: Add user profile endpoint
**Author**: @developer
**State**: OPEN (created 1 day ago)
**Changes**: 5 files, +347 -12 lines

**Scope**: Source Code (New Feature)
- Security Sensitive: false
- Files:
  - src/api/profile.ts (+156 lines)
  - src/models/user.ts (+89 lines)
  - tests/profile.test.ts (+98 lines)

**HEAD SHA**: abc123def456...
**Ready for**: code-quality-review
```

### Example 2: URL-Based Analysis

**Input**: "Analyze https://github.com/facebook/react/pull/12345"

**Process**:
1. Parse URL: owner=facebook, repo=react, pr=12345
2. Continue with standard analysis

### Example 3: Filtered Analysis

**Input**: "What test files changed in PR #42"

**Process**:
1. Fetch PR data
2. Filter file changes for test patterns
3. Extract test-specific details

**Output**:
```
Test Changes in PR #42

**Files Modified**:
1. tests/profile.test.ts
   - +98 lines, -0 lines
   - 3 change hunks

2. tests/integration/api.spec.ts
   - +45 lines, -5 lines
   - 2 change hunks
```

## Performance Considerations

- **gh CLI calls**: Minimize by using `--json` with multiple fields
- **Diff parsing**: For large PRs (>100 files), consider pagination
- **Categorization**: Use efficient path matching (glob patterns)

## Version History

- **1.0.0** (2025-01-08): Initial skill creation for software-engineering-suite
  - Generic file categorization (language-agnostic)
  - PR metadata fetching with HEAD SHA
  - Diff parsing and analysis
  - Scope identification
  - Commit history extraction
