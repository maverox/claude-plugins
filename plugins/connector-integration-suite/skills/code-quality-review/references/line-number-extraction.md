# Line Number Extraction Guide

## Overview

This guide explains how to correctly extract line numbers from files in a Pull Request for use in GitHub review comments.

**Critical Rule**: Always extract line numbers from the **NEW file version** (PR HEAD commit), as this is what the GitHub API requires for the `line` parameter.

---

## The Three Line Number Types

### 1. NEW_FILE (Recommended ✅)
Line numbers in the file **after** PR changes have been applied.

**Example**:
```rust
// File: backend/connectors/revolut.rs (NEW version at PR HEAD)
1: use common_enums;
2: use domain_types::router_data_v2::RouterDataV2;
3:
4: #[derive(Clone)]
5: const REVOLUT_API_VERSION: &str = "2025-10-16";  // ← Line 5 in NEW file
```

**GitHub API Requirement**: `line: 5, side: "RIGHT"`

---

### 2. OLD_FILE
Line numbers in the file **before** PR changes.

**Use Case**: Commenting on deleted lines (rare, requires `side: "LEFT"`)

**Example**:
```rust
// File: backend/connectors/revolut.rs (OLD version at base commit)
1: use common_enums;
2:
3: const OLD_VERSION: &str = "1.0";  // ← Line 3 in OLD file (deleted in PR)
```

**GitHub API**: `line: 3, side: "LEFT"` (for deleted lines only)

---

### 3. DIFF_POSITION (Deprecated ❌)
Sequential position in the unified diff output.

**Example**:
```diff
@@ -1,3 +1,5 @@
 use common_enums;
+use domain_types::router_data_v2::RouterDataV2;
+
 #[derive(Clone)]
+const REVOLUT_API_VERSION: &str = "2025-10-16";  // ← Line 22 in diff output
```

**Problem**: Line 22 in diff ≠ Line 5 in actual file

**Status**: The `position` parameter is deprecated by GitHub API

---

## Extraction Methods

### Method 1: Read File at HEAD Commit (Recommended ✅)

This is the most reliable method for getting correct line numbers.

#### Step 1: Get PR HEAD Commit SHA

```bash
# Get the HEAD commit SHA of the PR branch
HEAD_SHA=$(gh pr view {pr-number} --repo {owner}/{repo} --json headRefOid -q '.headRefOid')

echo "PR HEAD commit: $HEAD_SHA"
# Output: PR HEAD commit: 4bd7429b1cc5c38b072514eff3d0df9d7ba85e83
```

#### Step 2: Read File Content at HEAD Commit

```bash
# Fetch file content at the specific commit
gh api repos/{owner}/{repo}/contents/{file-path}?ref=$HEAD_SHA \
  --jq '.content' | base64 -d > /tmp/file_at_head.rs

# Example:
gh api repos/juspay/connector-service/contents/backend/connector-integration/src/connectors/revolut.rs?ref=4bd7429b1cc5c38b072514eff3d0df9d7ba85e83 \
  --jq '.content' | base64 -d > /tmp/revolut_new.rs
```

#### Step 3: Find Line Number in NEW File

```bash
# Find the exact line number using grep
LINE_NUM=$(grep -n "REVOLUT_API_VERSION" /tmp/revolut_new.rs | head -1 | cut -d: -f1)

echo "Line number in NEW file: $LINE_NUM"
# Output: Line number in NEW file: 5
```

#### Step 4: Extract Code Context

```bash
# Get the line and surrounding context (±2 lines)
sed -n "$((LINE_NUM-2)),$((LINE_NUM+2))p" /tmp/revolut_new.rs

# Output:
# 3:
# 4: #[derive(Clone)]
# 5: const REVOLUT_API_VERSION: &str = "2025-10-16";
# 6:
# 7: struct Revolut<T> {
```

#### Complete Example

