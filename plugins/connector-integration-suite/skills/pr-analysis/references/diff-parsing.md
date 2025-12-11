# Diff Parsing Reference

**Version**: 1.0.0
**Purpose**: Understanding and parsing unified diff format from GitHub PRs

---

## Unified Diff Format

### Basic Structure

```diff
diff --git a/file.rs b/file.rs
index abc123..def456 100644
--- a/file.rs
+++ b/file.rs
@@ -10,7 +10,8 @@ fn example() {
     let x = 5;
-    let y = 10;
+    let y = 20;
+    let z = 30;
     println!("{}", x);
 }
```

### Components

**1. Header**:
```diff
diff --git a/file.rs b/file.rs
```
- Identifies the file being changed
- `a/` prefix = old version
- `b/` prefix = new version

**2. Metadata**:
```diff
index abc123..def456 100644
--- a/file.rs
+++ b/file.rs
```
- `index`: Git blob IDs
- `---`: Old file path
- `+++`: New file path
- `100644`: File mode

**3. Hunk Header**:
```diff
@@ -10,7 +10,8 @@ fn example() {
```
- `-10,7`: Old file - start at line 10, span 7 lines
- `+10,8`: New file - start at line 10, span 8 lines
- `fn example()`: Context (function name)

**4. Change Lines**:
```diff
     let x = 5;      # Context line (unchanged)
-    let y = 10;     # Removed line
+    let y = 20;     # Added line
+    let z = 30;     # Added line
     println!("{}", x);  # Context line
```

---

## Parsing Hunks

### Hunk Header Format

```
@@ -<old_start>,<old_count> +<new_start>,<new_count> @@ [context]
```

**Examples**:

```diff
@@ -1,5 +1,6 @@
# Old: lines 1-5 (5 lines)
# New: lines 1-6 (6 lines)
# Change: 1 line added

@@ -10,7 +10,7 @@
# Old: lines 10-16 (7 lines)
# New: lines 10-16 (7 lines)
# Change: content modified, same line count

@@ -25,3 +25,0 @@
# Old: lines 25-27 (3 lines)
# New: line 25, 0 lines (deleted)
# Change: 3 lines removed
```

### Extracting Line Numbers

**For Added Lines (RIGHT side)**:
```bash
# Example hunk: @@ -10,7 +20,8 @@
# New file starts at line 20

new_start=20  # From +20,8
current_line=$new_start

# As you process each line:
case $line_prefix in
  " ")  # Context line
    current_line=$((current_line + 1))
    ;;
  "+")  # Added line
    echo "Added at line: $current_line"
    current_line=$((current_line + 1))
    ;;
  "-")  # Removed line (doesn't increment new line count)
    ;;
esac
```

**For Removed Lines (LEFT side)**:
```bash
# Example hunk: @@ -10,7 +20,8 @@
# Old file starts at line 10

old_start=10  # From -10,7
current_line=$old_start

# As you process each line:
case $line_prefix in
  " ")  # Context line
    current_line=$((current_line + 1))
    ;;
  "-")  # Removed line
    echo "Removed from line: $current_line"
    current_line=$((current_line + 1))
    ;;
  "+")  # Added line (doesn't exist in old file)
    ;;
esac
```

---

## Real-World Examples

### Example 1: Simple Addition

```diff
diff --git a/src/lib.rs b/src/lib.rs
index abc123..def456 100644
--- a/src/lib.rs
+++ b/src/lib.rs
@@ -5,6 +5,7 @@ pub fn process() {
     let data = fetch();
     let result = transform(data);
+    validate(&result);
     save(result);
 }
```

**Analysis**:
- Hunk: `-5,6 +5,7` (line 5, old=6 lines, new=7 lines)
- Line added at: **line 7** in new file
- Content: `validate(&result);`

### Example 2: Replacement

```diff
@@ -12,4 +12,4 @@ fn calculate(x: i64) -> i64 {
     let a = x * 2;
     let b = x + 5;
-    a + b
+    (a + b) * 10
 }
```

