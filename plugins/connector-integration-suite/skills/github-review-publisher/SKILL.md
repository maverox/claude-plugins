---
name: github-review-publisher
description: |
  Create and format GitHub PR review comments with line-level precision. Generates structured, severity-categorized comments and publishes them as pending reviews for manual approval. Auto-activates for: "create review comments", "publish review", "post review to GitHub", "create pending review".
allowed-tools: Bash, Read, Write
version: 1.0.0
---

# GitHub Review Publisher Skill

## Overview

This skill creates professional, well-formatted GitHub PR review comments from identified code issues. It generates line-level comments with proper severity indicators, code examples, and suggested fixes, then publishes them as a pending GitHub review for manual approval before posting.

## When to Use This Skill

This skill **auto-activates** when users request:
- "Create review comments for PR #238"
- "Publish review to GitHub"
- "Post review comments"
- "Create pending review"
- "Generate GitHub review"

The skill can also be invoked as the final step in `/pr-review` workflow to publish review findings.

## Input Context

The skill expects review data from upstream skills:

1. **From code-quality-review**:
   ```yaml
   issues:
     - severity: CRITICAL
       category: Type Safety
       file: backend/connectors/stripe.rs
       line: 45
       issue: "Using RouterData instead of RouterDataV2"
       current_code: "use RouterData;"
       suggested_fix: "use RouterDataV2;"
   ```

2. **From connector-integration-validator**:
   ```yaml
   validation_issues:
     - severity: WARNING
       file: backend/connectors/stripe/transformers.rs
       line: 120
       issue: "Status mapping incorrect"
       suggested_fix: "..."
   ```

3. **Direct input** (for standalone use):
   ```
   User: "Create review for these issues: [issue list]"
   ```

## Process

### Step 1: Collect Review Data

Gather all issues from upstream skills:

**From Multiple Skills**:
- code-quality-review → code quality issues
- connector-integration-validator → connector-specific issues

**Combine and Deduplicate**:
- Merge issues from all sources
- Remove duplicates (same file + line)
- Sort by severity (Critical → Warning → Suggestion)

---

### Step 2: Format Review Comments

Transform each issue into a GitHub-compatible review comment:

#### **Comment Structure**

```markdown
{severity_emoji} **{severity}** - {category}

{issue_description}

**Current**:
```{language}
{current_code}
```

**Suggested Fix**:
```{language}
{suggested_fix}
```

{additional_context}
```

#### **Severity Indicators**

| Severity | Emoji | Label | Priority |
|----------|-------|-------|----------|
| Critical | 🔴 | Critical | P0 |
| Warning | 🟡 | Important | P1 |
| Suggestion | 🟢 | Suggestion | P2 |

#### **Example Formatted Comment**

```markdown
🔴 **Critical** - Type Safety

Using deprecated RouterData instead of RouterDataV2 breaks UCS architecture compatibility.

**Current**:
```rust
use hyperswitch_domain_models::RouterData;
```

**Suggested Fix**:
```rust
use domain_types::router_data_v2::RouterDataV2;
```

**Impact**: This prevents the connector from working with the UCS architecture.
```

---

### Step 2.5: Validate Line Numbers Against PR Diff

**Purpose**: Ensure all line numbers exist in the NEW file before calling GitHub API to prevent "422 Line could not be resolved" errors.

#### **Process**:

#### A. Normalize Input (Backward Compatibility)

Handle both old and new issue formats:

```bash
# Map old 'line' field to 'line_number'
normalize_issue() {
  local issue="$1"

  # Backward compatibility: 'line' → 'line_number'
  if grep -q "^  line:" <<< "$issue" && ! grep -q "^  line_number:" <<< "$issue"; then
    echo "⚠️  Warning: Old format detected (using 'line' instead of 'line_number'), normalizing..."
    issue=$(echo "$issue" | sed 's/^  line:/  line_number:/')
  fi

  # Default line_reference to NEW_FILE if missing
  if ! grep -q "^  line_reference:" <<< "$issue"; then
    echo "⚠️  Warning: Missing 'line_reference', assuming NEW_FILE"
    issue+=$'\n  line_reference: "NEW_FILE"'
  fi

  # Validate line_reference is NEW_FILE
  line_ref=$(echo "$issue" | grep "line_reference:" | cut -d: -f2 | xargs | tr -d '"')
  if [[ "$line_ref" != "NEW_FILE" ]]; then
    echo "❌ Error: Unsupported line_reference: $line_ref (only NEW_FILE supported)"
    return 1
  fi

  echo "$issue"
}
```

