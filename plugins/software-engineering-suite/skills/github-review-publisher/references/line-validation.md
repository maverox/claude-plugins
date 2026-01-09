# Line Validation Reference

Algorithm and techniques for validating line numbers before creating GitHub review comments.

## Why Validation is Critical

GitHub's review API returns `422 "Line could not be resolved"` when:
- Line number doesn't exist in the file
- Line is outside the changed hunks
- File path is incorrect
- Using wrong side (LEFT vs RIGHT)

**Pre-validation eliminates these errors entirely.**

## The Problem

### Scenario

Code quality review finds an issue at line 45 of `src/api/handler.ts`.

However:
- The file only has 40 lines at the PR's HEAD commit
- Or line 45 exists but isn't part of the PR's changes
- Or the file was renamed

Creating a comment will fail with 422.

### Solution

**Always validate line numbers against the PR diff BEFORE calling the API.**

## Validation Algorithm

### Step 1: Fetch PR Diff

```bash
gh pr diff {pr-number} --repo {owner}/{repo} > /tmp/pr_diff.txt
```

### Step 2: Parse Valid Line Ranges

Extract which lines in each file are valid for comments:

```bash
#!/bin/bash

declare -A FILE_RANGES

current_file=""
while IFS= read -r line; do
  # Detect new file
  if [[ "$line" =~ ^\+\+\+\ b/(.+)$ ]]; then
    current_file="${BASH_REMATCH[1]}"
    FILE_RANGES["$current_file"]=""
  fi

  # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
  if [[ "$line" =~ ^@@\ -([0-9]+),?([0-9]*)\ \+([0-9]+),?([0-9]*)\ @@ ]]; then
    new_start="${BASH_REMATCH[3]}"
    new_count="${BASH_REMATCH[4]:-1}"  # Default to 1 if not specified
    new_end=$((new_start + new_count - 1))

    # Append range to file
    if [[ -z "${FILE_RANGES[$current_file]}" ]]; then
      FILE_RANGES["$current_file"]="$new_start-$new_end"
    else
      FILE_RANGES["$current_file"]="${FILE_RANGES[$current_file]},$new_start-$new_end"
    fi
  fi
done < /tmp/pr_diff.txt

# Debug: print all valid ranges
for file in "${!FILE_RANGES[@]}"; do
  echo "$file: ${FILE_RANGES[$file]}"
done
```

### Step 3: Validate Each Issue

```bash
is_line_valid() {
  local file="$1"
  local line_num="$2"

  # Get ranges for this file
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

# Example usage
result=$(is_line_valid "src/api/handler.ts" 45)
if [[ "$result" == "VALID" ]]; then
  echo "Line 45 is valid for comments"
else
  echo "Cannot comment on line 45: $result"
fi
```

### Step 4: Classify All Issues

```bash
VALID_ISSUES=()
SKIPPED_ISSUES=()

for issue in "${ALL_ISSUES[@]}"; do
  file=$(echo "$issue" | yq '.file')
  line_num=$(echo "$issue" | yq '.line_number')

  result=$(is_line_valid "$file" "$line_num")

  if [[ "$result" == "VALID" ]]; then
    VALID_ISSUES+=("$issue")
  else
    SKIPPED_ISSUES+=("$file|$line_num|$result")
  fi
done

echo "Valid: ${#VALID_ISSUES[@]}"
echo "Skipped: ${#SKIPPED_ISSUES[@]}"
```

## Understanding Hunk Headers

### Format

```
@@ -old_start,old_count +new_start,new_count @@ optional context
```

### Examples

```diff
@@ -10,7 +10,8 @@ function example() {
```
- Old file: starts at line 10, 7 lines of context
- New file: starts at line 10, 8 lines of context
- Valid comment range: lines 10-17

```diff
@@ -1,5 +1,10 @@
```
- Old file: starts at line 1, 5 lines
- New file: starts at line 1, 10 lines
- Valid comment range: lines 1-10

```diff
@@ -0,0 +1,50 @@
```
- Old file: didn't exist (0,0)
- New file: starts at line 1, 50 lines
- Valid comment range: lines 1-50
- This is a **new file**

## Edge Cases

### New File

```diff
diff --git a/src/newfile.ts b/src/newfile.ts
new file mode 100644
--- /dev/null
+++ b/src/newfile.ts
@@ -0,0 +1,25 @@
+import express from 'express';
+
+export function handler() {
...
```

Valid range: 1-25 (entire file is new)

### Deleted File

```diff
diff --git a/src/oldfile.ts b/src/oldfile.ts
deleted file mode 100644
--- a/src/oldfile.ts
+++ /dev/null
@@ -1,50 +0,0 @@
-import express from 'express';
...
```

**Cannot comment on deleted files** (no RIGHT side exists).

### Renamed File

