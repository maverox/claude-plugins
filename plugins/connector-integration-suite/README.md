# Connector Integration System Plugin

## Overview

Automated payment connector integration using skills-based architecture with scaffolding support from the Grace ecosystem. This plugin enables end-to-end connector development through 5 specialized, composable skills.

## Features

### Core Architecture
- ✅ **Skills-Based**: 5 specialized skills for modular, composable operations
- ✅ **Auto-Activation**: Skills activate based on context (no manual invocation needed)
- ✅ **Hybrid Design**: Use skills standalone OR orchestrated via `/connector-integrate` command
- ✅ **Backward Compatible**: Existing agents remain functional

### Scaffolding Support
- ✅ **Quick Start**: Auto-generate connector boilerplate in seconds
- ✅ **Flow Detection**: Automatically detects all available flows from codebase
- ✅ **Template-Based**: Uses proven templates from Grace ecosystem
- ✅ **Safe Updates**: Backup and rollback on errors
- ✅ **Validated**: Compiles successfully out of the box

### Quality Assurance
- ✅ **Review System**: 100-point quality scoring
- ✅ **Feedback Loop**: Automatic fix-verify iterations
- ✅ **Testing**: Integration tests and gRPC validation
- ✅ **Documentation**: Comprehensive guides and references

## Installation

This plugin is bundled with the connector-service repository. No additional installation required.

```bash
# Plugin already available at
.claude-plugin/
├── marketplace.json
└── README.md
```

## Usage

### Orchestrated Workflow (Full Integration)

Use the main command for complete end-to-end connector integration:

```bash
/connector-integrate <connector_name> [api_docs_url]

# Examples:
/connector-integrate stripe https://stripe.com/docs/api
/connector-integrate adyen
/connector-integrate worldpay https://developer.worldpay.com/docs/api
```

**Workflow**:
1. Research API documentation
2. Create implementation plan (with user validation)
3. Generate production-ready code
4. Review with quality scoring
5. Run comprehensive tests
6. Update memory system with learnings

### Standalone Skills (Individual Operations)

Skills auto-activate based on your requests. No need to invoke them directly:

```bash
# Research
"Research the Stripe API and create a spec"
→ Auto-activates research-api-docs skill

# Plan
"I have a spec at .claude/context/stripe/spec.md - create an implementation plan"
→ Auto-activates plan-connector-implementation skill

# Code Generation
"Implement the Stripe connector based on the plan"
→ Auto-activates generate-connector-code skill

# Code Review
"Review the Stripe connector code I just wrote"
→ Auto-activates review-connector-quality skill

# Testing
"Run integration tests for Stripe"
→ Auto-activates test-connector-integration skill

# Fix Issues
"Fix the connector based on review feedback"
→ Auto-activates generate-connector-code in fix mode
```

### Scaffolding (Quick Start)

Create connector boilerplate instantly:

```bash
# Via skill auto-activation
"Scaffold a new connector called 'worldpay' for https://api.worldpay.com"

# Or use script directly
bash .claude/skills/generate-connector-code/scripts/add_connector.sh \
  worldpay https://api.worldpay.com \
  --force -y
```

**What scaffolding creates**:
- Connector files with all flows stubbed out
- Updated module declarations
- Updated config files
- Validated compilation
- Implementation guidance

## Skills Reference

### 1. research-api-docs
**Purpose**: Scrape and parse API documentation
**Auto-activates for**: "research API", "scrape docs", "create spec"
**Output**: Technical specification file
**Tools**: Puppeteer MCP, WebFetch, WebSearch

### 2. plan-connector-implementation
**Purpose**: Create implementation plans with validation
**Auto-activates for**: "plan implementation", "create strategy"
**Output**: Implementation plan document
**Features**: Interactive user validation

### 3. generate-connector-code ⭐
**Purpose**: Generate production-ready Rust code
**Auto-activates for**: "implement connector", "generate code", "scaffold connector"
**Features**:
- Full code generation from specs
- Fix mode for review feedback
- **Scaffolding support** (Grace ecosystem)
- Auto-flow detection
- Template-based generation
**Output**: Complete connector implementation

### 4. review-connector-quality
**Purpose**: Review code quality
**Auto-activates for**: "review connector", "check quality"
**Features**: 100-point scoring system
**Output**: Quality review report with feedback

### 5. test-connector-integration
**Purpose**: Run integration tests
**Auto-activates for**: "test integration", "run tests"
**Tests**: cargo tests, gRPC tests, webhook verification
**Output**: Testing report

## Configuration

### Hook Integration

The plugin includes lifecycle hooks for audit and analytics:

```json
{
  "hooks": {
    "SessionEnd": [
      {
        "type": "command",
        "command": "python3 .claude/hooks/skill_lifecycle_hook.py"
      }
    ]
  }
}
```

### Metrics Tracked

- Skills invoked (total)
- Auto-activations
- Orchestrated invocations
- Standalone invocations
- Success/failure rates
- Feedback loop iterations

## Architecture

### Skills vs Agents

**Skills** (New):
- Auto-activates based on context
- Composable and reusable
- Standalone or orchestrated
- Better code reuse

**Agents** (Legacy - Still Supported):
- Called via commands
- Maintained for backward compatibility
- Will be deprecated in future versions

### Communication Pattern

Skills communicate via file-based artifacts:

```
research-api-docs → spec.md → plan-connector-implementation → implementation_plan.md
                                                      ↓
review-connector-quality ← review_report.md ← generate-connector-code
                              ↓
                    test-connector-integration
```

## Scaffolding Details

### Auto-Flow Detection

