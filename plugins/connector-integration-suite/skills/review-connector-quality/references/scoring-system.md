# Quality Scoring System

## Scoring Formula

```
Quality Score = 100
               - (Critical Issues × 20)
               - (Warnings × 5)
               - (Suggestions × 1)
```

**Maximum Score**: 100
**Minimum Score**: 0

## Issue Severity Levels

### 1. Critical Issues (20 points each)
Issues that **BLOCK approval** regardless of final score.

#### List of Critical Issues

**A. Architecture Violations**
- ❌ Using `RouterData` instead of `RouterDataV2`
- ❌ Using `ConnectorIntegration` instead of `ConnectorIntegrationV2`
- ❌ Importing from `hyperswitch_domain_models` instead of `domain_types`
- ❌ Missing generic type parameter `<T>` on connector struct

**B. Security Violations**
- ❌ Unsafe code blocks (`unsafe { }`)
- ❌ Hardcoded credentials or API keys
- ❌ Unwrap() calls on fallible operations (`.unwrap()` without justification)
- ❌ Exposing secrets in logs or errors

**C. Reference ID Violations**
- ❌ Hardcoded reference IDs (e.g., `"hardcoded_id_123"`)
- ❌ Mutating reference IDs (modifying extracted IDs)
- ❌ Missing reference ID extraction from responses

**D. Amount Handling Violations**
- ❌ Using primitive types (`i64`, `f64`) instead of `MinorUnit`
- ❌ Missing amount converter declaration in `create_all_prerequisites!`
- ❌ Manual amount calculations instead of using converter

**E. Status Mapping Violations**
- ❌ Unknown statuses mapped to `Failed` instead of `Pending`
- ❌ Incomplete status mapping (missing common statuses)

**F. Build Failures**
- ❌ Code does not compile (`cargo build` fails)
- ❌ Missing module declarations
- ❌ Type errors

**G. Critical Pattern Violations**
- ❌ Not using macro framework (no `create_all_prerequisites!`)
- ❌ Wrong transformer implementations
- ❌ Incorrect auth type implementation

### 2. Warnings (5 points each)
Issues that reduce score but don't block approval.

#### Examples of Warnings

**A. Code Style**
- Missing doc comments on public functions
- Poor variable naming
- Long functions (>100 lines)
- Complex nested structures

**B. Error Handling**
- Incomplete error messages
- Missing error context
- Catching all errors without logging

**C. Clippy Warnings**
- Unnecessary clones
- Unused variables
- Inefficient operations

**D. Documentation**
- Missing comments on complex logic
- No examples in doc comments
- Outdated documentation

**E. Pattern Adherence**
- Suboptimal flow implementation
- Inefficient API calls
- Missing optimizations

### 3. Suggestions (1 point each)
Minor improvements that don't affect functionality.

#### Examples of Suggestions

**A. Code Organization**
- Extract helper functions
- Group related code
- Improve file structure

**B. Naming Improvements**
- More descriptive names
- Consistent naming conventions
- Better type names

**C. Documentation**
- Add examples
- Improve comments
- Add README sections

## Quality Tiers

| Score Range | Tier | Status | Action |
|-------------|------|--------|--------|
| 95-100 | Excellent ✨ | ✅ Auto-Approval | Ready for production |
| 90-94 | Good ✅ | ✅ Approval | Ready for deployment |
| 80-89 | Fair ⚠️ | ❌ Blocked | Requires fixes |
| 60-79 | Poor ❌ | ❌ Blocked | Major rework needed |
| 0-59 | Critical 🚨 | ❌ Blocked | Rebuild from scratch |

## Scoring Examples

### Example 1: Perfect Score (100/100)
```
No issues = 100 - (0 × 20) - (0 × 5) - (0 × 1) = 100
```

### Example 2: Excellent (96/100)
```
1 critical issue + 0 warnings + 4 suggestions
= 100 - (1 × 20) - (0 × 5) - (4 × 1) = 76
= 100 - 20 - 0 - 4 = 76 ❌ (This is NOT excellent)

Example 2a: 1 critical, 2 warnings, 4 suggestions
= 100 - 20 - 10 - 4 = 66 ❌ (Still blocked)

Example 2b: 0 critical, 2 warnings, 4 suggestions
= 100 - 0 - 10 - 4 = 86 ❌ (Still blocked)

Example 2c: 0 critical, 0 warnings, 4 suggestions
= 100 - 0 - 0 - 4 = 96 ✅ (Excellent - auto-approval)
```

### Example 3: Good (92/100)
```
0 critical + 1 warning + 3 suggestions
= 100 - 0 - 5 - 3 = 92 ✅ (Good - approval)
```

### Example 4: Blocked (85/100)
```
0 critical + 3 warnings + 0 suggestions
= 100 - 0 - 15 - 0 = 85 ❌ (Blocked - requires fixes)
```

### Example 5: Critical (45/100)
```
2 critical + 5 warnings + 0 suggestions
= 100 - 40 - 25 - 0 = 35 ❌ (Critical - rebuild required)
```

## Scoring Strategy

### For Reviewers

1. **First Pass**: Identify all critical issues (these auto-block)
2. **Second Pass**: Count warnings and suggestions
3. **Calculate Score**: Apply formula
4. **Make Decision**:
   - Score ≥ 90 → APPROVE
   - Score < 90 → BLOCK

### For Implementation Agent

**Understanding Feedback**:
- **Critical Issues**: MUST fix (auto-blocking)
- **Warnings**: SHOULD fix (unless valid reason not to)
- **Suggestions**: NICE to fix (can defer to later)

