# GitHub API Patterns Reference

Comprehensive guide to using GitHub CLI (`gh`) for creating PR reviews with line-level comments.

## Prerequisites

### Installation

```bash
# macOS
brew install gh

# Ubuntu/Debian
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh
```

### Authentication

```bash
# Interactive login
gh auth login

# Check authentication status
gh auth status

# Expected output:
# github.com
#   ✓ Logged in to github.com as username
#   ✓ Git operations for github.com configured to use https protocol.
#   ✓ Token: ghp_************************************
```

## Creating Pending Reviews

### Single Comment Review

```bash
# Get commit SHA
COMMIT_SHA=$(gh pr view 42 --repo owner/repo --json headRefOid -q '.headRefOid')

# Create pending review with one comment
gh api repos/owner/repo/pulls/42/reviews \
  -X POST \
  -F commit_id="$COMMIT_SHA" \
  -F body="" \
  -F 'comments[][path]=src/api/handler.ts' \
  -F 'comments[][line]=25' \
  -F 'comments[][side]=RIGHT' \
  -F 'comments[][body]=**Warning**: Potential issue here'
```

### Multiple Comments Review

```bash
COMMIT_SHA=$(gh pr view 42 --repo owner/repo --json headRefOid -q '.headRefOid')

gh api repos/owner/repo/pulls/42/reviews \
  -X POST \
  -F commit_id="$COMMIT_SHA" \
  -F body="" \
  -F 'comments[][path]=src/api/handler.ts' \
  -F 'comments[][line]=25' \
  -F 'comments[][side]=RIGHT' \
  -F 'comments[][body]=**Critical**: SQL injection vulnerability' \
  -F 'comments[][path]=src/api/handler.ts' \
  -F 'comments[][line]=45' \
  -F 'comments[][side]=RIGHT' \
  -F 'comments[][body]=**Warning**: Empty catch block' \
  -F 'comments[][path]=src/utils/crypto.ts' \
  -F 'comments[][line]=67' \
  -F 'comments[][side]=RIGHT' \
  -F 'comments[][body]=**Suggestion**: Consider using AES-256'
```

### JSON Body Alternative

For complex comments with special characters:

```bash
COMMIT_SHA=$(gh pr view 42 --repo owner/repo --json headRefOid -q '.headRefOid')

gh api repos/owner/repo/pulls/42/reviews \
  -X POST \
  --input - <<EOF
{
  "commit_id": "$COMMIT_SHA",
  "body": "",
  "comments": [
    {
      "path": "src/api/handler.ts",
      "line": 25,
      "side": "RIGHT",
      "body": "## CRITICAL: Security\n\n**Issue**: SQL injection"
    },
    {
      "path": "src/utils/crypto.ts",
      "line": 67,
      "side": "RIGHT",
      "body": "## WARNING: Encryption\n\n**Issue**: Weak algorithm"
    }
  ]
}
EOF
```

## Line Number Parameters

### Understanding `line` vs `position` (Deprecated)

**IMPORTANT**: The `position` parameter is deprecated. Always use `line` and `side`.

| Parameter | Description | Status |
|-----------|-------------|--------|
| `position` | Relative position in diff | **DEPRECATED** |
| `line` | Actual line number in file | **USE THIS** |
| `side` | Which side of diff (`LEFT` or `RIGHT`) | **USE THIS** |

### Line and Side Usage

```json
{
  "path": "src/api/handler.ts",
  "line": 25,                    // Line number in the file
  "side": "RIGHT",               // RIGHT = new file version
  "body": "Comment text"
}
```

**Side values**:
- `RIGHT`: Comment on new file (added/modified lines) - **Most common**
- `LEFT`: Comment on old file (deleted lines) - Rarely used

### Example: Commenting on Line 25

If `src/api/handler.ts` has this diff:

```diff
@@ -20,10 +20,15 @@ export async function handleRequest(req, res) {
   const userId = req.params.id;

   // Fetch user from database
-  const user = await db.query(`SELECT * FROM users WHERE id = ${userId}`);
+  const query = `SELECT * FROM users WHERE id = ${userId}`;
+  const user = await db.query(query);
+
+  if (!user) {
+    return res.status(404).json({ error: 'User not found' });
+  }

   return res.json(user);
 }
```

To comment on line 23 (the query line):

```bash
gh api repos/owner/repo/pulls/42/reviews \
  -X POST \
  -F commit_id="$COMMIT_SHA" \
  -F 'comments[][path]=src/api/handler.ts' \
  -F 'comments[][line]=23' \
  -F 'comments[][side]=RIGHT' \
  -F 'comments[][body]=SQL injection vulnerability'
```

## Multi-Line Comment Ranges

For comments spanning multiple lines:

```json
{
  "path": "src/api/handler.ts",
  "start_line": 45,           // First line of range
  "start_side": "RIGHT",      // Side for start line
  "line": 50,                 // Last line of range
  "side": "RIGHT",            // Side for end line
  "body": "This entire block needs refactoring"
}
```

Example with `gh api`:

```bash
gh api repos/owner/repo/pulls/42/reviews \
  -X POST \
  -F commit_id="$COMMIT_SHA" \
  -F 'comments[][path]=src/api/handler.ts' \
  -F 'comments[][start_line]=45' \
  -F 'comments[][start_side]=RIGHT' \
  -F 'comments[][line]=50' \
  -F 'comments[][side]=RIGHT' \
  -F 'comments[][body]=Refactor this function'
```

## Comment Body Formatting

### Markdown Support

GitHub review comments support full Markdown:

```markdown
## Header

**Bold** and *italic* text

- Bullet points
- Work too

`Inline code` and:

```javascript
// Code blocks with syntax highlighting
const example = "work perfectly";
```

> Blockquotes
> for quoting code

[Links](https://example.com) are supported
```