```bash
#!/bin/bash

PR_NUMBER=328
REPO="juspay/connector-service"
FILE_PATH="backend/connector-integration/src/connectors/revolut.rs"
SEARCH_PATTERN="REVOLUT_API_VERSION"

# 1. Get HEAD commit SHA
HEAD_SHA=$(gh pr view $PR_NUMBER --repo $REPO --json headRefOid -q '.headRefOid')

# 2. Fetch file content at HEAD
gh api repos/$REPO/contents/$FILE_PATH?ref=$HEAD_SHA \
  --jq '.content' | base64 -d > /tmp/file_new.rs

# 3. Find line number
LINE_NUM=$(grep -n "$SEARCH_PATTERN" /tmp/file_new.rs | head -1 | cut -d: -f1)

# 4. Extract code snippet
CODE=$(sed -n "${LINE_NUM}p" /tmp/file_new.rs)

echo "Line in NEW file: $LINE_NUM"
echo "Code: $CODE"

# Output issue in correct format
cat << EOF
issues:
  - file: $FILE_PATH
    line_number: $LINE_NUM
    line_reference: "NEW_FILE"
    commit_sha: "$HEAD_SHA"
    issue: "API version is set to a future date"
    current_code: "$CODE"
EOF
```

**Output**:
```yaml
issues:
  - file: backend/connector-integration/src/connectors/revolut.rs
    line_number: 5
    line_reference: "NEW_FILE"
    commit_sha: "4bd7429b1cc5c38b072514eff3d0df9d7ba85e83"
    issue: "API version is set to a future date"
    current_code: "const REVOLUT_API_VERSION: &str = \"2025-10-16\";"
```

---

### Method 2: Parse Diff with Hunk Tracking

More complex but useful when you already have the diff and want to map positions.

#### Understanding Diff Hunk Headers

```diff
@@ -10,7 +20,8 @@  // ← Hunk header
```

**Format**: `@@ -<old_start>,<old_count> +<new_start>,<new_count> @@`

- `-10,7`: OLD file starts at line 10, contains 7 lines
- `+20,8`: NEW file starts at line 20, contains 8 lines

#### Tracking Line Numbers Through Diff

```bash
#!/bin/bash

# Parse diff and track NEW file line numbers
parse_diff_line_numbers() {
  local diff_file="$1"
  local new_line=0
  local in_hunk=false

  while IFS= read -r line; do
    # Detect hunk header
    if [[ "$line" =~ ^@@\ -[0-9]+,[0-9]+\ \+([0-9]+),[0-9]+ ]]; then
      new_line=${BASH_REMATCH[1]}
      in_hunk=true
      continue
    fi

    # Skip if not in a hunk
    [[ "$in_hunk" == false ]] && continue

    # Track line numbers
    if [[ "$line" =~ ^[+] ]]; then
      # Added line
      echo "NEW line $new_line: ${line:1}"
      ((new_line++))
    elif [[ "$line" =~ ^[-] ]]; then
      # Deleted line (don't increment new_line)
      :
    elif [[ "$line" =~ ^[\ ] ]]; then
      # Context line (unchanged)
      ((new_line++))
    fi
  done < "$diff_file"
}

# Usage
gh pr diff 328 > /tmp/pr_diff.txt
parse_diff_line_numbers /tmp/pr_diff.txt | grep "REVOLUT_API_VERSION"
```

**Warning**: This method is error-prone with:
- Multiple hunks in the same file
- Large insertions/deletions
- Renamed files

**Recommendation**: Use Method 1 (read file at HEAD) for reliability.

---

### Method 3: Use GitHub API Content Endpoint

Direct API call without local file operations.

```bash
# Get file content and line numbers in one call
get_line_number_from_api() {
  local repo="$1"
  local file_path="$2"
  local ref="$3"
  local search_pattern="$4"

  # Fetch file content
  local content=$(gh api "repos/$repo/contents/$file_path?ref=$ref" \
    --jq '.content' | base64 -d)

  # Find line number
  local line_num=$(echo "$content" | grep -n "$search_pattern" | head -1 | cut -d: -f1)

  echo "$line_num"
}

# Usage
LINE=$(get_line_number_from_api \
  "juspay/connector-service" \
  "backend/connector-integration/src/connectors/revolut.rs" \
  "4bd7429b1cc5c38b072514eff3d0df9d7ba85e83" \
  "REVOLUT_API_VERSION")

echo "Line number: $LINE"
# Output: Line number: 5
```