**Priority Order**:
1. Fix ALL critical issues first (score impact: -20 each)
2. Fix warnings (score impact: -5 each)
3. Address suggestions (score impact: -1 each)

**Minimum for Approval**: 90 points

## Common Scoring Scenarios

### Scenario A: First Implementation
**Issues Found**:
- Using RouterData instead of RouterDataV2 (CRITICAL: -20)
- Missing generic parameter (CRITICAL: -20)
- Primitive amount types (CRITICAL: -20)
- Missing error handling (WARNING: -5)

**Score**: 100 - 60 - 5 = 35 ❌ (Critical - blocked)

### Scenario B: After Fixes
**Issues Remaining**:
- Unknown status mapped to Failed (CRITICAL: -20)
- Missing doc comments (WARNING: -5)
- Long function (>100 lines) (WARNING: -5)
- Poor variable naming (SUGGESTION: -1)

**Score**: 100 - 20 - 10 - 1 = 69 ❌ (Poor - blocked)

### Scenario C: Ready for Approval
**Issues Remaining**:
- Clippy warning about unused variable (WARNING: -5)
- Missing doc comment on helper (SUGGESTION: -1)
- Inconsistent naming in one place (SUGGESTION: -1)

**Score**: 100 - 0 - 5 - 2 = 93 ✅ (Good - approved)

### Scenario D: Auto-Approval
**Issues Remaining**:
- None

**Score**: 100 ✅ (Excellent - approved)

## Score Validation

### Before Finalizing Review

**Double-Check**:
- [ ] All critical issues identified (highest priority)
- [ ] Score calculated correctly
- [ ] Decision matches score (≥90 = approve, <90 = block)
- [ ] Feedback includes exact file:line locations
- [ ] Required fixes clearly specified

### Common Scoring Errors

❌ **Forgetting Unknown Status Mapping**
```
Many connectors miss this critical rule:
Unknown status → Pending (NOT Failed)
This is a CRITICAL violation (-20 points)
```

❌ **Not Counting All Issues**
```
Reviewer might miss some critical issues
Always do multiple passes:
Pass 1: Architecture compliance
Pass 2: Security violations
Pass 3: Reference IDs
Pass 4: Amount handling
Pass 5: Status mapping
Pass 6: Code quality
```

❌ **Wrong Severity Assignment**
```
Unwrap() on fallible operation = CRITICAL (-20)
Not WARNING (-5)
```

❌ **Calculating Score Wrong**
```
Formula is:
Score = 100 - (Critical × 20) - (Warnings × 5) - (Suggestions × 1)

NOT: Score = 100 - Critical - Warning - Suggestion
```

## Feedback Loop Trigger

**When Blocked (score < 90)**:
1. Create detailed review report
2. List ALL critical issues with file:line
3. Specify required fixes for each
4. Provide examples of correct code
5. Implementation agent applies fixes
6. Re-review triggered automatically

**When Approved (score ≥ 90)**:
1. Report success to user
2. Provide score breakdown
3. Note any suggestions for future improvement
4. Trigger testing phase

## Tracking Iteration History

Maintain history across iterations:

```markdown
## Iteration History

### Iteration 1
- **Score**: 45/100
- **Critical Issues**: 2 (RouterDataV2, status_mapping)
- **Warnings**: 3
- **Suggestions**: 2
- **Fixes Requested**: All critical issues

### Iteration 2
- **Score**: 72/100
- **Critical Issues Fixed**: 2
- **New Critical Issues**: 0
- **Warnings Remaining**: 2
- **Suggestions**: 2
- **Fixes Applied**: All critical issues

### Iteration 3
- **Score**: 94/100
- **Critical Issues**: 0
- **Warnings**: 2 (non-blocking)
- **Suggestions**: 2
- **Status**: ✅ APPROVED
```

## Special Cases

### Borderline Scores (88-92)

**Score 89** (Fair):
```
Should be blocked (-5 from approval threshold)
Provide detailed feedback for fixes
Most common: Fix 1-2 warnings to reach 90
```

**Score 92** (Good):
```
Approved
Good quality but room for improvement
Can proceed to testing
```

### Multiple Critical Issues

**Score 25**:
```
Multiple critical issues present
5 critical issues × 20 = -100 (but floor at 0)
Requires significant rework
```

**Strategy**: Focus on systematic fixes, not individual issues

### No Critical but Many Warnings

**Score 75**:
```
0 critical + 5 warnings = 75
Blocked due to accumulated warnings
Strategy: Fix all warnings to reach 90
```

## Quality Targets

### Target Benchmarks

**First Pass Success Rate**: >60%
- 60% of connectors should pass first review

**Average Score**: 85-95
- Typical well-implemented connector

**Auto-Approval Rate**: >50%
- 50% of connectors should achieve 95-100

### Improvement Tracking

Monitor over time:
- Average score by iteration
- Most common critical issues
- Most common warnings
- Reviewer consistency

## Reviewer Calibration

### Standardization
- All reviewers use same checklist
- Same scoring formula
- Same severity definitions

### Training
- New reviewers: Review 5 approved connectors first
- Calibration: Review same connector, compare scores
- Consistency: Regular cross-reviews

### Quality Assurance
- Senior reviewer spot-checks
- Regular calibration sessions
- Score distribution analysis

## Conclusion

The 100-point scoring system ensures:
- **Consistent** quality standards
- **Clear** approval criteria (90+)
- **Actionable** feedback (critical/warning/suggestion)
- **Measurable** improvement (score tracking)
- **Defensible** decisions (documented rationale)

**Remember**: Score ≥ 90 = APPROVED, Score < 90 = BLOCKED
**Critical Rule**: ALL critical issues must be fixed before approval