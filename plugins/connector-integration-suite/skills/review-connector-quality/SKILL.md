---
name: review-connector-quality
description: |
  Review connector code quality against UCS patterns and best practices.
  Scores implementations on 100-point scale and provides detailed feedback.
  Creates feedback loops for fixes. Critical issues auto-block approval.
  Use when reviewing connector code, checking quality, analyzing implementations,
  or validating against standards.
  Auto-activates for requests like: "review [connector] connector",
  "check code quality for", "analyze connector implementation",
  "validate [connector] code", "score connector quality".
allowed-tools: Read, Grep, Bash, Write, Glob
version: 1.0.0
---

# Review Connector Quality Skill

## Overview

Review connector implementations for UCS architecture compliance, pattern adherence, and code quality. Score on 100-point scale and either approve (≥90) or create detailed feedback loop for fixes.

## When to Use This Skill

Auto-activates for these request patterns:
- "Review [connector] connector"
- "Check code quality for [connector]"
- "Analyze connector implementation"
- "Validate [connector] code"
- "Score connector quality"

Also useful for:
- Periodic quality audits
- Pre-merge reviews
- Identifying violations before production

## Input Context

The skill receives these parameters:
- `connector_name` (required): Name of the connector
- `code_path` (required): Path to connector code directory
- `spec_path` (optional): Path to spec.md
- `iteration` (optional): Review iteration (default: 1)

## Review Process

### Phase 0: Consult References (MANDATORY)

Read quality standards and checklist:

```bash
Read(".claude/skills/review-connector-quality/references/quality-checklist.md")
Read(".claude/skills/review-connector-quality/references/scoring-system.md")
Read(".claude/skills/review-connector-quality/references/critical-violations.md")
Read(".claude/knowledge/connector_integration_guide.md")
```

Focus on:
1. **Section 6: Core UCS Architecture Rules** - Types and patterns
2. **Section 7: Quality Checklist** - Validation criteria
3. **Section 8: Reviewer Checklist** - Review standards

### Phase 1: Extract Pattern Requirements

Read specification if available:
```bash
Read(spec_path)
```

Extract requirements:
- `CreateAccessToken` (OAuth flow needed)
- `Amount Converter` type
- `Auth Type` pattern
- `Flows` supported

### Phase 2: Run Automated Checks

Execute automated validation:
```bash
# Build check
cargo build 2>&1

# Clippy linting
cargo clippy 2>&1

# Pattern violations grep
grep -r "RouterData" code_path --include="*.rs"
grep -r "hyperswitch_domain_models" code_path --include="*.rs"
```

### Phase 3: Manual Review

Review each file for:

**Architecture Compliance**:
- Uses `RouterDataV2` (NOT `RouterData`)
- Uses `ConnectorIntegrationV2` (NOT `ConnectorIntegration`)
- Imports from `domain_types` (NOT `hyperswitch_domain_models`)
- Generic type `<T>` on connector struct

**Pattern Compliance**:
- Uses macro framework (`create_all_prerequisites!`, `macro_connector_implementation!`)
- Follows flow templates
- Proper transformer implementations

**Reference ID Integrity**:
- Extracts reference IDs from responses
- NO hardcoded IDs
- NO ID mutations
- IDs used for subsequent calls

**Amount Handling**:
- Uses `MinorUnit` types (NOT i64/f64)
- Amount converter declared in `create_all_prerequisites!`
- Proper conversion logic

**Status Mapping**:
- Unknown statuses → `Pending` (NOT `Failed`)
- Refund statuses → `Refunded` (NOT `Charged`)
- Proper mapping function

**Security**:
- NO unsafe code blocks
- Credentials use `Secret<T>` wrapper
- Proper error handling

**Code Quality**:
- Uses `?` operator for error propagation
- Proper pattern matching
- Clear, readable code
- Consistent naming

### Phase 4: Calculate Quality Score