**Analysis**:
- Old line 14: `a + b` (removed)
- New line 14: `(a + b) * 10` (added)
- **Comment target**: Line 14, RIGHT side

### Example 3: Multiple Hunks

```diff
@@ -5,3 +5,4 @@ fn first() {
     let x = 1;
+    let y = 2;
     process(x);
 }
@@ -20,5 +21,6 @@ fn second() {
     let a = 10;
     let b = 20;
+    let c = 30;
     combine(a, b);
 }
```

**Analysis**:
- **Hunk 1**: Line 7 (new file) - `let y = 2;` added
- **Hunk 2**: Line 23 (new file) - `let c = 30;` added

---

## Line Number Calculation

### Algorithm for RIGHT Side (New File)

```python
def calculate_new_line_numbers(diff_text):
    """
    Parse diff and return line numbers for added/modified lines
    """
    hunks = []
    current_hunk = None

    for line in diff_text.split('\n'):
        # Hunk header
        if line.startswith('@@'):
            # Parse: @@ -10,7 +20,8 @@ context
            match = re.match(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@', line)
            if match:
                old_start, old_count, new_start, new_count = map(int, match.groups())
                current_hunk = {
                    'new_start': new_start,
                    'new_line': new_start,  # Current line counter
                    'changes': []
                }
                hunks.append(current_hunk)

        # Change lines
        elif current_hunk:
            if line.startswith('+') and not line.startswith('+++'):
                # Added line
                current_hunk['changes'].append({
                    'type': 'added',
                    'line': current_hunk['new_line'],
                    'content': line[1:]  # Remove '+' prefix
                })
                current_hunk['new_line'] += 1

            elif line.startswith('-') and not line.startswith('---'):
                # Removed line (doesn't increment new_line)
                pass

            elif line.startswith(' '):
                # Context line
                current_hunk['new_line'] += 1

    return hunks
```

### Example Usage

```python
diff = """
@@ -10,5 +10,7 @@ fn example() {
     let x = 5;
-    let y = 10;
+    let y = 20;
+    let z = 30;
     println!("{}", x);
 }
"""

hunks = calculate_new_line_numbers(diff)
# Output:
# [
#   {
#     'new_start': 10,
#     'changes': [
#       {'type': 'added', 'line': 12, 'content': '    let y = 20;'},
#       {'type': 'added', 'line': 13, 'content': '    let z = 30;'}
#     ]
#   }
# ]
```

---

## Multi-Line Comment Ranges

### GitHub API Format

For comments spanning multiple lines:

```json
{
  "path": "src/lib.rs",
  "start_line": 10,
  "start_side": "RIGHT",
  "line": 15,
  "side": "RIGHT",
  "body": "Comment spanning lines 10-15"
}
```

### Identifying Ranges in Diff

```diff
@@ -5,10 +5,10 @@ fn process() {
     // Start of problematic block
     let x = unsafe {
         ptr::read(data)
     };
     let y = transform(x);
     // End of block
```

**To comment on lines 6-10**:
- `start_line`: 6
- `line`: 10
- Both `side`: "RIGHT"

---

## Binary Files

### Diff Output

```diff
diff --git a/image.png b/image.png
index abc123..def456 100644
Binary files a/image.png and b/image.png differ
```

**Handling**:
- Cannot create line-level comments on binary files
- Skip or create file-level comment only

---

## File Rename Detection

```diff
diff --git a/old_name.rs b/new_name.rs
similarity index 95%
rename from old_name.rs
rename to new_name.rs
index abc123..def456 100644
--- a/old_name.rs
+++ b/new_name.rs
@@ -10,3 +10,4 @@
```

**Important**:
- Use the **new filename** (`new_name.rs`) for comments
- Line numbers refer to the new file

---

## Edge Cases

### 1. File Creation