#### B. Fetch PR Diff and Extract Valid Ranges

```bash
# 1. Fetch PR diff
gh pr diff {pr-number} --repo {owner}/{repo} > /tmp/pr_diff.txt

# 2. Parse valid line ranges per file
declare -A FILE_RANGES

while IFS= read -r line; do
  # Detect file path
  if [[ "$line" =~ ^\+\+\+\ b/(.+)$ ]]; then
    current_file="${BASH_REMATCH[1]}"
    FILE_RANGES["$current_file"]=""
  fi

  # Parse hunk header: @@ -old +new @@
  if [[ "$line" =~ ^@@\ -[0-9]+,[0-9]+\ \+([0-9]+),([0-9]+) ]]; then
    new_start="${BASH_REMATCH[1]}"
    new_count="${BASH_REMATCH[2]}"
    new_end=$((new_start + new_count - 1))

    # Append range
    if [[ -z "${FILE_RANGES[$current_file]}" ]]; then
      FILE_RANGES["$current_file"]="$new_start-$new_end"
    else
      FILE_RANGES["$current_file"]="${FILE_RANGES[$current_file]},$new_start-$new_end"
    fi
  fi
done < /tmp/pr_diff.txt
```

#### C. Validate Each Issue

```bash
# Validate line number is in valid ranges
is_line_valid() {
  local file="$1"
  local line_num="$2"
  local ranges="${FILE_RANGES[$file]}"

  # File not in PR
  if [[ -z "$ranges" ]]; then
    echo "FILE_NOT_IN_PR"
    return 1
  fi

  # Check each range
  IFS=',' read -ra RANGE_ARRAY <<< "$ranges"
  for range in "${RANGE_ARRAY[@]}"; do
    IFS='-' read -r start end <<< "$range"
    if (( line_num >= start && line_num <= end )); then
      echo "VALID"
      return 0
    fi
  done

  echo "LINE_NOT_IN_RANGE:$ranges"
  return 1
}

# Classify issues
VALID_ISSUES=()
SKIPPED_ISSUES=()

for issue in "${ALL_ISSUES[@]}"; do
  file=$(echo "$issue" | grep "file:" | cut -d: -f2- | xargs)
  line_num=$(echo "$issue" | grep "line_number:" | cut -d: -f2 | xargs)

  result=$(is_line_valid "$file" "$line_num")

  if [[ "$result" == "VALID" ]]; then
    VALID_ISSUES+=("$issue")
  else
    SKIPPED_ISSUES+=("$file:$line_num:$result")
  fi
done
```

**Reference**: See `.claude/skills/github-review-publisher/references/line-validation.md` for complete validation algorithm and edge cases.

#### D. Proceed with Valid Issues Only

- Use `VALID_ISSUES` array for Step 3 (create review)
- Save `SKIPPED_ISSUES` for reporting in Step 4

**Benefit**: Eliminates "422 Line could not be resolved" errors entirely.

---

### Step 3: Create Pending Review via gh CLI

**CRITICAL**: GitHub API has deprecated the `position` parameter. Use `line` and `side` instead.

#### **Get HEAD Commit SHA**

```bash
COMMIT_SHA=$(gh pr view {pr-number} --repo {owner}/{repo} --json headRefOid -q '.headRefOid')
```

#### **Map File Lines to Diff Lines**

**Important**: The `line` parameter expects the **actual line number in the new file**, NOT a diff position.

**Parameters**:
- `line`: The line number in the new version of the file (RIGHT side)
- `side`: Always use `"RIGHT"` for new file content
- `path`: Relative path to the file from repository root

**Example**: If you want to comment on line 22 of `backend/connector-integration/src/connectors/revolut.rs`:
```json
{
  "path": "backend/connector-integration/src/connectors/revolut.rs",
  "line": 22,
  "side": "RIGHT",
  "body": "Comment text here"
}
```

#### **Create Pending Review with Inline Comments**

**CRITICAL CONSTRAINTS**:
1. Can only have ONE pending review per user per PR
2. Must use GitHub API `/pulls/{pr}/reviews` endpoint
3. Use `line` parameter (not deprecated `position`)
4. Do NOT include `event` parameter (creates PENDING state)
5. Leave `body` empty for inline-only reviews (no general comment)

**Working Method: GitHub API with Form Fields**