```diff
diff --git a/src/old-name.ts b/src/new-name.ts
similarity index 95%
rename from src/old-name.ts
rename to src/new-name.ts
--- a/src/old-name.ts
+++ b/src/new-name.ts
@@ -10,5 +10,6 @@ function example() {
...
```

Use the **new path** (`src/new-name.ts`) for comments.

### Multiple Hunks

```diff
@@ -10,5 +10,6 @@ function one() {
...
@@ -50,8 +51,12 @@ function two() {
...
@@ -100,3 +105,5 @@ function three() {
...
```

Valid ranges: 10-15, 51-62, 105-109

Lines between hunks (16-50, 63-104) are **NOT valid** for comments.

### Single Line Change

```diff
@@ -45,1 +45,1 @@ const config = {
-  timeout: 5000
+  timeout: 10000
```

Valid range: just line 45

### No Line Count

```diff
@@ -45 +45 @@ const value = 1;
```

When count is omitted, it defaults to 1.
Valid range: line 45 only

## Python Implementation

For more complex validation logic:

```python
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

@dataclass
class ValidationResult:
    valid: bool
    reason: str
    valid_ranges: Optional[List[Tuple[int, int]]] = None

def parse_diff_ranges(diff_content: str) -> Dict[str, List[Tuple[int, int]]]:
    """Parse diff to extract valid line ranges for each file."""
    file_ranges: Dict[str, List[Tuple[int, int]]] = {}
    current_file = None

    for line in diff_content.split('\n'):
        # Match file path: +++ b/path/to/file.ts
        file_match = re.match(r'^\+\+\+ b/(.+)$', line)
        if file_match:
            current_file = file_match.group(1)
            file_ranges[current_file] = []
            continue

        # Match hunk header: @@ -old +new @@
        hunk_match = re.match(
            r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@',
            line
        )
        if hunk_match and current_file:
            new_start = int(hunk_match.group(1))
            new_count = int(hunk_match.group(2) or 1)
            new_end = new_start + new_count - 1
            file_ranges[current_file].append((new_start, new_end))

    return file_ranges

def validate_line(
    file_path: str,
    line_number: int,
    file_ranges: Dict[str, List[Tuple[int, int]]]
) -> ValidationResult:
    """Validate if a line number is valid for commenting."""

    # Check if file is in PR
    if file_path not in file_ranges:
        return ValidationResult(
            valid=False,
            reason="FILE_NOT_IN_PR"
        )

    ranges = file_ranges[file_path]

    # Check if line is in any valid range
    for start, end in ranges:
        if start <= line_number <= end:
            return ValidationResult(
                valid=True,
                reason="VALID",
                valid_ranges=ranges
            )

    return ValidationResult(
        valid=False,
        reason="LINE_NOT_IN_RANGE",
        valid_ranges=ranges
    )

# Usage example
diff_content = """
diff --git a/src/api/handler.ts b/src/api/handler.ts
--- a/src/api/handler.ts
+++ b/src/api/handler.ts
@@ -20,10 +20,15 @@ export async function handleRequest(req, res) {
...
"""

file_ranges = parse_diff_ranges(diff_content)
result = validate_line("src/api/handler.ts", 25, file_ranges)

if result.valid:
    print("Line 25 is valid for comments")
else:
    print(f"Cannot comment: {result.reason}")
    print(f"Valid ranges: {result.valid_ranges}")
```

## Reporting Skipped Issues

When issues are skipped, provide clear feedback to the user:

```markdown
## Skipped Comments Report

**2 comment(s) skipped due to invalid line numbers**

### 1. src/api/handler.ts:999

- **Reason**: Line 999 does not exist in file (file has 150 lines)
- **Valid Ranges**: 20-34, 50-65, 100-120
- **Issue**: Empty catch block
- **Action**: Verify line number in GitHub UI

### 2. src/deleted.ts:45

- **Reason**: File not in PR (may have been deleted or renamed)
- **Issue**: Unused import
- **Action**: Check if file was renamed; use new path

---

**How to add these comments manually:**

1. Go to: https://github.com/owner/repo/pull/42/files
2. Navigate to the file
3. Click the line number to add a comment
4. Copy the formatted comment from the review skill output
```

## Best Practices

1. **Always validate before API call**
   - Never assume line numbers are correct
   - Upstream skills may have bugs

2. **Use NEW file lines**
   - Comments go on RIGHT side
   - Don't use diff positions or old file lines

3. **Handle all edge cases**
   - New files
   - Deleted files
   - Renamed files
   - Multiple hunks
   - Single-line changes

4. **Provide clear error reporting**
   - Tell user which comments were skipped
   - Explain why and how to fix

5. **Fail gracefully**
   - Don't fail entire review for one bad line
   - Create review with valid comments
   - Report skipped ones separately