```diff
diff --git a/new_file.rs b/new_file.rs
new file mode 100644
index 000000..abc123
--- /dev/null
+++ b/new_file.rs
@@ -0,0 +1,10 @@
+fn new_function() {
+    println!("Hello");
+}
```

- Old start: 0 (file didn't exist)
- New start: 1
- All lines are additions

### 2. File Deletion

```diff
diff --git a/deleted_file.rs b/deleted_file.rs
deleted file mode 100644
index abc123..000000
--- a/deleted_file.rs
+++ /dev/null
@@ -1,10 +0,0 @@
-fn old_function() {
-    println!("Goodbye");
-}
```

- New count: 0 (file no longer exists)
- Cannot add comments on deleted files (use LEFT side with old line numbers if needed)

### 3. No Newline at End of File

```diff
@@ -10,3 +10,4 @@
     last_line();
-}
\ No newline at end of file
+}
+// Added comment
```

- `\ No newline at end of file` - informational, not a real line
- Line numbers still sequential

---

## Parsing with grep/awk/sed

### Extract File Paths

```bash
# Get all changed files
gh pr diff 238 | grep '^diff --git' | awk '{print $3}' | sed 's|^a/||'
```

### Extract Hunk Headers

```bash
# Get all hunks with line numbers
gh pr diff 238 | grep '^@@'

# Parse hunk start lines
gh pr diff 238 | grep '^@@' | sed -E 's/@@ -[0-9]+,[0-9]+ \+([0-9]+),[0-9]+ @@.*/\1/'
```

### Count Additions/Deletions per File

```bash
# Count added lines in a file
gh pr diff 238 -- file.rs | grep '^+' | grep -v '^+++' | wc -l

# Count removed lines
gh pr diff 238 -- file.rs | grep '^-' | grep -v '^---' | wc -l
```

---

## Common Pitfalls

### 1. Line Number vs Diff Position

**WRONG**:
```json
{
  "path": "file.rs",
  "position": 15,  // Diff-relative position (15th line in diff)
  "body": "Comment"
}
```

**CORRECT**:
```json
{
  "path": "file.rs",
  "line": 45,  // Actual line number in file
  "side": "RIGHT",
  "body": "Comment"
}
```

### 2. Counting from Wrong Side

When commenting on new code, use:
- `side: "RIGHT"`
- Line numbers from the **new file** (`+10,8` part of hunk)

### 3. Ignoring Context Lines

Context lines (no prefix or space prefix) increment line count:

```diff
@@ -10,3 +10,4 @@
     let x = 1;  // Line 11 (context, counts)
+    let y = 2;  // Line 12 (added, counts)
     let z = 3;  // Line 13 (context, counts)
```

---

## Validation

### Check Line Number Validity

```bash
# Get file content at specific line
gh pr view 238 --json files -q '.files[] | select(.path=="file.rs")'

# Verify line exists in new version
FILE_LINES=$(gh pr diff 238 -- file.rs | grep -v '^[+- ]' | wc -l)
if [ $LINE_NUM -gt $FILE_LINES ]; then
  echo "ERROR: Line $LINE_NUM exceeds file length"
fi
```

---

## Tools & Libraries

### Command-Line Tools

**diff-so-fancy** - Better diff formatting:
```bash
brew install diff-so-fancy
gh pr diff 238 | diff-so-fancy
```

**delta** - Syntax-highlighted diffs:
```bash
brew install git-delta
gh pr diff 238 | delta
```

### Python Libraries

**unidiff**:
```python
from unidiff import PatchSet

diff_text = "..."
patch = PatchSet(diff_text)

for file in patch:
    print(f"File: {file.path}")
    for hunk in file:
        for line in hunk:
            if line.is_added:
                print(f"  +Line {line.target_line_no}: {line.value}")
```

---

## Version History

- **1.0.0** (2025-12-09): Initial reference
  - Unified diff format explanation
  - Line number calculation algorithms
  - Multi-line comment ranges
  - Edge cases and pitfalls
  - Parsing examples
