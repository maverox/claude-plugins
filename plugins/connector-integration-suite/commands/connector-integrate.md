# Connector Integration Command

Complete end-to-end connector integration using specialized skills (hybrid architecture: command + skills).

## Usage

```bash
/connector-integrate <connector_name> [api_docs_url]
```

## Examples

```bash
# With API URL
/connector-integrate stripe https://stripe.com/docs/api

# Auto-discover docs
/connector-integrate adyen

# Specific connector with direct docs
/connector-integrate worldpay https://developer.worldpay.com/docs/api
```

## What This Does

Orchestrates a **5-phase workflow** using specialized **skills** and memory systems:

### Phase 0: Context Loading
- Loads global learnings and common issues
- Injects past mistakes to avoid repeating them

### Phase 1: Research (research-api-docs skill)
- Scrapes API documentation
- Extracts payment flows, endpoints, schemas
- Creates technical specification
- **Output**: `.claude/context/connectors/<name>/spec.md`

### Phase 2: Planning (plan-connector-implementation skill)
- Reads specification from Phase 1
- Maps to UCS patterns
- Interactive user validation
- **Output**: `.claude/context/connectors/<name>/implementation_plan.md`

### Phase 3: Implementation (generate-connector-code skill)
- Reads specification and plan from previous phases
- Generates production-ready Rust code
- Follows UCS architecture patterns
- Updates module declarations
- **Output**: Rust files in `backend/connector-integration/src/connectors/<name>/`

### Phase 4: Review (review-connector-quality skill)
- Reviews generated code
- Checks for critical violations
- Scores quality (0-100)
- **Output**: `.claude/context/connectors/<name>/review_report.md`
- **Decision**: Approve (score >= 90) or Feedback Loop (score < 90)

### Phase 5: Feedback Loop (if needed)
If review score < 90:
- review-connector-quality creates detailed fix instructions
- generate-connector-code reads review report and applies fixes (fix mode)
- review-connector-quality re-reviews the fixed code
- Repeat up to 3 iterations until score >= 90

### Phase 6: Testing (test-connector-integration skill)
- Runs integration tests (`cargo test`)
- Executes gRPC tests (`grpcurl`) for all flows
- Verifies webhook handling
- **Output**: `.claude/context/connectors/<name>/testing_report.md`

### Phase 6: Learning (Memory System)
- Extracts new patterns and failures from the session
- Updates `global_learnings.md` and `common-issues.md`
- Ensures continuous improvement for future integrations

## Workflow Implementation

When this command is invoked, execute the following workflow:

### Step 0: Load Memory Context

```
1. Read Global Learnings:
   cat .claude/rules/learnings/global.md

2. Read Common Issues:
   cat .claude/rules/learnings/common-issues.md

3. Inject into Context:
   "Use these learnings to guide your decisions. Pay special attention to 'Common Issues' to avoid critical violations."
```

### Step 1: Setup

```
1. Extract parameters from command:
   - connector_name: <name>
   - api_docs_url: [url] (optional)

2. Create context directory:
   mkdir -p .claude/context/connectors/<name>/

3. Initialize status tracking:
   Create .claude/context/connectors/<name>/status.yaml
```

### Step 2: Invoke research-api-docs Skill

```
Skill(skill: "research-api-docs")

Context:
- connector_name: {connector_name}
- api_docs_url: {api_docs_url if provided, else 'auto-discover'}
```

**Skill Action**:
- Auto-activates for this connector integration workflow
- **SEARCHES** for official API documentation using WebSearch() (primary)
- **FALLS BACK** to mcp__firecrawl__firecrawl_search if WebSearch fails
- **SCRAPES** documentation using WebFetch() for controlled extraction
- **FALLS BACK** to mcp__firecrawl__firecrawl_scrape for complex layouts
- Extracts all payment flows, endpoints, and schemas
- Identifies authentication method and amount formats
- Creates comprehensive specification file

**Output**: `.claude/context/connectors/{connector_name}/spec.md`

