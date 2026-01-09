# Line Number Extraction Reference

Critical guide for extracting accurate line numbers from the NEW file version for GitHub PR review comments.

## Why This Matters

GitHub's review API requires the **actual line number in the new file** (after PR changes). Using wrong line numbers causes:
- `422 "Line could not be resolved"` errors
- Comments on wrong lines
- Failed review creation

## The Golden Rule

**ALWAYS extract line numbers from the NEW file at the PR's HEAD commit.**

Never use:
- Line numbers from diff output (these are positions, not line numbers)
- Line numbers from your local file (may be out of sync)
- Line numbers from the base branch

## Method 1: Read File at HEAD Commit (Recommended)

### Step 1: Get PR HEAD Commit SHA

```bash
HEAD_SHA=$(gh pr view {pr-number} --repo {owner}/{repo} --json headRefOid -q '.headRefOid')
echo "HEAD SHA: $HEAD_SHA"
```

### Step 2: Fetch File Content at HEAD

```bash
# Using GitHub API
gh api repos/{owner}/{repo}/contents/{file_path}?ref=$HEAD_SHA \
  | jq -r '.content' \
  | base64 -d \
  > /tmp/file_at_head.txt
```

### Step 3: Find Line Number in NEW File

```bash
# Find specific pattern
LINE_NUM=$(grep -n "pattern_to_find" /tmp/file_at_head.txt | head -1 | cut -d: -f1)
echo "Line number: $LINE_NUM"
```

### Step 4: Validate with Code Context

```bash
# Get the actual code at that line (for verification)
CODE_AT_LINE=$(sed -n "${LINE_NUM}p" /tmp/file_at_head.txt)
echo "Code at line $LINE_NUM: $CODE_AT_LINE"
```

### Complete Script

```bash
#!/bin/bash
set -e

PR_NUMBER="$1"
OWNER="$2"
REPO="$3"
FILE_PATH="$4"
PATTERN="$5"

# Get HEAD SHA
HEAD_SHA=$(gh pr view "$PR_NUMBER" --repo "$OWNER/$REPO" --json headRefOid -q '.headRefOid')

# Fetch file content
gh api "repos/$OWNER/$REPO/contents/$FILE_PATH?ref=$HEAD_SHA" \
  | jq -r '.content' \
  | base64 -d \
  > /tmp/file_content.txt

# Find line number
LINE_NUM=$(grep -n "$PATTERN" /tmp/file_content.txt | head -1 | cut -d: -f1)

if [[ -z "$LINE_NUM" ]]; then
  echo "Pattern not found in file"
  exit 1
fi

# Get code at line
CODE_AT_LINE=$(sed -n "${LINE_NUM}p" /tmp/file_content.txt)

echo "Line: $LINE_NUM"
echo "Code: $CODE_AT_LINE"
echo "SHA: $HEAD_SHA"
```

## Method 2: Parse Diff with Hunk Tracking

When you need to map diff changes to line numbers:

### Understanding Hunk Headers

```diff
@@ -old_start,old_count +new_start,new_count @@ context
```

Example:
```diff
@@ -10,7 +10,8 @@ function example() {
```
- Old file: starts at line 10, 7 lines
- New file: starts at line 10, 8 lines

### Tracking Line Numbers Through Diff

```python
def get_new_line_numbers(diff_content: str) -> dict:
    """Extract mapping of file -> valid line numbers from diff."""
    file_lines = {}
    current_file = None
    current_line = 0

    for line in diff_content.split('\n'):
        # New file
        if line.startswith('+++ b/'):
            current_file = line[6:]
            file_lines[current_file] = []
            continue

        # Hunk header
        match = re.match(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
        if match:
            current_line = int(match.group(1))
            continue

        # Track lines in new file
        if current_file and line.startswith('+'):
            file_lines[current_file].append(current_line)
            current_line += 1
        elif current_file and not line.startswith('-'):
            # Context line (exists in both)
            file_lines[current_file].append(current_line)
            current_line += 1

    return file_lines
```

## Method 3: Use GitHub API Content Endpoint

Direct API call without local files:

