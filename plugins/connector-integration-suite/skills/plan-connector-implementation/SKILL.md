---
name: plan-connector-implementation
description: |
  Create detailed implementation plans for payment connectors by validating
  API specs and mapping to UCS architecture patterns. Interactive planning
  with user feedback. Use when planning connector implementations, validating
  specs, or mapping APIs to UCS patterns.
  Auto-activates for requests like: "plan implementation for [connector]",
  "create implementation strategy", "map [connector] to UCS patterns", "validate connector spec".
allowed-tools: Read, Write, Plan, AskUser
version: 1.0.0
---

# Plan Connector Implementation Skill

## Overview

Bridge the gap between research (specification) and implementation (code) by creating detailed implementation plans with interactive user validation. This skill maps API requirements to UCS architecture patterns and standardizes flow classifications.

## When to Use This Skill

Auto-activates for these request patterns:
- "Plan implementation for [connector]"
- "Create implementation strategy for [connector]"
- "Map [connector] to UCS patterns"
- "Validate the [connector] spec"

Also useful for:
- Reviewing and refining API specifications
- Confirming flow classifications before implementation
- Validating architecture decisions
- Getting user feedback on implementation approach

## Input Context

The skill receives these parameters:
- `connector_name` (required): Name of the connector
- `spec_path` (required): Path to `.claude/context/connectors/<connector_name>/spec.md`

## Process

### Phase 0: Consult References

Read integration strategy reference to understand planning patterns:

```bash
Read(".claude/skills/plan-connector-implementation/references/ucs-patterns.md")
Read(".claude/skills/plan-connector-implementation/references/amount-converters.md")
Read(".claude/skills/plan-connector-implementation/references/auth-types.md")
Read(".claude/knowledge/connector_integration_guide.md")
```

Focus on these sections:
1. **Standard Flow Definitions** - Understand flow semantics
2. **Integration Strategy** - Implementation plan template and macro framework
3. **UCS Patterns** - Architecture requirements

### Phase 1: Analysis & Flow Classification

Read the specification file:
```bash
Read(spec_path)
```

**Classify flows against standard definitions:**
1. For each flow in the spec, classify it against **26 standard flows**:
   - `Authorize`, `Capture`, `Void`, `Refund`
   - `PSync` (Payment Sync), `RSync` (Refund Sync)
   - `PreAuthenticate`, `Authenticate`, `PostAuthenticate`
   - `CreateSessionToken`, `CreateAccessToken`
   - Others as defined in flow definitions

2. **Analyze architectural choices:**
   - **Auth Type**: Map to ConnectorAuthType
   - **Amount Converter**: Based on detected format
   - **Status Mapping**: Connector → UCS AttemptStatus
   - **Complexity**: Unusual patterns or edge cases

3. **Review pattern notes** from research agent

### Phase 2: Interactive Planning (MANDATORY)

Use the `Plan` tool to validate flow classifications and strategy with the user:

```bash
Plan(
  goal: "Create a detailed implementation plan for {connector_name}",
  context: """I have analyzed the spec and classified flows. I need to confirm:
           1. Flow Classifications: [List with specific questions]
           2. Auth Type: [Detected type and mapping to ConnectorAuthType]
           3. Amount Converter: [Detected format]
           4. Status Mappings: [Connector status → Hyperswitch AttemptStatus]""",
  deliverable: "A finalized implementation plan document."
)
```

**Key Questions to Ask:**
- Flow classification ambiguity (e.g., "Is this Authorize or PreAuthenticate?")
- Status mapping confirmation
- Auth type validation
- Amount converter verification
- Special handling requirements

The `Plan` tool handles interactive dialogue automatically.

### Phase 3: Generate Implementation Plan

Create `.claude/context/connectors/<connector_name>/implementation_plan.md`:

```markdown
# Implementation Plan - {Connector Name}

## 1. Architecture Choices
- **Auth Type**: {Type} (Pattern: {Pattern Name})
- **Amount Converter**: {Converter}
- **Base URL**: {URL}
- **Merchant ID**: {If applicable}

## 2. Flow Mapping
| Flow | Endpoint | Method | Status Mapping | Request Schema |
|------|----------|--------|----------------|----------------|
| Authorize | /v1/pay | POST | succeeded→Charged | PaymentCreateRequest |
| Capture | /v1/pay/{id}/capture | POST | completed→Charged | CaptureRequest |
| Refund | /v1/refund | POST | success→Refunded | RefundRequest |
| PSync | /v1/pay/{id} | GET | succeeded→Charged | - |

## 3. Data Transformations
- **Reference ID**: Extract from `{field_name}`
- **Metadata**: Map `{connector_field}` → `{ucs_field}`
- **Customer Data**: {How to extract/store}
- **Error Mapping**: {Connector error → UCS error}

## 4. Special Instructions for Implementation
- {Connector-specific quirks}
- {Edge cases to handle}
- {Validation requirements}
- {Rate limiting considerations}

## 5. Validation Checklist
- [ ] Auth flow validated
- [ ] Amount converter confirmed
- [ ] Status mappings validated
- [ ] Flow classifications approved
- [ ] Reference ID extraction plan clear
- [ ] Error handling strategy defined
```

## Output

Creates these artifacts:
- **Primary Output**: `.claude/context/connectors/<connector_name>/implementation_plan.md`
- **Status**: Plan approved and ready for implementation

**Important**: Once created, this plan triggers the autonomous Coder-Reviewer-Tester loop:
- **Implementation Agent** generates Rust code
- **Review Agent** validates quality
- **Testing Agent** runs integration tests

## Examples

### Standalone Usage

**User**: "I have a Stripe spec at .claude/context/connectors/stripe/spec.md - create an implementation plan"

**Skill Action**:
1. Reads and analyzes the specification
2. Classifies flows (Authorize, Capture, Refund, etc.)
3. Confirms architecture choices with user
4. Creates detailed implementation plan

**Output**: Implementation plan ready for code generation

### Orchestrated Usage

Called by `/connector-integrate` after research:
1. Consumes specification from `research-api-docs` skill
2. Creates implementation plan
3. Triggers `generate-connector-code` skill

## Integration

**Prerequisites**:
- Specification must exist from `research-api-docs` skill

**Dependents**:
- `generate-connector-code` consumes this plan
- `/connector-integrate` orchestrates this as Phase 2

**Command Integration**: The `/connector-integrate` command invokes this skill after research, passing spec_path from Phase 1.

## References

- UCS Patterns: `.claude/skills/plan-connector-implementation/references/ucs-patterns.md`
- Amount Converters: `.claude/skills/plan-connector-implementation/references/amount-converters.md`
- Auth Types: `.claude/skills/plan-connector-implementation/references/auth-types.md`
- Integration Guide: `.claude/knowledge/connector_integration_guide.md`