**Wait for completion**, then verify spec file exists and contains all required sections.

### Step 3: Invoke plan-connector-implementation Skill (Interactive)

```
Skill(skill: "plan-connector-implementation")

Context:
- connector_name: {connector_name}
- spec_path: .claude/context/connectors/{connector_name}/spec.md
```

**Skill Action**:
- Auto-activates for implementation planning
- Analyzes specification and classifies flows
- **INTERACTIVELY** validates with user (uses AskUser tool)
- Maps requirements to UCS patterns
- Creates detailed implementation plan

**Output**: `.claude/context/connectors/{connector_name}/implementation_plan.md`

**Wait for completion**, then verify:
- Implementation plan created
- User confirmed all flow classifications and architecture choices

### Step 4: Invoke generate-connector-code Skill

```
Skill(skill: "generate-connector-code")

Context:
- connector_name: {connector_name}
- spec_path: .claude/context/connectors/{connector_name}/spec.md
- implementation_plan_path: .claude/context/connectors/{connector_name}/implementation_plan.md
- mode: generate
```

**Skill Action**:
- Auto-activates for connector code generation
- Reads specification and implementation plan
- Generates `{connector_name}.rs` with macro-based implementation
- Generates `transformers.rs` with request/response transformers
- Updates module declarations in connectors.rs
- Updates config/development.toml
- Runs `cargo build` and systematically resolves errors

**Output**:
- `backend/connector-integration/src/connectors/{connector_name}.rs`
- `backend/connector-integration/src/connectors/{connector_name}/transformers.rs`
- Updated connectors.rs and development.toml

**Wait for completion**, then verify:
- All code files created
- `cargo build` succeeds

### Step 5: Invoke review-connector-quality Skill

```
Skill(skill: "review-connector-quality")

Context:
- connector_name: {connector_name}
- code_path: backend/connector-integration/src/connectors/{connector_name}/
- iteration: 1
```

**Skill Action**:
- Auto-activates for code quality review
- Reviews generated code for UCS architecture compliance
- Checks for critical violations (RouterDataV2, reference IDs, amounts, status mapping)
- Runs automated checks (cargo build, clippy)
- Calculates quality score (0-100)
- Creates detailed review report

**Output**: `.claude/context/connectors/{connector_name}/review_report.md`

**Decision**:
- If score >= 90: APPROVE → Continue to testing
- If score < 90: BLOCK → Enter feedback loop

**Wait for completion**, then:
1. Read review report
2. Extract quality score
3. Make decision

### Step 5: Decision Point

```
IF score >= 90:
  Report SUCCESS to user
  Show quality score, files created, next steps
  END workflow

ELSE (score < 90):
  Enter FEEDBACK LOOP (max 3 iterations)
```

### Step 6: Feedback Loop (if needed)

```
iteration = 1
max_iterations = 3

WHILE score < 90 AND iteration < max_iterations:
  iteration += 1

  # Invoke generate-connector-code in Fix Mode
  Skill(skill: "generate-connector-code")

  Context:
  - connector_name: {connector_name}
  - mode: fix
  - review_report_path: .claude/context/connectors/{connector_name}/review_report.md
  - iteration: {iteration}

  Action:
  - Reads review report
  - Extracts all CRITICAL issues with file:line locations
  - Applies each fix exactly as specified
  - Re-runs cargo build to validate

  # Wait for fixes, then re-review
  Skill(skill: "review-connector-quality")

  Context:
  - connector_name: {connector_name}
  - code_path: backend/connector-integration/src/connectors/{connector_name}/
  - iteration: {iteration}

  Action:
  - Re-reviews code after fixes
  - Checks if previous CRITICAL issues were resolved
  - Calculates new quality score
  - Updates review report with iteration history

  # Read new score
  Read review report
  Extract new score

  IF score >= 90:
    Report SUCCESS
    BREAK
  ELSE IF iteration >= max_iterations:
    Report FAILURE (max iterations exceeded)
    BREAK

### Step 7: Invoke test-connector-integration Skill

```
Skill(skill: "test-connector-integration")

