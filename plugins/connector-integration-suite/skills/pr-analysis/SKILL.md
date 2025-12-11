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
   → Detects repo from git remote
   ```

2. **Full PR URL**:
   ```
   User: "Analyze https://github.com/hyperswitch/connector-service/pull/238"
   → Extracts owner, repo, and PR number
   ```

3. **PR Number + Repository**:
   ```
   User: "Analyze PR #238 in hyperswitch/connector-service"
   → Uses explicit repository
   ```

## Process

### Step 1: Parse Input

Extract the following from user request:
- **PR Number**: Integer identifier
- **Repository**: Auto-detect from git or extract from URL
  - Format: `owner/repo` (e.g., `hyperswitch/connector-service`)
- **Optional Filters**: Specific files or paths to focus on

**Auto-Detection Logic**:
```bash
# If repository not provided, detect from git remote
git remote get-url origin
# Parse: https://github.com/owner/repo.git → owner/repo
```

### Step 2: Fetch PR Metadata

Use `gh` CLI to fetch comprehensive PR information:

```bash
gh pr view {pr-number} \
  --repo {owner}/{repo} \
  --json number,title,author,state,headRefName,baseRefName,createdAt,updatedAt,changedFiles,additions,deletions,body
```

**Extract**:
- PR number and title
- Author (login and name)
- State (OPEN, CLOSED, MERGED)
- Branch names (head and base)
- Timestamps (created, updated)
- Change statistics (files changed, additions, deletions)
- PR description/body

### Step 3: Fetch File Changes

Get the list of files modified in the PR:

```bash
gh pr diff {pr-number} --repo {owner}/{repo} --name-only
```

**Categorize files** by type:
- **Connector files**: `backend/connector-integration/src/connectors/**`
- **Core domain**: `backend/domain_types/**`
- **Tests**: `**/*test*.rs`, `**/tests/**`
- **Documentation**: `**/*.md`
- **Configuration**: `Cargo.toml`, `*.json`, `*.yaml`

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
- **Connector Integration**: Changes in connector files
- **Core Domain**: Type definitions, domain models
- **API Changes**: Router, handlers, endpoints
- **Infrastructure**: Configuration, CI/CD
- **Documentation**: README, docs
- **Tests**: Test files, test utilities

**Change Patterns**:
- New file creation vs. modification
- Large refactoring (>500 lines changed)
- Security-sensitive areas (auth, encryption, secrets)
- Performance-critical paths (hot loops, DB queries)

### Step 6: Extract Commit Information

Get commit history for context:

```bash
gh pr view {pr-number} --repo {owner}/{repo} --json commits -q '.commits[]|{oid,messageHeadline,author}'
```

**Useful for**:
- Understanding change progression
- Identifying incremental fixes
- Detecting WIP or fixup commits

## Output

The skill produces a **structured PR analysis** containing:

### 1. PR Metadata Section

```yaml
pr_number: 238
title: "feat(connector): Add Stripe integration"
author: username
state: OPEN
head_branch: feature/stripe-connector
base_branch: main
created_at: 2025-12-08T10:30:00Z
updated_at: 2025-12-09T15:45:00Z
changed_files: 8
additions: 1247
deletions: 23
```

### 2. File Changes Section

```yaml
files_changed:
  connector_files:
    - backend/connector-integration/src/connectors/stripe.rs
    - backend/connector-integration/src/connectors/stripe/transformers.rs
  core_domain:
    - backend/domain_types/src/types.rs
  tests:
    - backend/connector-integration/tests/stripe_tests.rs
  documentation:
    - README.md
```

### 3. Change Scope Analysis

```yaml
scope:
  primary: connector_integration
  categories:
    - connector_integration
    - core_domain
    - tests

  change_characteristics:
    new_connector: true
    security_sensitive: true  # auth changes detected
    large_refactor: false
    breaking_changes: false

  connector_details:  # if applicable
    connector_name: stripe
    flows_implemented:
      - Authorize
      - Capture
      - Void
      - Refund
