---
name: generate-connector-code
description: |
  Generate production-ready Rust connector code following UCS architecture
  patterns. Supports both initial generation and fix mode based on review
  feedback. Uses macro-based implementation with systematic error resolution.
  Use when implementing connectors, generating Rust code, or fixing connector
  issues from review feedback.
  Auto-activates for requests like: "implement [connector] connector",
  "generate connector code for", "write Rust code for [connector]",
  "create connector implementation", "fix connector code".
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 1.0.0
---

# Generate Connector Code Skill

## Overview

Generate production-ready, macro-based Rust code for payment connectors following UCS (Universal Connector Service) architecture patterns. Supports both initial generation and fix mode based on review feedback.

**Enhanced with Scaffolding**: This skill includes a **quick scaffolding mode** that generates connector boilerplate using proven templates from the Grace ecosystem, auto-detects flows, and updates all necessary integration files in one command.

## When to Use This Skill

Auto-activates for these request patterns:
- "Implement [connector] connector"
- "Generate connector code for [connector]"
- "Write Rust code for [connector]"
- "Create connector implementation"
- "Fix connector code based on review"

**Scaffolding Mode** (Quick Start):
- "Scaffold [connector] connector"
- "Generate boilerplate for [connector]"
- "Create connector scaffolding"
- "Initialize new connector [name]"
- "Set up connector structure for [name]"

Also useful for:
- Applying fixes from review feedback
- Updating connector implementations
- Regenerating code with new patterns
- Quick connector structure creation
- Flow auto-detection and implementation

## Input Context

The skill receives these parameters:
- `connector_name` (required): Name of the connector
- `spec_path` (required): Path to spec.md
- `implementation_plan_path` (required): Path to implementation_plan.md
- `mode` (required): "generate" (first time) or "fix" (applying review feedback)
- `review_report_path` (optional): Path to review_report.md (only for fix mode)

**Scaffolding Mode** parameters:
- `connector_name` (required): Name in snake_case (e.g., "stripe")
- `base_url` (required): Base URL for the connector API
- `scaffold_mode` (optional): Set to true for quick scaffolding

## Process

### Phase 0: Consult References (MANDATORY)

Read the UCS architecture and pattern guides:

```bash
Read(".claude/skills/generate-connector-code/references/ucs-architecture.md")
Read(".claude/skills/generate-connector-code/references/macro-patterns.md")
Read(".claude/skills/generate-connector-code/references/transformer-patterns.md")
Read(".claude/knowledge/connector_integration_guide.md")
```

Focus on:
1. **Section 6: Core UCS Architecture Rules** - Correct types and patterns
2. **Section 8: Coder Guidelines** - Implementation standards
3. **Macro Patterns** - Template usage

### Phase 0.5: Scaffolding Detection (Optional)

If `scaffold_mode` is true, run scaffolding workflow:

```bash
# Use add_connector.sh script for quick scaffolding
bash .claude/skills/generate-connector-code/scripts/add_connector.sh \
  --list-flows  # Display available flows

bash .claude/skills/generate-connector-code/scripts/add_connector.sh \
  {connector_name} {base_url} \
  --force -y  # Auto-create connector with all flows
```

**What Scaffolding Does**:
1. Auto-detects all available flows from ConnectorServiceTrait
2. Generates connector boilerplate using templates
3. Updates all integration files (protobuf, domain types, etc.)
4. Creates test scaffolding
5. Validates compilation

**Scaffolding Output**:
- Connector files with all flows stubbed out
- Updated module declarations
- Config file additions
- Validation of compilation

### Phase 1: Read Specification & Plan

For **generate mode**:
```bash
Read(spec_path)
Read(implementation_plan_path)
```

For **fix mode**:
```bash
Read(review_report_path)
```

The implementation plan contains final decisions:
- Auth Type (from plan)
- Amount Converter (from plan)
- Flow Mapping (from plan)
- Special Instructions (from plan)

### Phase 2: Generate Code Structure

Create main connector file:

```rust
// backend/connector-integration/src/connectors/{connector_name}.rs

use domain_types::router_data_v2::RouterDataV2;
use interfaces::connector_integration_v2::ConnectorIntegrationV2;
use crate::connectors::{connector_name}::transformers::{ConnectorName, PaymentFlowData};

struct {ConnectorName}<T> { }

impl<T: crate::utils:: jwt::JwtSigner, H: crate::utils::hypervisor_http_client::Hypervisor>
    ConnectorIntegrationV2<T, H> for {ConnectorName}<T>
{
    // Implementation using macro framework
}
```

### Phase 3: Generate Transformers

Create request/response transformers:

```rust
// backend/connector-integration/src/connectors/{connector_name}/transformers.rs

use crate::connectors::{connector_name}::transformers::PaymentFlowData;

pub struct PaymentFlowData { }

// Request Transformer
impl<T> From<&RouterDataV2<T>> for PaymentFlowData where T: Debug {
    fn from(data: &RouterDataV2<T>) -> Self {
        // Transform RouterData to connector-specific format
    }
}

// Response Transformer
impl<T> From<ConnectorNameResponse> for types::RouterResponse<T> where T: Debug {
    fn from(response: ConnectorNameResponse) -> Self {
        // Transform connector response to UCS types
    }
}
```

### Phase 4: Apply Macro Patterns

Use macro framework for boilerplate:

```rust
// Foundation
macros::create_all_prerequisites!(
    connector_name: {ConnectorName},
    api: [
        (flow: Authorize, ...),
        (flow: Capture, ...),
        (flow: Refund, ...),
    ],
    amount_converters: [amount_converter: {ConverterType}],
);

// Flow Implementations
macros::macro_connector_implementation!(
    connector: {ConnectorName},
    flow_name: Authorize,
    resource_common_data: PaymentFlowData,
    // ... configuration
);
```

### Phase 5: Update Module Declarations

Update `.claude/commands/connectors.rs`:
```rust
pub mod {connector_name};

#[cfg(feature = "connector_{connector_name}")]
pub use {connector_name}::ConnectorName;
```

Update `config/development.toml`:
```toml
[{connector_name}]
base_url = "https://api.{connector_name}.com"
```

### Phase 6: Build & Resolve Errors

Run build and systematically resolve all errors:
```bash
cargo build 2>&1 | tee build_output.txt
```

**Systematic Error Resolution**:
1. Capture ALL errors (not one-by-one)
2. Analyze error dependency graph
3. Categorize: Missing declarations → Type mismatches → Logic errors
4. Fix in optimal order (root causes first)
5. Expected: 2-3 rebuild cycles

### Phase 7: For Fix Mode

Apply fixes from review report:
```bash
Read(review_report_path)

# Extract all CRITICAL issues with file:line locations
# Apply each fix exactly as specified
# Re-run cargo build to validate
```

## Critical Rules

1. **Types**: Use `RouterDataV2` and `ConnectorIntegrationV2` (NOT legacy types)
2. **Imports**: Import from `domain_types` (NOT `hyperswitch_domain_models`)
3. **Amounts**: Use `MinorUnit` converter (NOT primitives like i64/f64)
4. **Reference IDs**: Extract from router_data (NEVER hardcode or mutate)
5. **Status Mapping**: Unknown → `Pending`, Refund statuses → `Charged`
6. **Unsafe Code**: NEVER allowed
7. **Errors**: Use `?` operator for error handling
8. **Generics**: Add `<T>` to connector struct for trait bounds
9. **Macro Usage**: Use macro framework for boilerplate
10. **Declarations**: Update connectors.rs and development.toml

## Output

Creates these artifacts:
- **Main File**: `backend/connector-integration/src/connectors/<name>.rs`
- **Transformers**: `backend/connector-integration/src/connectors/<name>/transformers.rs`
- **Module Updates**: connectors.rs
- **Config Updates**: config/development.toml
- **Build Status**: All errors resolved

## Examples

### Standalone Usage

**User**: "Fix the Stripe connector based on review at .claude/context/connectors/stripe/review_report.md"

**Skill Action**:
1. Reads review report
2. Extracts critical issues
3. Applies fixes systematically
4. Re-runs build
5. Ensures all issues resolved

### Scaffolding Usage (Quick Start)

**User**: "Scaffold a new connector called 'worldpay' for https://api.worldpay.com"

**Skill Action**:
1. Runs add_connector.sh scaffolding script
2. Auto-detects all available flows
3. Generates connector boilerplate with all flows
4. Updates integration files (protobuf, domain types, etc.)
5. Creates test scaffolding
6. Validates compilation
7. Provides implementation guidance

**Output**:
- `backend/connector-integration/src/connectors/worldpay.rs`
- `backend/connector-integration/src/connectors/worldpay/transformers.rs`
- Updated module declarations
- Updated config files
- Compilation validated

**Next Steps Provided**:
1. Implement request/response transformers in transformers.rs
2. Update API endpoints and logic in main connector file
3. Run cargo check to validate

### Orchestrated Usage

Called by `/connector-integrate` after planning:
1. Consumes spec and plan
2. Generates code (or scaffolds if requested)
3. Runs build validation
4. Triggers `review-connector-quality` skill

## Integration

**Prerequisites**:
- Specification from `research-api-docs` skill
- Implementation plan from `plan-connector-implementation` skill

**Dependents**:
- `review-connector-quality` consumes generated code
- `/connector-integrate` orchestrates this as Phase 3

**Command Integration**: The `/connector-integrate` command invokes this skill for code generation phase.

## References

- UCS Architecture: `.claude/skills/generate-connector-code/references/ucs-architecture.md`
- Macro Patterns: `.claude/skills/generate-connector-code/references/macro-patterns.md`
- Transformer Patterns: `.claude/skills/generate-connector-code/references/transformer-patterns.md`
- Integration Guide: `.claude/knowledge/connector_integration_guide.md`
- Flow Templates: `.claude/skills/generate-connector-code/references/flow-templates/`

## Scaffolding Tools

- Scaffolding Script: `.claude/skills/generate-connector-code/scripts/add_connector.sh`
- Connector Template: `.claude/skills/generate-connector-code/scripts/connector.rs.template`
- Transformers Template: `.claude/skills/generate-connector-code/scripts/transformers.rs.template`
- Test Template: `.claude/skills/generate-connector-code/scripts/test.rs.template`
- Macro Templates Guide: `.claude/skills/generate-connector-code/scripts/macro_templates.md`

**Scaffolding Features**:
- Auto-flow detection from codebase
- Template-based generation
- Comprehensive file updates
- Backup and rollback support
- Compilation validation
- Future-proof (includes new flows automatically)