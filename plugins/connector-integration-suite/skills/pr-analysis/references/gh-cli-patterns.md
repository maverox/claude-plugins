# GitHub CLI Patterns Reference

**Version**: 1.0.0
**Purpose**: Comprehensive guide to using `gh` CLI for PR operations

---

## Installation & Authentication

### Check Installation
```bash
gh --version
# Output: gh version 2.40.0 (2024-01-15)
```

### Authentication
```bash
# Interactive login
gh auth login

# Check auth status
gh auth status

# Output should show:
# ✓ Logged in to github.com as username
# ✓ Token: *******************
```

### Set Default Repository
```bash
# Explicitly specify repo in each command
gh pr view 123 --repo owner/repo

# Or use -R shorthand
gh pr view 123 -R owner/repo
```

---

## PR Viewing Commands

### Basic PR View
```bash
# View PR summary
gh pr view {pr-number}

# View specific PR in specific repo
gh pr view {pr-number} --repo {owner}/{repo}
```

### JSON Output (Recommended)

**Single Field**:
```bash
gh pr view 238 --json title
# Output: {"title":"feat(connector): Add Stripe integration"}
```

**Multiple Fields**:
```bash
gh pr view 238 --json number,title,author,state,headRefName,baseRefName
```

**All Metadata**:
```bash
gh pr view 238 --json \
  number,title,author,state,headRefName,baseRefName,\
  createdAt,updatedAt,changedFiles,additions,deletions,\
  body,labels,assignees,reviewers
```

### Field Reference

| Field | Description | Example |
|-------|-------------|---------|
| `number` | PR number | `238` |
| `title` | PR title | `"feat: Add Stripe"` |
| `author` | PR author object | `{"login":"user"}` |
| `state` | PR state | `"OPEN"`, `"CLOSED"`, `"MERGED"` |
| `headRefName` | Source branch | `"feature/stripe"` |
| `baseRefName` | Target branch | `"main"` |
| `headRefOid` | HEAD commit SHA | `"abc123def456..."` |
| `createdAt` | Creation timestamp | `"2025-12-08T10:30:00Z"` |
| `updatedAt` | Last update timestamp | `"2025-12-09T15:45:00Z"` |
| `changedFiles` | File count | `8` |
| `additions` | Lines added | `1247` |
| `deletions` | Lines removed | `23` |
| `body` | PR description | `"This PR adds..."` |
| `labels` | Label objects | `[{"name":"enhancement"}]` |
| `commits` | Commit list | `[{"oid":"...","messageHeadline":"..."}]` |

---

## JSON Querying with jq

### Basic Queries

**Extract Single Value**:
```bash
gh pr view 238 --json title -q '.title'
# Output: feat(connector): Add Stripe integration
```

**Extract Nested Value**:
```bash
gh pr view 238 --json author -q '.author.login'
# Output: username
```

**Extract Array Elements**:
```bash
gh pr view 238 --json labels -q '.labels[].name'
# Output:
# enhancement
# connector
```

### Advanced Queries

**Commit SHA (HEAD)**:
```bash
COMMIT_SHA=$(gh pr view 238 --json headRefOid -q '.headRefOid')
echo $COMMIT_SHA
# Output: abc123def456789...
```

**Commit List**:
```bash
gh pr view 238 --json commits -q '.commits[]|{oid,message:.messageHeadline,author:.author.login}'
# Output:
# {
#   "oid": "abc123...",
#   "message": "feat: Add Stripe connector",
#   "author": "username"
# }
```

**Filter Commits**:
```bash
# Get only commit SHAs
gh pr view 238 --json commits -q '.commits[].oid'

# Get only commit messages
gh pr view 238 --json commits -q '.commits[].messageHeadline'
```

**Format Output**:
```bash
gh pr view 238 --json number,title,author -q '"PR #\(.number): \(.title) by @\(.author.login)"'
# Output: PR #238: feat(connector): Add Stripe integration by @username
```