Context:
- connector_name: {connector_name}
- implementation_plan_path: .claude/context/connectors/{connector_name}/implementation_plan.md
```

**Skill Action**:
- Auto-activates for connector testing
- Runs integration tests (`cargo test {connector_name}_integration_test`)
- Executes gRPC tests for all flows using grpcurl
- Verifies webhook handling (if applicable)
- Creates comprehensive testing report

**Output**: `.claude/context/connectors/{connector_name}/testing_report.md`

**Wait for completion**, then verify testing report exists and shows PASS status.

### Step 8: Learning & Memory Update

```
Task(
  description: "Extract learnings and update memory",
  prompt: "Review the session and update the memory system.
  
  Input Context:
  - review_report: .claude/context/connectors/{connector_name}/review_report.md
  - global_learnings: .claude/rules/learnings/global.md
  - common_issues: .claude/rules/learnings/common-issues.md
  
  Process:
  1. Identify any NEW patterns or quirks discovered (e.g., auth headers, status mappings).
  2. Identify any failures that occurred (from review report).
  3. Update 'global_learnings.md' if a new pattern is found.
  4. Update 'common-issues.md' if a new common failure is found (increment frequency or add new issue).
  
  Output:
  - Update .claude/rules/learnings/global.md (if needed)
  - Update .claude/rules/learnings/common-issues.md (if needed)
  - Summary of what was learned."
)
```

## User Progress Updates

Provide real-time updates at each phase:

```
🚀 Starting connector integration: {connector_name}

🧠 Phase 0: Context Loading
   Loading global learnings...
   Loading common issues...
   ✅ Memory context injected

🔍 Phase 1/3: Research
   Launching connector-research agent...
   Scraping API documentation...
   ✅ Specification created: {line_count} lines
   📄 File: .claude/context/connectors/{connector_name}/spec.md

🔨 Phase 2/3: Implementation
   Launching connector-implementation agent...
   Generating connector code...
   ✅ Files created: {connector_name}.rs, {connector_name}/transformers.rs
   ✅ Build successful

📋 Phase 3/3: Review
   Launching connector-review agent...
   Running quality checks...

   [If score >= 90]
   ✅ Quality Score: {score}/100 ({rating})
   ✅ Status: APPROVED

   [If score < 90]
   ⚠️  Quality Score: {score}/100
   ❌ Status: BLOCKED - {critical_count} critical issues

   [If BLOCKED]
   🔄 Feedback Loop (Iteration {iteration}/{max_iterations})
      Sending fixes to implementation agent...
      ✅ Fixes applied
      Re-running review...
      [Loop continues...]

🧠 Phase 5: Learning
   Extracting new patterns...
   Updating memory system...
   ✅ Global learnings updated

✨ SUCCESS!
   Connector: {connector_name}
   Quality Score: {final_score}/100 ({rating})
   Time: {duration} minutes
   Iterations: {iteration_count}

   📁 Files Created:
   - backend/connector-integration/src/connectors/{connector_name}.rs
   - backend/connector-integration/src/connectors/{connector_name}/transformers.rs

   📄 Reports:
   - Specification: .claude/context/connectors/{connector_name}/spec.md
   - Review: .claude/context/connectors/{connector_name}/review_report.md

   🎯 Next Steps:
   1. Write tests in test.rs
   2. Add credentials to .github/test/creds.json
   3. Run: cargo nextest run --package connector-integration
   4. Create PR
```

## Status Tracking

Maintain workflow state in: `.claude/context/connectors/<name>/status.yaml`

```yaml
connector: {connector_name}
started_at: {timestamp}
updated_at: {timestamp}