```bash
# Get commit SHA
COMMIT_SHA=$(gh pr view {pr-number} --repo {owner}/{repo} --json headRefOid -q '.headRefOid')

# Create pending review with multiple inline comments
gh api repos/{owner}/{repo}/pulls/{pr-number}/reviews \
  -X POST \
  -F commit_id="$COMMIT_SHA" \
  -F body="" \
  -F 'comments[][path]=backend/connectors/revolut.rs' \
  -F 'comments[][line]=22' \
  -F 'comments[][side]=RIGHT' \
  -F 'comments[][body]=🟡 **Warning** - Issue description here' \
  -F 'comments[][path]=backend/connectors/revolut/transformers.rs' \
  -F 'comments[][line]=1255' \
  -F 'comments[][side]=RIGHT' \
  -F 'comments[][body]=🟢 **Suggestion** - Another comment'
```

**Key Parameters**:
- `commit_id`: HEAD commit SHA from PR
- `body`: Empty string for inline-only (or brief summary)
- `comments[]`: Array of comment objects
  - `path`: Relative file path from repo root
  - `line`: Actual line number in NEW file
  - `side`: Always `"RIGHT"` for new content
  - `body`: Formatted comment text (markdown supported)

**IMPORTANT NOTES**:
- Start with fewer comments and add more if successful
- Validate ALL line numbers exist in the new file
- If you get 422 "Line could not be resolved", a line number is invalid
- Only ONE pending review allowed - delete existing before creating new
- Comments are NOT posted publicly until manually submitted in GitHub UI

#### **Troubleshooting 422 "Line could not be resolved"**

This error occurs when:
1. Line number doesn't exist in the NEW file version
2. File path is incorrect
3. Using `position` instead of `line`

**Solution**:
- Verify line numbers exist in the PR's changed files
- Use `gh pr diff {pr-number}` to see actual line numbers
- Ensure file paths match exactly (relative from repo root)

---

### Step 4: Generate Review Summary

Create a comprehensive summary for display in chat:

#### **Summary Structure**

```markdown
# 📋 PR Review Complete: PR #{number}

## PR Information
- **Repository**: {owner}/{repo}
- **Title**: {pr_title}
- **Author**: @{author}
- **Files Changed**: {file_count}

## Review Statistics
- **Total Pending Comments**: {total_comments}
  - 🔴 Critical: {critical_count}
  - 🟡 Important: {warning_count}
  - 🟢 Suggestions: {suggestion_count}

## Connector Integration Validation (if applicable)
- **API Conformance**: ✅ Pass
- **Authentication Patterns**: ✅ Pass
- **Payment Flow Implementation**: ⚠️  1 warning
- **Amount Converters**: ✅ Pass
- **Status Mapping**: ⚠️  1 warning

## Summary
{overall_assessment}

## Line-Level Comments Created (Pending Approval)

⚠️  All comments below have been created as PENDING and are attached to specific lines

### 📄 {file_path_1}

**Line {line}** • {severity_emoji} {severity} - {category}
> {issue_description}
> ```{language}
> {suggested_fix}
> ```

[... all comments grouped by file ...]

---

✅ **{total_comments} Pending Review Comments Created**

**Next Steps:**
1. Go to GitHub PR: {pr_url}/files
2. You will see pending comments on specific lines
3. Manually review and approve/edit/delete each comment
4. Submit your review when ready

⚠️  **Comments are NOT posted publicly yet** - they're pending your manual approval in GitHub UI.
```

#### **Skipped Comments Report** (if any)

If any comments were skipped during validation, include this section:

```markdown
---

⚠️  **{skipped_count} Comment(s) Skipped Due to Invalid Line Numbers**

**Skipped Comments**:

1. **File**: `{file_path}`
   **Line**: {line_number}
   **Line Reference**: {line_reference}
   **Reason**: {skip_reason}
   **Valid Lines in PR**: {valid_ranges}
   **Issue**: {issue_description}
   **Action**: Verify line number in GitHub UI or re-run upstream skill

[Repeat for each skipped comment]

**Note**: These comments were not included in the pending review to avoid API errors.

**How to Fix**:
- View file at HEAD commit: https://github.com/{owner}/{repo}/blob/{commit_sha}/{file_path}
- Verify the correct line number for each issue
- Add comments manually in GitHub UI if needed
- Or fix line number extraction in upstream skills (code-quality-review, connector-integration-validator)
```

**Example Skipped Comment Report**:

```markdown
⚠️  **1 Comment Skipped Due to Invalid Line Numbers**

**Skipped Comments**:

1. **File**: `backend/connector-integration/src/connectors/revolut.rs`
   **Line**: 999
   **Line Reference**: NEW_FILE
   **Reason**: Line 999 does not exist in NEW file (file has 738 lines)
   **Valid Lines in PR**: 1-738
   **Issue**: Unnecessary clone operation
   **Action**: Correct line number is likely 617 (based on code pattern)

**How to Fix**:
- View file: https://github.com/juspay/connector-service/blob/4bd7429b1cc5c38b072514eff3d0df9d7ba85e83/backend/connector-integration/src/connectors/revolut.rs
- Search for the code pattern: `let attempt_status = code.clone().into();`
- Find actual line number (617) and add comment manually in GitHub UI
```

---

## Output

The skill produces:

### 1. GitHub Pending Review

**Created via gh CLI**:
- Review ID (for later reference)
- Pending status (not posted)
- Line-level comments attached

**User can**:
- View in GitHub UI
- Edit each comment
- Delete unwanted comments
- Add more comments
- Submit review when ready

---

### 2. Chat Summary

**Displayed to user**:
- Complete review statistics
- All comments listed (for reference)
- Next steps instructions
- GitHub PR URL

---

### 3. Review Metadata (Optional)

**Saved to file** (for tracking):
```yaml
review_metadata:
  pr_number: 238
  repository: hyperswitch/connector-service
  review_id: 123456789
  status: PENDING
  created_at: 2025-12-09T16:30:00Z
  comments_count: 12
  severity_breakdown:
    critical: 2
    warnings: 5
    suggestions: 5
```

---

## Integration with Other Skills

### Upstream Skills (Providers)

**1. pr-analysis**
- Provides PR metadata (number, title, author)
- Supplies file paths for comments
- Provides commit SHA

**2. code-quality-review**
- Provides code quality issues
- Categorized by severity
- With line numbers and suggestions

**3. connector-integration-validator**
- Provides connector-specific issues
- API conformance results
- UCS compliance findings

---

### Standalone Usage

Can be used independently for:
- Publishing review from custom issue list
- Creating follow-up reviews
- Adding comments to existing reviews
- Re-reviewing after fixes

---

## Reference Files

### 1. `comment-formatting.md`
Comment structure guidelines:
- Markdown formatting best practices
- Severity indicator usage
- Code block formatting
- Suggested fix templates

### 2. `gh-api-patterns.md`
GitHub API usage patterns:
- Creating pending reviews
- Line-level comment syntax
- Multi-line comment ranges
- Error handling
- Review status management

---

## Error Handling

### Commit SHA Not Found
```
Error: Could not get HEAD commit SHA for PR #{pr-number}

Solution: Verify PR exists and is accessible
```

### Comment Skipped: Line Not in PR Diff
```
Warning: Comment skipped - Line {line_number} not in valid ranges for {file_path}

Cause: Line number doesn't exist in the NEW file version or is outside changed hunks

Solutions:
1. View file at HEAD commit in GitHub to verify line number
2. Check if file was renamed (update file path in issue)
3. Ensure upstream skill extracted line number from NEW file, not diff output
4. Run validation manually: gh pr diff {pr} | grep "@@ " to see valid ranges
```

**Example**:
```
⚠️  Comment skipped for backend/connectors/revolut.rs:999

Reason: Line 999 not in valid range (file has 738 lines)
Valid ranges: 1-738
Action: Verify line number matches actual file content at PR HEAD
```

### Comment Skipped: File Not in PR
```
Warning: Comment skipped - File {file_path} not modified in this PR

Cause: File path doesn't appear in PR diff

Solutions:
1. Verify file path is correct (relative from repo root)
2. Check if file was renamed (use new path)
3. Ensure file is actually part of the PR changes
```

### Comment Skipped: Unsupported Line Reference
```
Error: Comment skipped - Unsupported line_reference: {line_reference}

Cause: line_reference is not "NEW_FILE" (only NEW_FILE supported)

Solutions:
1. Update upstream skill to use NEW_FILE line numbers
2. Convert line number to NEW file reference manually
3. Verify upstream skill is following line extraction guide
```

### Authentication Failed
```
Error: gh CLI not authenticated

Solution: Run 'gh auth login' to authenticate with GitHub
```

### 422 Unprocessable Entity (Should No Longer Occur)
```
Error: {"message":"Unprocessable Entity","errors":["Line could not be resolved"]}

Cause: This error should be prevented by Step 2.5 (validation)

If this error still occurs:
1. Check validation logic is running correctly
2. Verify FILE_RANGES parsing is working
3. Review validation logs for skipped issues
4. File bug report - validation should prevent this error
```

---

## Examples