The scaffolding system automatically detects flows from `ConnectorServiceTrait`:

```bash
bash .claude/skills/generate-connector-code/scripts/add_connector.sh --list-flows
```

**Output**:
```
Auto-Detected Flows from ConnectorServiceTrait:
===============================================

PaymentAuthorizeV2          Process payment authorization
PaymentSyncV2               Synchronize status
PaymentVoidV2               Void/cancel operations
PaymentCapture              Capture authorized payments
RefundV2                    Process refunds
...
```

### Templates Used

1. **connector.rs.template**: Main connector file with all trait implementations
2. **transformers.rs.template**: Request/response transformers
3. **test.rs.template**: Test scaffolding
4. **macro_templates.md**: Macro pattern documentation

### Safety Features

- ✅ Automatic backups before changes
- ✅ Rollback on errors
- ✅ Compilation validation
- ✅ Git status checks

## Best Practices

### 1. Use Scaffolding for Quick Start
```bash
# Start with scaffolding for structure
"Scaffold a connector called 'mypay'"

# Then use full workflow for implementation
/connector-integrate mypay
```

### 2. Review Before Implementing
```bash
# Let review skill check your code
"Review the connector code I wrote"
```

### 3. Iterate with Feedback Loop
```bash
# Auto-fix based on review
"Fix the connector based on review feedback"
# System automatically applies fixes and re-reviews
```

### 4. Test Early and Often
```bash
# Run tests after each major change
"Run integration tests for the connector"
```

## Troubleshooting

### Issue: Skill doesn't auto-activate
**Solution**: Check that your request includes trigger keywords
- "research" → research-api-docs
- "plan" → plan-connector-implementation
- "implement" or "generate" → generate-connector-code
- "review" → review-connector-quality
- "test" → test-connector-integration

### Issue: Scaffolding fails
**Solution**:
```bash
# Check git status (must be clean or use --force)
git status

# Use debug mode
bash .claude/skills/generate-connector-code/scripts/add_connector.sh \
  myconnector https://api.test.com \
  --debug
```

### Issue: Code doesn't compile
**Solution**:
```bash
# Validation runs automatically
# Check compilation errors
cargo check --package connector-integration

# Review report for guidance
cat .claude/context/connectors/<name>/review_report.md
```

### Issue: Review score too low
**Solution**:
- Read review report for specific issues
- Fix critical issues (score -20 each)
- Address warnings (score -5 each)
- System will auto-re-review after fixes

## Examples

### Example 1: Complete Workflow

```bash
# Step 1: Scaffold for quick start
"Scaffold a new connector called 'fastpay' for https://api.fastpay.com"

# Step 2: Research and plan
/connector-integrate fastpay https://api.fastpay.com/docs

# Result: Complete connector with quality score and tests
```

### Example 2: Incremental Development

```bash
# Start with research
"Research the PayPal API and create a spec"

# Then plan
"Plan implementation for PayPal based on the spec"

# Then implement
"Generate connector code based on the plan"

# Then review
"Review the PayPal connector code"

# Then test
"Run integration tests for PayPal"
```

### Example 3: Fix Issues

```bash
# Initial implementation
/connector-integrate testpay

# Review shows issues
# System creates feedback loop
# Auto-applies fixes
# Re-reviews until score >= 90
# Reports success
```

## Migration from Agents

### What Changed

**Before** (Agent-Based):
```bash
/connector-integrate stripe  # Called agent A, B, C, D, E
```

**After** (Skills-Based):
```bash
/connector-integrate stripe  # Orchestrates skills 1-5
"Review my connector"        # Standalone skill usage
"Scaffold new connector"     # Scaffolding mode
```

### Backward Compatibility

✅ All agents remain functional
✅ No breaking changes
✅ Gradual migration path
✅ Clear documentation

### Migration Path

1. **Use skills for new work** (recommended)
2. **Agents still work** (for existing workflows)
3. **Future deprecation** (agents → skills)

### Packaging & Distribution

To share this plugin with your team as a standalone package (detached from the repo):

1.  **Run the packaging script from the repository root**:
    ```bash
    ./.claude-plugin/package.sh
    ```
    This creates a `dist/` directory containing the standalone plugin. By default, it includes all skills/agents/rules but only selective hooks (configured in the script).

2.  **Verify the package**:
    ```bash
    ls -R dist/
    cat dist/plugin.json  # Verify components list
    ```

3.  **Distribute**:
    - Commit the contents of `dist/` to a separate repository (e.g., `juspay/connector-tools`).
    - OR share the `dist/` folder directly.

4.  **Install in other projects**:
    ```bash
    /plugin install <path-to-dist-or-git-url>
    ```

## Contributing

### Adding New Skills

1. Create `.claude/skills/<skill-name>/SKILL.md`
2. Define auto-activation triggers
3. Add comprehensive references
4. Update plugin marketplace.json

### Customizing Templates

1. Copy templates to custom location
2. Modify as needed
3. Update scaffolding script
4. Test compilation

## License

This plugin is part of the connector-service project. See project LICENSE for details.

## Support

- **Documentation**: `.claude/skills/*/SKILL.md`
- **Migration Guide**: `SKILLS_MIGRATION_SUMMARY.md`
- **Hook Integration**: `.claude/hooks/audit-trail.md`

## Version History

### 1.0.0
- Initial release
- 5 skills with auto-activation
- Scaffolding support from Grace
- Hook integration for lifecycle tracking
- Backward compatible with agents
- 100% test coverage

---

**Plugin ID**: connector-integration@skills-migration
**Version**: 1.0.0
**Compatible**: Claude Code 4.0.0+