**Scoring Formula**:
```
Score = 100
       - (Critical Issues × 20)
       - (Warnings × 5)
       - (Suggestions × 1)
```

**Quality Tiers**:
- **95-100**: Excellent ✨ - Auto-approval
- **90-94**: Good ✅ - Approval
- **80-89**: Fair ⚠️ - Blocked (feedback required)
- **60-79**: Poor ❌ - Blocked (major fixes needed)
- **0-59**: Critical 🚨 - Blocked (rebuild required)

### Phase 5: Generate Review Report

Create `.claude/context/connectors/<connector_name>/review_report.md`:

```markdown
# Quality Review Report - {Connector Name}

## Summary
- **Quality Score**: {score}/100 ({tier})
- **Status**: {APPROVED/BLOCKED}
- **Iteration**: {N}
- **Date**: {timestamp}

## Scoring Breakdown
- **Critical Issues**: {count} × 20 = -{points}
- **Warnings**: {count} × 5 = -{points}
- **Suggestions**: {count} × 1 = -{points}
- **Final Score**: {score}/100

## Critical Issues (BLOCKING)
{If score < 90, list all critical issues with file:line}

### ISSUE-{N}: {Title}
- **File**: {path}:{line}
- **Severity**: CRITICAL
- **Description**: {What is wrong}
- **Required Fix**: {Exact change needed}
- **Example**: {Correct code snippet}

## Warnings (NON-BLOCKING)
{List warnings with suggestions}

### WARN-{N}: {Title}
- **File**: {path}:{line}
- **Severity**: WARNING
- **Description**: {What could be improved}
- **Suggestion**: {How to improve}

## Suggestions (NON-BLOCKING)
{List suggestions for enhancement}

## Iteration History
```yaml
iteration_1:
  score: {score}
  issues: [{ISSUE-001, ISSUE-005}]
  fixes_requested: [{RouterDataV2, status_mapping}]
iteration_2:
  score: {score}
  issues: [{WARN-001}]
  fixes_applied: [{RouterDataV2, status_mapping}]
  new_issues: [{unwrap_usage}]
```

## Automated Checks
- **Build Status**: {Pass/Fail}
- **Clippy Lints**: {count} warnings
- **Pattern Violations**: {list any found}

## Approval Criteria
To achieve score ≥ 90:
{List remaining items to fix}

## Recommendation
{APPROVED/BLOCKED} - {reason}
```

### Phase 6: Decision

**If score ≥ 90**: APPROVED
- Report success
- Ready for testing phase
- Code can be deployed

**If score < 90**: BLOCKED
- Create detailed feedback loop
- Implementation agent applies fixes
- Re-review required

## Examples

### Standalone Usage

**User**: "Review the connector code at backend/connector-integration/src/connectors/worldpay/"

**Skill Action**:
1. Reads all connector files
2. Runs automated checks
3. Reviews for violations
4. Calculates quality score
5. Creates detailed report

**Output**: Approval or detailed feedback with specific fixes

### Orchestrated Usage

Called by `/connector-integrate` after code generation:
1. Reviews generated code
2. Scores quality
3. If approved: triggers `test-connector-integration`
4. If blocked: triggers feedback loop

## Integration

**Prerequisites**:
- Code generated by `generate-connector-code` skill

**Dependents**:
- Triggers feedback loop to `generate-connector-code` skill (fix mode)
- If approved: triggers `test-connector-integration` skill
- `/connector-integrate` orchestrates this as Phase 4

**Command Integration**: The `/connector-integrate` command invokes this skill for review phase.

## References

- Quality Checklist: `.claude/skills/review-connector-quality/references/quality-checklist.md`
- Scoring System: `.claude/skills/review-connector-quality/references/scoring-system.md`
- Critical Violations: `.claude/skills/review-connector-quality/references/critical-violations.md`
- Integration Guide: `.claude/knowledge/connector_integration_guide.md`