---

## Edge Cases

### Case 1: Files with Large Insertions/Deletions

**Problem**: A 100-line insertion at the top shifts all subsequent line numbers.

**Example**:
```diff
@@ -1,5 +1,105 @@
+// 100 new lines of imports and documentation
+...
 const REVOLUT_API_VERSION: &str = "2025-10-16";  // Now at line 105, was line 5
```

**Solution**: Always read from HEAD commit to get current line numbers (Method 1).

---

### Case 2: Renamed Files

**Problem**: File path changes between base and HEAD.

**Example**:
- OLD: `backend/connectors/revolut.rs`
- NEW: `backend/connector-integration/src/connectors/revolut.rs`

**Detection**:
```bash
# Check if file was renamed
gh pr diff 328 | grep "^rename from\|^rename to"

# Output:
# rename from backend/connectors/revolut.rs
# rename to backend/connector-integration/src/connectors/revolut.rs
```

**Solution**: Use the NEW file path when creating review comments.

---

### Case 3: Binary Files

**Problem**: Binary files (images, compiled binaries) don't have line numbers.

**Detection**:
```bash
# Check if file is binary
file /tmp/image.png
# Output: /tmp/image.png: PNG image data

# Or from diff
gh pr diff 328 | grep "Binary files"
# Output: Binary files a/image.png and b/image.png differ
```

**Solution**: Skip line-level comments for binary files. Only general review comments allowed.

---

### Case 4: Files with No Changes in Hunk

**Problem**: File appears in PR but specific lines weren't modified.

**Example**: Commenting on existing code that wasn't changed in the PR.

**Solution**: You can still comment on any line in the NEW file, even if it wasn't modified. Use line numbers from the NEW file version.

---

## Testing Line Numbers

### Test 1: Verify Line Exists in NEW File

```bash
# Get file length
FILE_LENGTH=$(gh api repos/{owner}/{repo}/contents/{file}?ref=$HEAD_SHA \
  --jq '.content' | base64 -d | wc -l)

# Check if line number is valid
if (( LINE_NUM > 0 && LINE_NUM <= FILE_LENGTH )); then
  echo "✅ Line $LINE_NUM is valid (file has $FILE_LENGTH lines)"
else
  echo "❌ Line $LINE_NUM is invalid (file has $FILE_LENGTH lines)"
fi
```

### Test 2: Verify Line Content Matches

```bash
# Extract the specific line
ACTUAL_CODE=$(gh api repos/{owner}/{repo}/contents/{file}?ref=$HEAD_SHA \
  --jq '.content' | base64 -d | sed -n "${LINE_NUM}p")

EXPECTED_CODE='const REVOLUT_API_VERSION: &str = "2025-10-16";'

if [[ "$ACTUAL_CODE" == "$EXPECTED_CODE" ]]; then
  echo "✅ Line content matches"
else
  echo "❌ Line content mismatch"
  echo "Expected: $EXPECTED_CODE"
  echo "Actual: $ACTUAL_CODE"
fi
```

### Test 3: Validate Against PR Diff

```bash
# Get valid line ranges from PR diff
gh pr diff 328 | grep "^@@" | while read hunk; do
  # Extract new file line range
  if [[ "$hunk" =~ \+([0-9]+),([0-9]+) ]]; then
    start=${BASH_REMATCH[1]}
    count=${BASH_REMATCH[2]}
    end=$((start + count - 1))
    echo "Valid range: $start-$end"
  fi
done
```

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Using Diff Line Numbers

```bash
# WRONG: Using line number from diff output
gh pr diff 328 | grep -n "REVOLUT_API_VERSION"
# Output: 22:+const REVOLUT_API_VERSION: &str = "2025-10-16";
# ← Line 22 is the diff position, NOT the file line number
```

**Fix**: Read the actual file at HEAD commit.

---

