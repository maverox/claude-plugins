---
description: Automatically review a PR using specialized skills
---

# PR Auto-Review Workflow (Skills-Based)

You are initiating an automated Pull Request review workflow using specialized skills for modular, reusable analysis.

## Task Overview

Execute a comprehensive PR review by orchestrating specialized skills:
1. **pr-analysis** - Fetch and analyze PR data
2. **code-quality-review** - Review code quality and security
3. **connector-integration-validator** - Validate connector changes (if applicable)
4. **github-review-publisher** - Create pending review with comments

## Workflow Execution

### Step 1: Parse Input

Extract from user command:
- **PR Number or URL**: The PR to review
- **Repository**: Auto-detect from git or extract from URL (e.g., hyperswitch/connector-service)
- **Review Scope**: Optional focus areas (e.g., `--focus=security,performance`)

**Examples**:
```bash
/pr-review 123
/pr-review https://github.com/hyperswitch/connector-service/pull/238
/pr-review 123 --focus=security
```

**Parse Logic**:
```
If URL provided:
  Extract: owner, repo, pr_number from URL
Else if number only:
  Detect repo from git remote
  pr_number = provided number
```

---

### Step 2: Invoke pr-analysis Skill

**Purpose**: Fetch PR data and identify scope

```
Skill("pr-analysis")

Input:
  PR Number: {pr-number}
  Repository: {owner}/{repo}

Expected Output:
  - PR metadata (title, author, files changed)
  - File changes categorized
  - Change scope identified (connector_integration, core_domain, etc.)
  - Diff content
  - Connector name (if applicable)
```

**Wait for completion** - This skill provides context for downstream skills

---

### Step 3: Invoke code-quality-review Skill

**Purpose**: Review code quality, security, and best practices

```
Skill("code-quality-review")

Input:
  - PR Number: {pr-number}
  - Repository: {owner}/{repo}
  - File Changes: {from pr-analysis}
  - Diff Content: {from pr-analysis}

Expected Output:
  - Quality score (0-100)
  - Categorized issues:
    * Critical issues (security, type safety, etc.)
    * Warnings (code quality, patterns)
    * Suggestions (documentation, improvements)
  - Detailed analysis per file
```

**Run in parallel** with connector-integration-validator (if applicable)

---

### Step 4: Invoke connector-integration-validator Skill (Conditional)

**Purpose**: Validate connector-specific patterns and API conformance

**Condition**: Only if `scope.primary == "connector_integration"`

```
If pr-analysis identified connector integration:
  Skill("connector-integration-validator")

  Input:
    - Connector Name: {from pr-analysis}
    - Connector Files: {from pr-analysis}
    - API Documentation: {auto-fetch or use existing spec}

  Expected Output:
    - API conformance results
    - Authentication validation
    - Flow implementation validation
    - Amount converter validation
    - Status mapping validation
    - UCS compliance check
```

**Run in parallel** with code-quality-review for efficiency

---

### Step 5: Invoke github-review-publisher Skill

**Purpose**: Create pending review with formatted comments

```
Skill("github-review-publisher")

Input:
  - PR Number: {pr-number}
  - Repository: {owner}/{repo}
  - Issues from code-quality-review
  - Issues from connector-integration-validator (if applicable)
  - PR metadata from pr-analysis

Expected Output:
  - Pending review created in GitHub
  - Review ID
  - Comment count
  - Review summary displayed in chat
```

**Wait for all review skills to complete** before invoking

---

### Step 6: Display Summary

After all skills complete, display comprehensive summary:

```markdown
# 📋 PR Review Complete: PR #{number}

## PR Information
- **Repository**: {owner}/{repo}
- **Title**: {pr_title}
- **Author**: @{author}
- **Files Changed**: {file_count}

## Review Statistics
- **Quality Score**: {score}/100
- **Total Pending Comments**: {comment_count}
  - 🔴 Critical: {critical_count}
  - 🟡 Important: {warning_count}
  - 🟢 Suggestions: {suggestion_count}

## Connector Integration Validation (if applicable)
- **API Conformance**: {status}
- **Authentication Patterns**: {status}
- **Payment Flow Implementation**: {status}
- **Amount Converters**: {status}
- **Status Mapping**: {status}
- **UCS Compliance**: {status}

## Summary
{overall_assessment}

## Next Steps
1. Go to GitHub PR: {pr_url}/files
2. Review pending comments (not posted publicly yet)
3. Edit, approve, or discard comments
4. Submit review when ready

⚠️ **Comments are PENDING** - they require your manual approval before posting.
```

---