phases:
  research:
    status: completed | in_progress | failed
    completed_at: {timestamp}
    output: .claude/context/connectors/{connector_name}/spec.md

  implementation:
    status: completed | in_progress | failed
    iteration: {N}
    completed_at: {timestamp}
    outputs:
      - backend/connector-integration/src/connectors/{connector_name}.rs
      - backend/connector-integration/src/connectors/{connector_name}/transformers.rs

  review:
    status: completed | in_progress | failed
    iteration: {N}
    completed_at: {timestamp}
    scores:
      - iteration: 1, score: {score}, status: {approved|blocked}
      - iteration: 2, score: {score}, status: {approved|blocked}
    final_score: {score}
    final_status: {approved|blocked}

overall_status: success | in_progress | failed
final_score: {score}
total_iterations: {N}
duration_minutes: {duration}
```

## Error Handling

### Research Phase Fails
```
If connector-research fails:
  - Report error to user
  - Suggest: "Try providing a direct API documentation URL"
  - Show: Research agent error message
  - Exit with error
```

### Implementation Phase Fails
```
If connector-implementation fails:
  - Report error to user
  - Show: Compiler errors (if build failed)
  - Suggest: Manual intervention needed
  - Exit with error
```

### Review Phase Fails
```
If connector-review fails:
  - Report error to user
  - Show: Review error message
  - Exit with error
```

### Max Iterations Exceeded
```
If iterations >= 3 AND score < 90:
  - Report: "Failed to achieve passing score after 3 iterations"
  - Show: Final review report
  - List: Remaining critical issues
  - Suggest: Manual intervention needed
  - Exit with partial success
```

## Expected Timeline

- **Research**: 5-10 minutes
- **Implementation**: 10-20 minutes
- **Review**: 3-5 minutes
- **Feedback Loop** (if needed): 5-15 minutes per iteration
- **Total**: 20-50 minutes for complete integration

## Files Created

```
.claude/context/connectors/<name>/
├── spec.md               # Technical specification (research output)
├── review_report.md      # Quality review (review output)
└── status.yaml           # Workflow state

backend/connector-integration/src/connectors/
├── <name>.rs             # Main connector implementation (implementation output)
└── <name>/
    └── transformers.rs   # Request/response transformers (implementation output)
```

## Success Criteria

Mark as SUCCESS when:
- ✅ All 3 phases completed
- ✅ Quality score >= 90
- ✅ cargo build succeeds
- ✅ All files created
- ✅ Module declarations updated

## Skills Used

This command orchestrates these **specialized skills**:

1. **research-api-docs** (`.claude/skills/research-api-docs/SKILL.md`)
   - Scrapes API documentation
   - Creates technical specification
   - Auto-activates for documentation requests

2. **plan-connector-implementation** (`.claude/skills/plan-connector-implementation/SKILL.md`)
   - Creates implementation plans
   - Interactive validation with user
   - Maps API to UCS patterns

3. **generate-connector-code** (`.claude/skills/generate-connector-code/SKILL.md`)
   - Generates production-ready Rust code
   - Applies fixes (in fix mode)
   - Systematic error resolution

4. **review-connector-quality** (`.claude/skills/review-connector-quality/SKILL.md`)
   - Reviews code quality (100-point scale)
   - Creates feedback reports
   - Auto-activates for code review requests

5. **test-connector-integration** (`.claude/skills/test-connector-integration/SKILL.md`)
   - Runs integration tests
   - Executes gRPC tests
   - Verifies webhook handling

**Benefits of Skills Architecture**:
- ✅ **Composable**: Skills can be used standalone or orchestrated
- ✅ **Auto-activation**: Skills activate based on context (e.g., "review this connector" → review skill)
- ✅ **Reusable**: Each skill has focused expertise and can be called independently
- ✅ **Maintainable**: Clear separation of concerns with dedicated references

**Backward Compatibility**: During transition, agents (`.claude/agents/`) remain functional but skills are preferred for new workflows.

## Resume Capability (Future)

If workflow is interrupted, can resume from status.yaml:
```bash
/connector-integrate <name> --resume
```

This would:
1. Read status.yaml
2. Identify last completed phase
3. Resume from next phase