```bash
# Get file content at specific commit
FILE_CONTENT=$(gh api \
  "repos/$OWNER/$REPO/contents/$FILE_PATH?ref=$HEAD_SHA" \
  -q '.content' \
  | base64 -d)

# Find line number using awk
echo "$FILE_CONTENT" | awk "/pattern/{print NR; exit}"
```

## Common Patterns for Finding Issues

### Find Function Definition

```bash
# TypeScript/JavaScript
grep -n "function functionName\|const functionName = \|functionName(" /tmp/file.txt

# Python
grep -n "def function_name\|async def function_name" /tmp/file.txt

# Rust
grep -n "fn function_name\|pub fn function_name" /tmp/file.txt
```

### Find Variable Assignment

```bash
# Assignment with specific value
grep -n "variableName\s*=" /tmp/file.txt

# Specific pattern
grep -n "eval(" /tmp/file.txt
```

### Find Class Definition

```bash
grep -n "class ClassName\|export class ClassName" /tmp/file.txt
```

## Edge Cases

### Pattern Appears Multiple Times

```bash
# Find all occurrences
grep -n "pattern" /tmp/file.txt

# Output:
# 45:  const result = eval(userInput);
# 120: // eval is dangerous
# 180: evaluate(data);  # False positive

# Use more specific pattern
grep -n "eval(userInput)" /tmp/file.txt
```

### Pattern with Special Characters

```bash
# Escape regex special characters
grep -n "\\$\\{userId\\}" /tmp/file.txt

# Or use fixed string
grep -Fn '${userId}' /tmp/file.txt
```

### Multiline Patterns

```bash
# Use pcregrep for multiline
pcregrep -Mn "try\s*{\s*\n\s*await\s+saveData" /tmp/file.txt
```

### File Renamed in PR

```bash
# Get the NEW filename from diff
NEW_PATH=$(gh pr diff $PR_NUMBER --repo $OWNER/$REPO | grep "^+++ b/" | cut -c7-)

# Use the new path for all operations
```

## Output Format for Issues

Every issue MUST include these fields:

```yaml
- severity: WARNING
  category: Error Handling
  file: src/api/handler.ts
  line_number: 45                    # From NEW file
  line_reference: "NEW_FILE"         # Always "NEW_FILE"
  commit_sha: "abc123def456..."      # PR HEAD commit
  code_at_line: "catch (e) { }"      # Validation checksum
  issue: "Empty catch block"
  current_code: |
    catch (e) { }
  suggested_fix: |
    catch (e) {
      logger.error('Failed', { error: e });
      throw e;
    }
  impact: "Errors silently swallowed"
```

## Validation Before GitHub API

Always validate before creating review comments:

```bash
# 1. Verify file exists in PR
gh pr diff $PR --name-only | grep -q "$FILE_PATH"

# 2. Verify line is within file
TOTAL_LINES=$(wc -l < /tmp/file_at_head.txt)
if [[ $LINE_NUM -gt $TOTAL_LINES ]]; then
  echo "Invalid line number: $LINE_NUM > $TOTAL_LINES"
fi

# 3. Verify line is in changed hunks (optional, for stricter validation)
# Parse hunk headers and check if line is in valid range
```

## Troubleshooting

### Pattern Not Found

```
Cause: Pattern doesn't exist in file at HEAD commit

Solutions:
1. Verify file path is correct
2. Check if code was changed since analysis
3. Use broader search pattern
4. Manually inspect file content
```

### Line Number Too High

```
Cause: Line number exceeds file length

Solutions:
1. Re-fetch file at HEAD commit
2. Verify file wasn't truncated
3. Check for encoding issues
```

### Different Code at Line

```
Cause: Line number points to different code than expected

Solutions:
1. File may have been modified after initial analysis
2. Verify using code_at_line checksum
3. Re-run analysis with fresh file content
```

## Best Practices

1. **Always use HEAD SHA** - Never assume local files match PR
2. **Include code_at_line** - For validation and debugging
3. **Validate before API call** - Prevent 422 errors
4. **Handle edge cases** - Renamed files, multiple matches
5. **Log extraction steps** - For debugging failed extractions