```

### 4. Diff Summary

```yaml
diff_summary:
  hunks: 45
  significant_changes:
    - file: backend/connector-integration/src/connectors/stripe.rs
      lines_added: 456
      lines_removed: 0
      hunks: 12
    - file: backend/connector-integration/src/connectors/stripe/transformers.rs
      lines_added: 678
      lines_removed: 15
      hunks: 18
```

### 5. Commit History

```yaml
commits:
  - oid: abc123def456
    message: "feat: Add Stripe connector structure"
    author: username
  - oid: def456ghi789
    message: "feat: Implement Stripe transformers"
    author: username
  - oid: ghi789jkl012
    message: "fix: Update status mappings"
    author: username
```

## Integration with Other Skills

### Downstream Skills (Consumers)

**1. code-quality-review**
- Uses file changes to focus review
- Leverages diff to identify review targets
- Uses scope analysis to apply appropriate standards

**2. connector-integration-validator**
- Triggered if `scope.primary == "connector_integration"`
- Uses connector_name and flows_implemented
- Reads diff to extract implementation details

**3. github-review-publisher**
- Uses file paths for line-level comments
- References PR metadata for review context
- Uses commit SHA for review creation

### Standalone Usage

Can be used independently for:
- Quick PR summaries in chat
- Understanding PR scope before deep review
- Extracting specific file changes
- Analyzing change patterns across PRs

## Reference Files

### 1. `gh-cli-patterns.md`
Comprehensive guide to GitHub CLI usage:
- Common `gh` commands for PR operations
- JSON query patterns (`.commits[]`, `.headRefOid`, etc.)
- Error handling for gh CLI failures
- Authentication troubleshooting

### 2. `diff-parsing.md`
Diff parsing techniques:
- Understanding unified diff format
- Extracting line numbers from hunks
- Identifying added/removed/modified lines
- Multi-line comment range detection
- Handling binary file changes

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

**Input**: "Analyze PR #238"

**Process**:
1. Detect repo from git: `hyperswitch/connector-service`
2. Fetch PR metadata via gh CLI
3. Get file changes: 8 files
4. Identify scope: connector_integration (Stripe)
5. Parse diff: 1247 additions, 23 deletions

**Output**:
```
📋 PR #238 Analysis

**Title**: feat(connector): Add Stripe integration
**Author**: @username
**State**: OPEN (created 2 days ago)
**Changes**: 8 files, +1247 -23 lines

**Scope**: Connector Integration
- New connector: Stripe
- Flows: Authorize, Capture, Void, Refund
- Files:
  - stripe.rs (+456 lines)
  - stripe/transformers.rs (+678 lines)
  - tests (+98 lines)

**Ready for**: code-quality-review, connector-integration-validator
```

### Example 2: Focused Analysis

**Input**: "What connector files changed in PR #238"

**Process**:
1. Fetch PR data
2. Filter file changes for connector paths
3. Extract connector-specific details

**Output**:
```
🔍 Connector Changes in PR #238

**Connector**: Stripe
**Files Modified**:
1. backend/connector-integration/src/connectors/stripe.rs
   - +456 lines, -0 lines
   - 12 change hunks

2. backend/connector-integration/src/connectors/stripe/transformers.rs
   - +678 lines, -15 lines
   - 18 change hunks

**Flows Detected**: Authorize, Capture, Void, Refund
```

### Example 3: URL-Based Analysis

**Input**: "Analyze https://github.com/hyperswitch/connector-service/pull/238"

**Process**:
1. Parse URL: owner=hyperswitch, repo=connector-service, pr=238
2. Continue with standard analysis

**Output**: Same as Example 1

## Performance Considerations

- **gh CLI calls**: Minimize by using `--json` with multiple fields
- **Diff parsing**: For large PRs (>1000 files), consider pagination
- **Categorization**: Use efficient path matching (glob patterns)

## Version History

- **1.0.0** (2025-12-09): Initial skill creation
  - PR metadata fetching
  - File change categorization
  - Diff parsing and analysis
  - Scope identification
  - Commit history extraction
