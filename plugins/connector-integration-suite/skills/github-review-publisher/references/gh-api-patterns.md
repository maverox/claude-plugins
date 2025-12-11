# GitHub API Patterns Reference

**Version**: 1.0.0
**Purpose**: GitHub API usage patterns for creating and managing PR reviews

---

## Prerequisites

### gh CLI Installation

```bash
# Check installation
gh --version

# Install if needed
brew install gh  # macOS
sudo apt install gh  # Linux
```

### Authentication

```bash
# Login interactively
gh auth login

# Verify authentication
gh auth status

# Should show:
# ✓ Logged in to github.com as username
```

---

## Creating Pending Reviews

### Basic Concept

**Pending Reviews**:
- Created via API but NOT posted publicly
- Visible only to you in GitHub UI
- Can be edited, modified, or discarded
- Must be manually submitted to post

**To create pending review**: Omit the `event` parameter

---

### Step 1: Get HEAD Commit SHA

**Required** for all reviews:

```bash
# Get commit SHA
COMMIT_SHA=$(gh pr view {pr-number} --repo {owner}/{repo} --json headRefOid -q '.headRefOid')

echo $COMMIT_SHA
# Output: abc123def456789...
```

**Why needed**: Reviews must be attached to specific commit to track line numbers correctly

---

### Step 2: Create Review with Comments

#### **Single Comment** (Simple)

```bash
gh api repos/{owner}/{repo}/pulls/{pr-number}/reviews \
  -X POST \
  -f commit_id="$COMMIT_SHA" \
  -f body="Overall review summary (optional)" \
  -f comments[][path]="backend/connectors/stripe.rs" \
  -f comments[][line]=45 \
  -f comments[][side]="RIGHT" \
  -f comments[][body]="Review comment text"
```

**Field Explanations**:
- `commit_id`: HEAD commit SHA (required)
- `body`: Overall review summary (optional)
- `comments[][path]`: File path relative to repo root
- `comments[][line]`: Line number in NEW file version
- `comments[][side]`: "RIGHT" for new code, "LEFT" for old code
- `comments[][body]`: Comment text (supports Markdown)

---

#### **Multiple Comments** (Recommended)

For multiple comments, use JSON input:

```bash
gh api repos/{owner}/{repo}/pulls/{pr-number}/reviews \
  -X POST \
  --input - <<EOF
{
  "commit_id": "$COMMIT_SHA",
  "body": "Automated code review completed. ${COMMENT_COUNT} issues found.",
  "comments": [
    {
      "path": "backend/connector-integration/src/connectors/stripe.rs",
      "line": 25,
      "side": "RIGHT",
      "body": "🔴 **Critical** - Type Safety\n\nUsing RouterData instead of RouterDataV2..."
    },
    {
      "path": "backend/connector-integration/src/connectors/stripe.rs",
      "line": 45,
      "side": "RIGHT",
      "body": "🟡 **Important** - Error Handling\n\nMissing error propagation..."
    },
    {
      "path": "backend/connector-integration/src/connectors/stripe/transformers.rs",
      "line": 67,
      "side": "RIGHT",
      "body": "🟢 **Suggestion** - Documentation\n\nConsider adding doc comment..."
    }
  ]
}
EOF
```

---

### Step 3: Verify Review Created

```bash
# Get review ID from response
REVIEW_ID=$(gh api repos/{owner}/{repo}/pulls/{pr-number}/reviews \
  --jq '.[-1].id')

echo "Review created with ID: $REVIEW_ID"
```

---

## Line Number Calculation

### Understanding Line Numbers

**IMPORTANT**: Use actual file line numbers, NOT diff positions

**Correct** ✅:
```json
{
  "line": 45,  // Line 45 in the file
  "side": "RIGHT"
}
```

**Wrong** ❌:
```json
{
  "position": 12  // 12th line in the diff (DON'T USE)
}
```

---

### Finding Line Numbers

#### **Method 1: From Diff with grep**

```bash
# Find line number for specific code
gh pr diff {pr-number} | grep -n "RouterData"

# Output: 145:use hyperswitch_domain_models::RouterData;
#         ^^^--- This is the diff line, not file line
```

#### **Method 2: From File Content**

```bash
# View file at specific commit
gh api repos/{owner}/{repo}/contents/{file-path}?ref={commit-sha} \
  --jq '.content' | base64 -d | grep -n "RouterData"

# Output: 25:use hyperswitch_domain_models::RouterData;
#         ^^--- This is the file line number (CORRECT)
```