### Special Characters

When using `-F` flags, escape special characters:

```bash
# Quotes
-F 'comments[][body]=Use "parameterized" queries'

# Newlines (use $'...')
-F $'comments[][body]=Line 1\nLine 2\nLine 3'

# Or use heredoc with JSON
```

### Emoji Support

```bash
-F 'comments[][body]=**Warning** - Performance issue'
```

## Review States

| State | Description | How to Create |
|-------|-------------|---------------|
| `PENDING` | Draft, not visible to others | Omit `event` parameter |
| `COMMENT` | Visible comment, no approval | `-F event=COMMENT` |
| `APPROVE` | Approve the PR | `-F event=APPROVE` |
| `REQUEST_CHANGES` | Request changes | `-F event=REQUEST_CHANGES` |

### Creating Different Review Types

```bash
# Pending (default - recommended for initial creation)
gh api repos/owner/repo/pulls/42/reviews \
  -X POST \
  -F commit_id="$COMMIT_SHA" \
  -F body="" \
  -F 'comments[][path]=file.ts' \
  -F 'comments[][line]=25' \
  -F 'comments[][side]=RIGHT' \
  -F 'comments[][body]=Comment'

# Approve with comment
gh api repos/owner/repo/pulls/42/reviews \
  -X POST \
  -F commit_id="$COMMIT_SHA" \
  -F event=APPROVE \
  -F body="LGTM!" \
  -F 'comments[][path]=file.ts' \
  -F 'comments[][line]=25' \
  -F 'comments[][side]=RIGHT' \
  -F 'comments[][body]=Minor suggestion'

# Request changes
gh api repos/owner/repo/pulls/42/reviews \
  -X POST \
  -F commit_id="$COMMIT_SHA" \
  -F event=REQUEST_CHANGES \
  -F body="Please fix the security issues" \
  -F 'comments[][path]=file.ts' \
  -F 'comments[][line]=25' \
  -F 'comments[][side]=RIGHT' \
  -F 'comments[][body]=Critical issue'
```

## Error Handling

### 422 "Line could not be resolved"

**Cause**: Line number doesn't exist in the file at that commit.

**Solution**:
1. Verify line number in the PR diff: `gh pr diff 42`
2. Ensure using `line` (not `position`)
3. Check file path is correct (relative from repo root)
4. Verify the line is in the NEW file (RIGHT side)

### 422 "Review cannot be submitted"

**Cause**: Trying to submit a review that has no comments or body.

**Solution**: Always include at least one comment or a body.

### 403 "Resource not accessible"

**Cause**: Insufficient permissions or authentication.

**Solution**:
```bash
# Re-authenticate
gh auth logout
gh auth login

# Check permissions
gh auth status
```

### 409 "Pending review already exists"

**Cause**: You can only have one pending review per PR.

**Solution**: Delete existing pending review first:

```bash
# List reviews
gh api repos/owner/repo/pulls/42/reviews

# Delete pending review (replace REVIEW_ID)
gh api repos/owner/repo/pulls/42/reviews/REVIEW_ID -X DELETE
```

## Complete Example Script

```bash
#!/bin/bash
set -e

# Configuration
OWNER="owner"
REPO="repo"
PR_NUMBER="42"

# Get commit SHA
echo "Fetching PR HEAD commit..."
COMMIT_SHA=$(gh pr view "$PR_NUMBER" --repo "$OWNER/$REPO" --json headRefOid -q '.headRefOid')
echo "Commit SHA: $COMMIT_SHA"

# Create review with multiple comments
echo "Creating pending review..."
RESPONSE=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/reviews" \
  -X POST \
  -F commit_id="$COMMIT_SHA" \
  -F body="" \
  -F 'comments[][path]=src/api/handler.ts' \
  -F 'comments[][line]=25' \
  -F 'comments[][side]=RIGHT' \
  -F 'comments[][body]=**Critical**: SQL injection vulnerability' \
  -F 'comments[][path]=src/utils/crypto.ts' \
  -F 'comments[][line]=67' \
  -F 'comments[][side]=RIGHT' \
  -F 'comments[][body]=**Warning**: Consider stronger encryption')

# Extract review ID
REVIEW_ID=$(echo "$RESPONSE" | jq -r '.id')
echo "Created pending review: $REVIEW_ID"

# Output URL
echo "View in GitHub: https://github.com/$OWNER/$REPO/pull/$PR_NUMBER/files"
echo "Comments are PENDING - submit manually in GitHub UI"
```

## Best Practices

1. **Always create PENDING reviews first**
   - Allows manual review before publishing
   - Can edit/delete comments before submission

2. **Batch comments into single review**
   - More efficient than individual comments
   - Better user experience

3. **Validate line numbers before API call**
   - Parse diff to extract valid line ranges
   - Skip invalid lines rather than failing

4. **Use descriptive commit SHA**
   - Always get fresh SHA from PR
   - Don't hardcode commit SHAs

5. **Handle API errors gracefully**
   - Retry on transient failures
   - Report skipped comments to user

## Useful Commands Reference

```bash
# Get PR info
gh pr view 42 --repo owner/repo --json number,title,author,state,headRefOid

# Get PR diff
gh pr diff 42 --repo owner/repo

# Get changed files
gh pr diff 42 --repo owner/repo --name-only

# List reviews on PR
gh api repos/owner/repo/pulls/42/reviews

# Get specific review
gh api repos/owner/repo/pulls/42/reviews/REVIEW_ID

# Delete pending review
gh api repos/owner/repo/pulls/42/reviews/REVIEW_ID -X DELETE

# Submit pending review
gh api repos/owner/repo/pulls/42/reviews/REVIEW_ID/events \
  -X POST \
  -F event=COMMENT
```