---

## PR Diff Commands

### Full Diff
```bash
# Get complete diff
gh pr diff 238

# Diff for specific repo
gh pr diff 238 --repo owner/repo
```

### File List Only
```bash
# List changed files (names only)
gh pr diff 238 --name-only

# Output:
# backend/connector-integration/src/connectors/stripe.rs
# backend/connector-integration/src/connectors/stripe/transformers.rs
# backend/domain_types/src/types.rs
```

### Specific File Diff
```bash
# Get diff for specific file
gh pr diff 238 -- backend/connector-integration/src/connectors/stripe.rs
```

### Patch Format
```bash
# Get diff in patch format
gh pr diff 238 --patch
```

---

## PR File Operations

### List Files
```bash
# List all changed files with stats
gh pr view 238 --json files -q '.files[]|{path:.path,additions:.additions,deletions:.deletions}'

# Output:
# {
#   "path": "backend/connector-integration/src/connectors/stripe.rs",
#   "additions": 456,
#   "deletions": 0
# }
```

### File Filtering
```bash
# Get only Rust files
gh pr diff 238 --name-only | grep '\.rs$'

# Get only connector files
gh pr diff 238 --name-only | grep 'connectors/'

# Count changed files by type
gh pr diff 238 --name-only | grep '\.rs$' | wc -l
```

---

## PR Status & Checks

### Check Status
```bash
# Get CI/CD status
gh pr checks 238

# Output:
# ✓ Build          successful in 5m
# ✓ Tests          successful in 8m
# ✓ Lint           successful in 2m
```

### Detailed Checks
```bash
gh pr checks 238 --json

# Get specific check status
gh pr checks 238 --json | jq '.[] | select(.name=="Build") | .conclusion'
# Output: SUCCESS
```

---

## PR Review Operations

### List Reviews
```bash
gh pr view 238 --json reviews -q '.reviews[]|{author:.author.login,state:.state,body:.body}'
```

### Create Review Comment (API)
```bash
# Get HEAD commit SHA first
COMMIT_SHA=$(gh pr view 238 --json headRefOid -q '.headRefOid')

# Create pending review with line-level comment
gh api repos/owner/repo/pulls/238/reviews \
  -X POST \
  -f commit_id="$COMMIT_SHA" \
  -f body="Overall review summary" \
  -f comments[][path]="backend/connectors/stripe.rs" \
  -f comments[][line]=45 \
  -f comments[][side]="RIGHT" \
  -f comments[][body]="Consider proper error handling"
```

### Multiple Comments (JSON Input)
```bash
gh api repos/owner/repo/pulls/238/reviews \
  -X POST \
  --input - <<EOF
{
  "commit_id": "$COMMIT_SHA",
  "body": "Automated review",
  "comments": [
    {
      "path": "file1.rs",
      "line": 45,
      "side": "RIGHT",
      "body": "Issue 1"
    },
    {
      "path": "file2.rs",
      "line": 78,
      "side": "RIGHT",
      "body": "Issue 2"
    }
  ]
}
EOF
```

---

## Repository Detection

### From Git Remote
```bash
# Get origin URL
ORIGIN_URL=$(git remote get-url origin)

# Parse owner/repo from HTTPS URL
# Example: https://github.com/hyperswitch/connector-service.git
REPO=$(echo $ORIGIN_URL | sed 's/.*github\.com[:/]\(.*\)\.git/\1/')
echo $REPO
# Output: hyperswitch/connector-service

# Parse from SSH URL
# Example: git@github.com:hyperswitch/connector-service.git
REPO=$(echo $ORIGIN_URL | sed 's/.*:\(.*\)\.git/\1/')
```

### Robust Parsing
```bash
# Function to extract repo
parse_repo() {
  local url=$1
  # Remove .git suffix
  url=${url%.git}
  # Extract owner/repo
  if [[ $url =~ github\.com[:/](.+)$ ]]; then
    echo "${BASH_REMATCH[1]}"
  else
    echo "ERROR: Could not parse repository from $url" >&2
    return 1
  fi
}

REPO=$(parse_repo "$(git remote get-url origin)")
```