#### **Method 3: From Hunk Headers**

From diff output:
```diff
@@ -10,7 +20,8 @@ fn example() {
```

- Old file: starts at line 10
- New file: starts at line 20

Count from there:
```diff
@@ -10,7 +20,8 @@
     context line    // line 20
     context line    // line 21
+    added line      // line 22 ← This is the line number to use
     context line    // line 23
```

---

## Multi-Line Comment Ranges

### Commenting on Multiple Lines

To comment on lines 45-50:

```json
{
  "path": "file.rs",
  "start_line": 45,
  "start_side": "RIGHT",
  "line": 50,
  "side": "RIGHT",
  "body": "Comment spanning lines 45-50"
}
```

**Use Cases**:
- Function spans multiple lines
- Multiple related issues in block
- Complex refactoring suggestion

---

## Comment Body Formatting

### Markdown Support

GitHub comments support **full Markdown**:

```markdown
🔴 **Critical** - Type Safety

Using deprecated RouterData breaks compatibility.

**Current**:
```rust
use RouterData;
```

**Suggested Fix**:
```rust
use RouterDataV2;
```

**Reference**: [UCS Guide](link)
```

---

### Special Characters

**Escape quotes** in JSON:

```json
{
  "body": "Use the \\\"?\\\" operator instead of unwrap()"
}
```

**Or use heredoc** to avoid escaping:

```bash
COMMENT_BODY=$(cat <<'COMMENT'
🔴 **Critical** - Type Safety

Use "RouterDataV2" instead of "RouterData"
COMMENT
)

# Use in JSON
jq -n --arg body "$COMMENT_BODY" '{
  path: "file.rs",
  line: 45,
  side: "RIGHT",
  body: $body
}'
```

---

### Emoji in Comments

**Use Unicode emojis** directly:

```json
{
  "body": "🔴 Critical issue\n🟡 Warning\n🟢 Suggestion"
}
```

**Common review emojis**:
- 🔴 Critical
- 🟡 Warning/Important
- 🟢 Suggestion
- ✅ Approved
- ❌ Blocked
- ⚠️ Caution
- 💡 Tip

---

## Review States

### Pending Review (Default)

**Create without posting**:
```json
{
  "commit_id": "...",
  "body": "...",
  "comments": [...]
  // NO "event" parameter = PENDING
}
```

**User can**:
- View in GitHub UI
- Edit comments
- Delete comments
- Add more comments
- Submit later

---

### Submitting Pending Review

**Later, to submit**:

```bash
# Get pending review ID
REVIEW_ID=$(gh api repos/{owner}/{repo}/pulls/{pr-number}/reviews \
  --jq '.[] | select(.state=="PENDING") | .id')

# Submit with event type
gh api repos/{owner}/{repo}/pulls/{pr-number}/reviews/${REVIEW_ID}/events \
  -X POST \
  -f event="COMMENT"  # or "APPROVE" or "REQUEST_CHANGES"
```

**Event Types**:
- `COMMENT` - General comments
- `APPROVE` - Approve PR
- `REQUEST_CHANGES` - Request changes before merge

---

## Error Handling

### Invalid Line Number

**Error**:
```json
{
  "message": "Validation Failed",
  "errors": [{
    "resource": "PullRequestReviewComment",
    "field": "line",
    "code": "invalid"
  }]
}
```

**Causes**:
- Line number doesn't exist in file
- Line number is in wrong side (LEFT vs RIGHT)
- File was deleted/renamed

**Solution**:
```bash
# Verify line exists in new file
gh api repos/{owner}/{repo}/contents/{file-path}?ref={head-sha} \
  --jq '.content' | base64 -d | wc -l

# Should be >= line number
```

---

### Invalid File Path

**Error**:
```json
{
  "message": "Not Found",
  "errors": [{
    "resource": "Blob",
    "field": "sha",
    "code": "not_found"
  }]
}
```

**Causes**:
- File path incorrect (typo, wrong directory)
- File doesn't exist in PR
- Path not relative to repo root

**Solution**:
```bash
# List all files in PR
gh pr diff {pr-number} --name-only

# Verify path matches exactly
```

---

### Authentication Errors

**Error**:
```
HTTP 401: Bad credentials
```

**Solution**:
```bash
# Re-authenticate
gh auth logout
gh auth login

# Verify
gh auth status
```