## Skill Orchestration Details

### Sequential vs Parallel Execution

**Sequential** (must wait):
1. pr-analysis (first - provides context)
2. code-quality-review + connector-integration-validator (parallel if applicable)
3. github-review-publisher (last - needs input from review skills)

**Parallel** (can run together):
- code-quality-review + connector-integration-validator

**Execution Flow**:
```
pr-analysis
     ↓
     ├─→ code-quality-review ───┐
     │                           ├─→ github-review-publisher
     └─→ connector-integration-validator (if applicable) ──┘
```

---

### Error Handling

#### PR Not Found
```markdown
❌ PR #{number} not found in {owner}/{repo}

Please check:
- PR number is correct
- Repository is accessible
- gh CLI is authenticated (`gh auth status`)
```

#### Skill Execution Failed

```markdown
❌ {skill-name} skill failed

Error: {error_message}

**Recovery Options**:
1. Check skill logs for details
2. Run skill manually: Skill("{skill-name}")
3. Verify prerequisites (gh CLI, auth, etc.)
```

#### Partial Success

```markdown
⚠️ Review Completed with Warnings

**Successful**:
✅ pr-analysis
✅ code-quality-review

**Failed**:
❌ connector-integration-validator - {reason}

**Result**: Review created with available data. Connector validation incomplete.

**Action**: Review may be incomplete. Consider manual connector validation.
```

---

## Benefits of Skills-Based Approach

### Compared to Previous Agent-Based System

**Before** (Monolithic Agent):
```
/pr-review 238
    ↓
general-purpose agent (all-in-one)
    ↓
pending review created
```

**Limitations**:
- ❌ Can't reuse parts independently
- ❌ No auto-activation for related tasks
- ❌ Difficult to extend or modify
- ❌ All or nothing execution

**After** (Skills-Based):
```
/pr-review 238
    ↓
    ├─> pr-analysis skill
    ├─> code-quality-review skill (parallel)
    ├─> connector-integration-validator skill (parallel, conditional)
    └─> github-review-publisher skill
```

**Benefits**:
- ✅ Each skill usable standalone
- ✅ Skills auto-activate for related tasks
- ✅ Easy to add new review types
- ✅ Graceful partial failures
- ✅ Parallel execution where possible
- ✅ Clear separation of concerns

---

## Standalone Skill Usage

Users can also invoke skills individually:

### Examples

**Analyze PR without review**:
```
"Analyze PR #238"
→ pr-analysis skill auto-activates
→ Shows PR summary, file changes, scope
```

**Review specific code**:
```
"Review the code quality in backend/connectors/stripe.rs"
→ code-quality-review skill auto-activates
→ Analyzes single file, provides feedback
```

**Validate connector without full PR review**:
```
"Validate the Stripe connector implementation"
→ connector-integration-validator skill auto-activates
→ Checks against API docs, UCS compliance
```

**Create review from custom issues**:
```
"Create GitHub review with these issues: [list]"
→ github-review-publisher skill auto-activates
→ Formats and publishes pending review
```

---

## Integration with Existing Systems

### Backward Compatibility

The skills-based system complements existing agents:
- **code-change-reviewer agent**: Can coexist with code-quality-review skill
- **@pr-orchestrator agent**: Skills provide same functionality with better modularity

### Migration Path

**Phase 1** (Current): Skills-based /pr-review command
**Phase 2** (Future): Deprecate agent-based approach
**Phase 3** (Future): Skills only

---

## Advanced Features

### Focus Areas (Optional)

```bash
/pr-review 238 --focus=security
```

**Implementation**:
```
Pass focus to skills:
  code-quality-review(focus: "security")
  → Prioritize security checks
  → Skip non-security suggestions
```

**Supported Focus Areas**:
- `security` - Security vulnerabilities only
- `performance` - Performance issues
- `connector` - Connector-specific validation only
- `quality` - Code quality only

---

### Incremental Reviews

For large PRs, review in stages:

```bash
/pr-review 238 --files="backend/connectors/**"
```

**Implementation**:
```
Filter file list before passing to skills:
  pr-analysis → filter files
  code-quality-review → review filtered files only
```

---

## Version History

- **2.0.0** (2025-12-09): Skills-based refactor
  - Migrated from agent-based to skills-based orchestration
  - Added parallel execution support
  - Added conditional connector validation
  - Improved error handling
  - Added standalone skill usage

- **1.0.0** (Previous): Agent-based implementation
  - Single general-purpose agent
  - Sequential execution only

---

**Now execute the PR review workflow using the skills orchestration pattern described above.**