### ❌ Mistake 2: Using Line Numbers from Local Checkout

```bash
# WRONG: Using line numbers from your local working directory
grep -n "REVOLUT_API_VERSION" backend/connector-integration/src/connectors/revolut.rs
# ← Your local file might be different from PR HEAD
```

**Fix**: Always fetch from the specific commit SHA.

---

### ❌ Mistake 3: Assuming Base Commit Line Numbers

```bash
# WRONG: Using line numbers from the PR base (target branch)
BASE_SHA=$(gh pr view 328 --json baseRefOid -q '.baseRefOid')
gh api repos/{owner}/{repo}/contents/{file}?ref=$BASE_SHA
# ← This gives you OLD file line numbers, not NEW
```

**Fix**: Use `headRefOid` (PR branch HEAD), not `baseRefOid` (target branch).

---

## Recommended Workflow

For use in code-quality-review and connector-integration-validator skills:

```bash
#!/bin/bash
# extract_line_numbers.sh

PR_NUMBER="$1"
REPO="$2"
FILE_PATH="$3"

# 1. Get PR HEAD commit
HEAD_SHA=$(gh pr view $PR_NUMBER --repo $REPO --json headRefOid -q '.headRefOid')

# 2. Download file at HEAD
TEMP_FILE=$(mktemp)
gh api "repos/$REPO/contents/$FILE_PATH?ref=$HEAD_SHA" \
  --jq '.content' | base64 -d > "$TEMP_FILE"

# 3. Function to find line number by pattern
find_line() {
  local pattern="$1"
  grep -n "$pattern" "$TEMP_FILE" | head -1 | cut -d: -f1
}

# 4. Function to extract code at line
get_code_at_line() {
  local line_num="$1"
  sed -n "${line_num}p" "$TEMP_FILE"
}

# 5. Validate line exists
validate_line() {
  local line_num="$1"
  local file_length=$(wc -l < "$TEMP_FILE")

  if (( line_num > 0 && line_num <= file_length )); then
    return 0  # Valid
  else
    return 1  # Invalid
  fi
}

# Export functions for use in skill
export -f find_line
export -f get_code_at_line
export -f validate_line
export HEAD_SHA
export TEMP_FILE

# Cleanup on exit
trap "rm -f $TEMP_FILE" EXIT
```

**Usage in Skill**:
```bash
source extract_line_numbers.sh 328 juspay/connector-service backend/connectors/revolut.rs

# Find issue
LINE=$(find_line "REVOLUT_API_VERSION")
CODE=$(get_code_at_line "$LINE")

# Validate
if validate_line "$LINE"; then
  # Create issue
  cat << EOF
  - file: $FILE_PATH
    line_number: $LINE
    line_reference: "NEW_FILE"
    commit_sha: "$HEAD_SHA"
    current_code: "$CODE"
EOF
fi
```

---

## Performance Considerations

- **Cache HEAD commit content**: Download each file once, use for all issues in that file
- **Batch API calls**: Use single API call per file, not per issue
- **Parallel processing**: Process multiple files concurrently

---

## Summary

**Key Takeaways**:

1. ✅ Always use **NEW_FILE** line numbers (PR HEAD commit)
2. ✅ Use Method 1 (read file at HEAD) for reliability
3. ✅ Include `line_reference: "NEW_FILE"` and `commit_sha` in output
4. ✅ Validate line numbers exist before creating issues
5. ❌ Never use diff positions or local file line numbers
6. ❌ Never assume line numbers from base commit

**GitHub API Requirements**:
- `line`: Actual line number in NEW file
- `side`: `"RIGHT"` for NEW file content
- `path`: Relative path from repository root

**Output Format**:
```yaml
issues:
  - file: path/to/file.rs
    line_number: 45           # Actual line in NEW file
    line_reference: "NEW_FILE" # Explicit reference type
    commit_sha: "abc123..."   # PR HEAD commit
    issue: "Description"
    current_code: "..."
    suggested_fix: "..."
```

---

**Version**: 1.0
**Last Updated**: 2025-12-10
**Status**: Production Ready