---

### Permission Errors

**Error**:
```
HTTP 403: Resource not accessible by integration
```

**Causes**:
- No write access to repository
- Token lacks review permissions

**Solution**: Ensure you have write/review permissions on the repo

---

## Complete Example Script

```bash
#!/bin/bash

# Configuration
PR_NUMBER=$1
REPO="hyperswitch/connector-service"

# Get commit SHA
echo "Fetching PR data..."
COMMIT_SHA=$(gh pr view $PR_NUMBER --repo $REPO --json headRefOid -q '.headRefOid')

if [ -z "$COMMIT_SHA" ]; then
  echo "Error: Could not get commit SHA"
  exit 1
fi

echo "Commit SHA: $COMMIT_SHA"

# Prepare review comments (from issues)
REVIEW_JSON=$(cat <<EOF
{
  "commit_id": "$COMMIT_SHA",
  "body": "Automated code review completed. 3 issues found.",
  "comments": [
    {
      "path": "backend/connector-integration/src/connectors/stripe.rs",
      "line": 25,
      "side": "RIGHT",
      "body": "🔴 **Critical** - Type Safety\n\nUsing RouterData instead of RouterDataV2 breaks UCS compatibility.\n\n**Current**:\n\`\`\`rust\nuse hyperswitch_domain_models::RouterData;\n\`\`\`\n\n**Suggested Fix**:\n\`\`\`rust\nuse domain_types::router_data_v2::RouterDataV2;\n\`\`\`"
    },
    {
      "path": "backend/connector-integration/src/connectors/stripe.rs",
      "line": 45,
      "side": "RIGHT",
      "body": "🟡 **Important** - Error Handling\n\nMissing error propagation. Use \`?\` operator instead of \`unwrap()\`."
    },
    {
      "path": "backend/connector-integration/src/connectors/stripe/transformers.rs",
      "line": 120,
      "side": "RIGHT",
      "body": "🟢 **Suggestion** - Documentation\n\nConsider adding a doc comment explaining this transformation."
    }
  ]
}
EOF
)

# Create pending review
echo "Creating pending review..."
RESPONSE=$(gh api repos/$REPO/pulls/$PR_NUMBER/reviews \
  -X POST \
  --input - <<< "$REVIEW_JSON")

REVIEW_ID=$(echo $RESPONSE | jq -r '.id')

if [ -z "$REVIEW_ID" ] || [ "$REVIEW_ID" == "null" ]; then
  echo "Error: Failed to create review"
  echo "Response: $RESPONSE"
  exit 1
fi

echo "✅ Review created successfully!"
echo "Review ID: $REVIEW_ID"
echo "Status: PENDING"
echo ""
echo "Next steps:"
echo "1. Go to: https://github.com/$REPO/pull/$PR_NUMBER/files"
echo "2. Review and edit comments in GitHub UI"
echo "3. Submit review when ready"
```

---

## Best Practices

### 1. Always Use Pending Reviews

**Why**: Gives you chance to review before posting

```json
// Good ✅
{
  "commit_id": "...",
  "comments": [...]
  // No event = pending
}

// Risky ❌
{
  "commit_id": "...",
  "comments": [...],
  "event": "COMMENT"  // Posts immediately
}
```

---

### 2. Batch All Comments

**Create single review** with all comments:

```json
{
  "comments": [
    // All comments here
  ]
}
```

**Not** multiple reviews with one comment each

---

### 3. Validate Line Numbers

**Before creating review**:

```bash
# Check file exists and line count
FILE_LINES=$(gh pr diff $PR --name-only | grep "$FILE" | wc -l)

if [ $FILE_LINES -eq 0 ]; then
  echo "Error: File not in PR"
  exit 1
fi
```

---

### 4. Handle Errors Gracefully

```bash
# Attempt to create review
if ! RESPONSE=$(gh api repos/$REPO/pulls/$PR/reviews ... 2>&1); then
  echo "Error creating review: $RESPONSE"

  # Parse error
  ERROR_MSG=$(echo $RESPONSE | jq -r '.message')
  echo "API Error: $ERROR_MSG"

  # Take corrective action
  exit 1
fi
```

---

## Version History

- **1.0.0** (2025-12-09): Initial GitHub API patterns
  - Pending review creation
  - Line number calculation
  - Multi-line comments
  - Error handling
  - Complete examples
  - Best practices