### Example 1: Successful Review Creation

**Input**: Issues from code-quality-review + connector-integration-validator

**Process**:
1. Collect 12 issues (2 critical, 5 warnings, 5 suggestions)
2. Format each as GitHub comment
3. Get commit SHA
4. Create pending review with all comments
5. Display summary

**Output**:
```
✅ Review Created Successfully!

📋 **12 pending comments** created for PR #238

**Severity Breakdown**:
- 🔴 Critical: 2
- 🟡 Important: 5
- 🟢 Suggestions: 5

**Files with Comments**:
1. backend/connector-integration/src/connectors/stripe.rs (4 comments)
2. backend/connector-integration/src/connectors/stripe/transformers.rs (6 comments)
3. backend/domain_types/src/types.rs (2 comments)

**Next Steps**:
Go to https://github.com/hyperswitch/connector-service/pull/238/files

You will see your pending review comments. Review, edit, or delete them, then submit when ready.

⚠️  Comments are PENDING - not posted publicly yet!
```

---

### Example 2: Review with Multi-Line Comments

**Input**: Issue spanning multiple lines

**Format**:
```json
{
  "path": "backend/connectors/stripe.rs",
  "start_line": 45,
  "start_side": "RIGHT",
  "line": 50,
  "side": "RIGHT",
  "body": "🟡 **Important** - Code Quality\n\nThis entire function could be refactored..."
}
```

**Output**: Comment appears on lines 45-50 in GitHub UI

---

### Example 3: Error Recovery

**Input**: One comment has invalid line number

**Process**:
1. Attempt to create review with all comments
2. API returns error for comment #5 (line 999 doesn't exist)
3. Skip invalid comment
4. Create review with remaining valid comments
5. Report skipped comment to user

**Output**:
```
⚠️  Review Created with Warnings

**Comments Created**: 11/12
**Skipped**: 1 comment (invalid line number)

**Skipped Comment**:
- File: backend/connectors/stripe.rs
- Line: 999 (line doesn't exist in file)
- Issue: Status mapping incorrect

**Action Required**: Manually verify line number and add comment in GitHub UI

**Next Steps**: Review the 11 pending comments in GitHub
```

---

## Advanced Features

### Multi-File Review Organization

Comments are grouped by file in the summary for easy navigation:

```markdown
### 📄 backend/connector-integration/src/connectors/stripe.rs

**Line 25** • 🔴 Critical - Type Safety
> Using RouterData instead of RouterDataV2

**Line 45** • 🟡 Important - Error Handling
> Missing error propagation with ? operator

**Line 120** • 🟢 Suggestion - Documentation
> Add doc comment for this function

---

### 📄 backend/connector-integration/src/connectors/stripe/transformers.rs

**Line 67** • 🔴 Critical - Security
> Hardcoded reference ID detected

...
```

---

### Review Statistics

**Auto-calculated**:
- Total comments
- Severity breakdown
- Files affected
- Average issues per file
- Most common issue category

**Example**:
```markdown
## Review Statistics
- **Total Issues**: 12
- **Files Affected**: 3
- **Average Issues per File**: 4
- **Most Common Category**: Code Quality (5 issues)

**Severity Distribution**:
🔴 Critical: 17% (2 issues)
🟡 Important: 42% (5 issues)
🟢 Suggestions: 41% (5 issues)
```

---

### Recommendation Engine

Based on severity distribution, provide recommendation:

```markdown
## Recommendation

**Overall Assessment**: BLOCK MERGE ❌

**Critical issues detected** (2). These must be fixed before merging:
1. Type safety violation (stripe.rs:25)
2. Security risk - hardcoded credentials (transformers.rs:67)

After fixing critical issues, re-run review to verify.
```

**Recommendation Logic**:
- Critical issues (≥1) → BLOCK MERGE ❌
- Warnings only (≥3) → REQUEST CHANGES ⚠️
- Warnings only (<3) → APPROVE WITH COMMENTS ✅
- Suggestions only → APPROVE ✅

---

## Performance Considerations

- **Batch Comments**: Create single review with all comments (not individual comments)
- **Deduplication**: Remove duplicate issues before creating comments
- **Line Validation**: Pre-validate line numbers to avoid API errors
- **Retry Logic**: Retry on transient failures (rate limiting, network issues)

---

## Version History

- **1.0.0** (2025-12-09): Initial skill creation
  - Pending review creation
  - Line-level comment formatting
  - Severity-based categorization
  - Multi-file organization
  - Review statistics
  - Recommendation engine