---

## Error Handling

### PR Not Found
```bash
gh pr view 999999 --repo owner/repo
# Error: pull request not found

# Check exit code
if ! gh pr view $PR_NUM --repo $REPO &>/dev/null; then
  echo "PR #$PR_NUM not found"
  exit 1
fi
```

### Authentication Errors
```bash
gh pr view 238
# Error: gh: To get started with GitHub CLI, please run: gh auth login

# Verify authentication
if ! gh auth status &>/dev/null; then
  echo "Not authenticated. Run: gh auth login"
  exit 1
fi
```

### Permission Errors
```bash
gh pr view 238 --repo private/repo
# Error: Resource not accessible by integration

# Check if user has read access
```

---

## Performance Optimization

### Minimize API Calls
```bash
# BAD - Multiple calls
TITLE=$(gh pr view 238 --json title -q '.title')
AUTHOR=$(gh pr view 238 --json author -q '.author.login')
STATE=$(gh pr view 238 --json state -q '.state')

# GOOD - Single call
PR_DATA=$(gh pr view 238 --json title,author,state)
TITLE=$(echo $PR_DATA | jq -r '.title')
AUTHOR=$(echo $PR_DATA | jq -r '.author.login')
STATE=$(echo $PR_DATA | jq -r '.state')
```

### Caching
```bash
# Cache PR data for multiple operations
PR_JSON=$(gh pr view 238 --json number,title,author,state,headRefName,headRefOid,changedFiles,additions,deletions)

# Reuse cached data
echo $PR_JSON | jq -r '.title'
echo $PR_JSON | jq -r '.author.login'
```

---

## Common Patterns

### Complete PR Analysis
```bash
#!/bin/bash

PR_NUM=$1
REPO=$2

# Fetch all metadata in one call
PR_DATA=$(gh pr view $PR_NUM --repo $REPO \
  --json number,title,author,state,headRefName,baseRefName,headRefOid,\
  createdAt,updatedAt,changedFiles,additions,deletions,body)

# Extract fields
TITLE=$(echo $PR_DATA | jq -r '.title')
AUTHOR=$(echo $PR_DATA | jq -r '.author.login')
FILES_CHANGED=$(echo $PR_DATA | jq -r '.changedFiles')
ADDITIONS=$(echo $PR_DATA | jq -r '.additions')
DELETIONS=$(echo $PR_DATA | jq -r '.deletions')
COMMIT_SHA=$(echo $PR_DATA | jq -r '.headRefOid')

# Get file list
FILES=$(gh pr diff $PR_NUM --repo $REPO --name-only)

# Get commit history
COMMITS=$(gh pr view $PR_NUM --repo $REPO \
  --json commits -q '.commits[]|{oid,message:.messageHeadline}')

echo "PR #$PR_NUM: $TITLE"
echo "Author: @$AUTHOR"
echo "Changed: $FILES_CHANGED files (+$ADDITIONS -$DELETIONS)"
echo "Files:"
echo "$FILES"
```

---

## Troubleshooting

### Issue: "gh: command not found"
**Solution**: Install GitHub CLI
```bash
# macOS
brew install gh

# Linux (Debian/Ubuntu)
sudo apt install gh

# Verify
gh --version
```

### Issue: Rate Limiting
```bash
# Check rate limit
gh api rate_limit

# Output shows remaining requests
```

### Issue: Large Diffs Timeout
```bash
# For very large PRs, fetch incrementally
gh pr diff 238 --name-only  # Fast, just file names
gh pr diff 238 -- specific/file.rs  # Fetch specific files
```

---

## Version History

- **1.0.0** (2025-12-09): Initial reference
  - Complete gh CLI command reference
  - JSON querying patterns
  - Error handling strategies
  - Performance optimization tips
