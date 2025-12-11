# Connector Scaffolding Guide

## Overview

The `generate-connector-code` skill includes a **quick scaffolding mode** that generates connector boilerplate using proven templates from the Grace ecosystem. This allows you to create a complete connector structure in seconds.

## What is Scaffolding?

Scaffolding is a **quick-start mechanism** that:
- Auto-detects all available flows from the codebase
- Generates connector boilerplate using proven templates
- Updates all necessary integration files
- Creates test scaffolding
- Validates compilation
- Provides next-steps guidance

**Use scaffolding when**:
- You want to quickly create a new connector
- You need a starting point with all flows stubbed out
- You want to avoid manual file creation
- You need to update integration files automatically

**Don't use scaffolding when**:
- You need custom architecture (use full generate mode)
- You're fixing existing code (use fix mode)
- You want fine-grained control (use manual generation)

## Scaffolding Script: add_connector.sh

**Location**: `.claude/skills/generate-connector-code/scripts/add_connector.sh`

### Features

1. **Auto-Flow Detection**
   - Scans `ConnectorServiceTrait` for all available flows
   - Automatically includes all detected flows
   - Future-proof: includes new flows automatically

2. **Template-Based Generation**
   - Uses proven templates from Grace ecosystem
   - Generates production-ready boilerplate
   - Maintains consistency across connectors

3. **Comprehensive File Updates**
   - Updates protobuf definitions
   - Updates domain types
   - Updates connectors module
   - Updates integration types
   - Updates config files

4. **Safety Features**
   - Creates automatic backups
   - Supports rollback on errors
   - Validates compilation
   - Checks for conflicts

5. **User-Friendly**
   - Clear progress indicators
   - Color-coded output
   - Implementation guidance
   - Next steps provided

## Usage Examples

### Example 1: List Available Flows

```bash
# Show all flows available for auto-detection
bash .claude/skills/generate-connector-code/scripts/add_connector.sh --list-flows
```

**Output**:
```
Auto-Detected Flows from ConnectorServiceTrait:
===============================================

PaymentAuthorizeV2          Process payment authorization
PaymentSyncV2               Synchronize status
PaymentVoidV2               Void/cancel operations
PaymentVoidPostCaptureV2    Void operations after capture
PaymentCapture              Capture authorized payments
RefundV2                    Process refunds
RefundSyncV2                Synchronize refund status
...
```

### Example 2: Scaffold New Connector

```bash
# Create connector with auto-confirmation
bash .claude/skills/generate-connector-code/scripts/add_connector.sh \
  stripe https://api.stripe.com \
  --force -y
```

**What it does**:
1. Validates environment and inputs
2. Auto-detects all flows
3. Creates backup of existing files
4. Generates connector boilerplate
5. Updates all integration files
6. Validates compilation
7. Provides next steps

**Files Created**:
- `backend/connector-integration/src/connectors/stripe.rs`
- `backend/connector-integration/src/connectors/stripe/transformers.rs`

**Files Updated**:
- `backend/grpc-api-types/proto/payment.proto`
- `backend/domain_types/src/connector_types.rs`
- `backend/connector-integration/src/connectors.rs`
- `backend/connector-integration/src/types.rs`
- `config/development.toml`
- `config/sandbox.toml`
- `config/production.toml`

### Example 3: Interactive Creation

```bash
# Create connector with user confirmation
bash .claude/skills/generate-connector-code/scripts/add_connector.sh \
  worldpay https://api.worldpay.com
```

**Output**:
```
🔧 STEP: Implementation Plan
=====================

📁 Files to create:
   ├── backend/connector-integration/src/connectors/worldpay.rs
   └── backend/connector-integration/src/connectors/worldpay/transformers.rs

📝 Files to modify:
   ├── backend/grpc-api-types/proto/payment.proto
   ├── backend/domain_types/src/connector_types.rs
   ├── backend/connector-integration/src/connectors.rs
   ├── backend/connector-integration/src/types.rs
   └── config/development.toml

🎯 Configuration:
   ├── Connector: Worldpay
   ├── Enum ordinal: 101
   ├── Base URL: https://api.worldpay.com
   └── Flows: [PaymentAuthorizeV2, PaymentSyncV2, ...]

❓ Proceed with implementation? [y/N]: y
```

## Integration with Skills

### Via generate-connector-code Skill

The scaffolding functionality is integrated into the `generate-connector-code` skill:

```bash
# Auto-activates scaffolding mode
"Scaffold a new connector called 'myconnector' for https://api.example.com"
```

**Skill Action**:
1. Detects scaffolding request
2. Runs add_connector.sh script
3. Validates output
4. Provides guidance

### Standalone Usage

You can also use the script directly:

```bash
cd /path/to/connector-service
bash .claude/skills/generate-connector-code/scripts/add_connector.sh \
  {connector_name} {base_url} \
  [options]
```

## Options

| Option | Description |
|--------|-------------|
| `--list-flows` | Display auto-detected flows and exit |
| `--force` | Ignore git status and force creation |
| `-y, --yes` | Skip confirmation prompts |
| `--debug` | Enable debug logging |
| `-h, --help` | Show help message |
| `-v, --version` | Show version information |

## Templates Used

The scaffolding script uses these templates:

### 1. connector.rs.template
**Purpose**: Main connector file template
**Generated**: `backend/connector-integration/src/connectors/{name}.rs`

**Contents**:
- Module declarations
- Connector struct with generic type
- All trait implementations (auto-detected flows)
- Import statements
- Type definitions

**Key Placeholders**:
- `{{CONNECTOR_NAME_PASCAL}}` → PascalCase connector name
- `{{CONNECTOR_NAME_SNAKE}}` → snake_case connector name
- `{{CONNECTOR_NAME_UPPER}}` → UPPER_CASE connector name
- `{{BASE_URL}}` → Base URL for API

### 2. transformers.rs.template
**Purpose**: Request/response transformers template
**Generated**: `backend/connector-integration/src/connectors/{name}/transformers.rs`

**Contents**:
- Request transformer structs
- Response transformer structs
- `From<&RouterDataV2<T>>` implementations
- `TryFrom<Response>` implementations
- Type conversions

### 3. test.rs.template
**Purpose**: Test scaffolding template
**Generated**: `backend/connector-integration/src/connectors/{name}/test.rs` (optional)

**Contents**:
- Integration test stubs
- Test cases for each flow
- Mock data structures

## Auto-Flow Detection

### How It Works

1. Scans `backend/interfaces/src/connector_types.rs`
2. Finds `ConnectorServiceTrait` definition
3. Extracts all trait names (e.g., `PaymentAuthorizeV2<T>`)
4. Generates implementations for all detected flows

**Benefits**:
- ✅ Future-proof: New flows added automatically
- ✅ Consistent: All flows follow same pattern
- ✅ No manual configuration needed
- ✅ Reduces errors from missing flows

### Detected Flows

Common flows detected:
- PaymentAuthorizeV2
- PaymentSyncV2
- PaymentVoidV2
- PaymentVoidPostCaptureV2
- PaymentCapture
- RefundV2
- RefundSyncV2
- PaymentPreAuthenticateV2
- PaymentAuthenticateV2
- PaymentPostAuthenticateV2
- CreateAccessToken
- CreateSessionToken
- SetupMandateV2
- UpdateMandateV2
- RevokeMandateV2
- PaymentMethodToken
- AcceptDisputeV2
- SubmitEvidenceV2

## File Updates

The scaffolding script automatically updates these files:

### 1. payment.proto
**What**: Adds connector to protobuf enum
**Example**: `STRIPE = 100;`
**Why**: gRPC communication needs connector identifier

### 2. connector_types.rs (domain_types)
**What**: Adds connector to ConnectorEnum
**Example**: `Stripe,`
**Why**: Domain layer needs connector type

### 3. connectors.rs (connector-integration)
**What**: Adds module declaration and use statement
**Example**:
```rust
pub mod stripe;
pub use self::stripe::Stripe;
```
**Why**: Module system needs explicit declarations

### 4. types.rs (domain_types)
**What**: Adds connector field to Connectors struct
**Example**: `pub stripe: ConnectorParams,`
**Why**: Configuration management needs connector params

### 5. types.rs (connector-integration)
**What**: Adds connector instantiation
**Example**:
```rust
ConnectorEnum::Stripe => Box::new(connectors::Stripe::new()),
```
**Why**: Runtime connector lookup needs instantiations

### 6. Config Files
**What**: Adds connector configuration section
**Example**:
```toml
[connectors]
stripe.base_url = "https://api.stripe.com"
```
**Why**: Runtime needs base URL and other config

## Safety Features

### Backup System

Before making changes, script creates backup:

```bash
Backup created at: .connector_backup_1640995200/
```

**Backed up files**:
- payment.proto
- connector_types.rs
- types.rs (domain_types)
- types.rs (connector-integration)
- connectors.rs
- development.toml
- sandbox.toml
- production.toml

### Rollback

On error, automatic rollback occurs:

```bash
# If compilation fails or error occurs
Performing emergency rollback
Emergency rollback completed
```

**Rollback actions**:
1. Removes generated connector files
2. Restores all backed up files
3. Cleans up backup directory

### Validation

After generation, script validates:

1. **Compilation**: `cargo check`
2. **Formatting**: `cargo fmt`
3. **Conflicts**: Checks for naming conflicts

## Next Steps After Scaffolding

After scaffolding completes, you receive guidance:

```
✅ SUCCESS: Connector 'stripe' successfully created!

🔧 Next Steps
============

1️⃣  Implement Core Logic:
   📁 Edit: backend/connector-integration/src/connectors/stripe/transformers.rs
      • Update request/response structures for your API
      • Implement proper field mappings
      • Handle authentication requirements

2️⃣  Customize Connector:
   📁 Edit: backend/connector-integration/src/connectors/stripe.rs
      • Update URL patterns and endpoints
      • Implement error handling
      • Add connector-specific logic

3️⃣  Validation Commands:
   📋 Check compilation: cargo check --package connector-integration
   📋 Run tests: cargo test --package connector-integration
   📋 Build: cargo build --package connector-integration
```

## Common Use Cases

### Use Case 1: Quick Start
**Scenario**: New connector needed, want to start coding immediately
**Command**: Scaffold with auto-confirmation
```bash
bash .claude/skills/generate-connector-code/scripts/add_connector.sh \
  paypal https://api.paypal.com \
  --force -y
```

### Use Case 2: Explore Flows
**Scenario**: Want to see what flows are available
**Command**: List flows only
```bash
bash .claude/skills/generate-connector-code/scripts/add_connector.sh \
  --list-flows
```

### Use Case 3: Interactive Setup
**Scenario**: Want to review changes before creating
**Command**: Interactive mode
```bash
bash .claude/skills/generate-connector-code/scripts/add_connector.sh \
  square https://connect.squareup.com
```

### Use Case 4: Debug Issues
**Scenario**: Scaffolding failed, want to see what went wrong
**Command**: Debug mode
```bash
bash .claude/skills/generate-connector-code/scripts/add_connector.sh \
  test https://api.test.com \
  --debug
```

## Best Practices

### 1. Use in Clean Git State
```bash
# Check git status before scaffolding
git status

# If dirty, commit or stash changes
git stash push -m "work in progress"
```

### 2. Review Changes
```bash
# After scaffolding, review what changed
git diff

# Check specific files
git diff payment.proto
git diff config/development.toml
```

### 3. Test Compilation
```bash
# Validate compilation after scaffolding
cargo check --package connector-integration

# Run tests
cargo test --package connector-integration
```

### 4. Iterate Quickly
```bash
# Scaffold
bash add_connector.sh myconnector https://api.test.com --force -y

# Implement transformers
# Edit backend/connector-integration/src/connectors/myconnector/transformers.rs

# Test
cargo check --package connector-integration
```

## Troubleshooting

### Issue: "Git working directory is not clean"
**Solution**: Commit changes or use `--force` flag
```bash
git add .
git commit -m "work in progress"

# Or
bash add_connector.sh myconnector https://api.test.com --force
```

### Issue: "Connector already exists"
**Solution**: Use different name or `--force` to override
```bash
# Use different name
bash add_connector.sh myconnector_v2 https://api.test.com

# Or force override (destructive)
bash add_connector.sh myconnector https://api.test.com --force
```

### Issue: "Compilation validation failed"
**Solution**: Automatic rollback occurs, check errors
```bash
# Review compilation errors
cargo check --package connector-integration 2>&1 | head -50

# Fix issues in generated code
# Re-run scaffolding if needed
```

### Issue: "Template substitution failed"
**Solution**: Check connector name format
```bash
# Use snake_case for connector name
bash add_connector.sh my_connector https://api.test.com

# Not: MyConnector, my-connector, or MY_CONNECTOR
```

## Advanced Usage

### Custom Template Modifications

You can customize templates before scaffolding:

```bash
# Copy templates to custom location
cp .claude/skills/generate-connector-code/scripts/connector.rs.template \
   ./my_custom_template.rs

# Modify template
vim ./my_custom_template.rs

# Use custom template
sed 's|connector.rs.template|my_custom_template.rs|g' \
  .claude/skills/generate-connector-code/scripts/add_connector.sh > \
  my_add_connector.sh

# Use custom script
bash my_add_connector.sh myconnector https://api.test.com
```

### Batch Scaffolding

Scaffold multiple connectors at once:

```bash
# Create array of connector configurations
connectors=(
  "stripe:https://api.stripe.com"
  "paypal:https://api.paypal.com"
  "square:https://connect.squareup.com"
)

# Loop through and scaffold each
for connector in "${connectors[@]}"; do
  IFS=':' read -r name url <<< "$connector"
  bash .claude/skills/generate-connector-code/scripts/add_connector.sh \
    "$name" "$url" --force -y
done
```

## Integration with Full Workflow

Scaffolding can be part of the full connector integration workflow:

```bash
# Step 1: Scaffold for quick start
"Scaffold a connector called 'newpay' for https://api.newpay.com"

# Step 2: Research and plan
"Research the NewPay API and create a spec"
"Plan implementation for NewPay"

# Step 3: Implement
"Generate connector code for NewPay based on spec and plan"

# Step 4: Review and fix
"Review the NewPay connector code"
"Fix the NewPay connector based on review feedback"

# Step 5: Test
"Run integration tests for NewPay"
```

**Or use full workflow without scaffolding**:
```bash
/connector-integrate newpay https://api.newpay.com/docs
```

## Comparison: Scaffolding vs Full Generation

| Feature | Scaffolding | Full Generation |
|---------|-------------|-----------------|
| Speed | ⚡ Very fast (seconds) | 🐌 Slower (minutes) |
| Customization | Basic (templates) | High (custom code) |
| Flows | All auto-detected | Custom (from spec) |
| Implementation | Manual after | Automated |
| Review needed | Yes | Yes |
| Testing | Manual | Automated |
| Use case | Quick start | Production-ready |

**Choose scaffolding when**:
- You need a starting point
- Want to iterate quickly
- Need all flows available
- Plan to customize heavily

**Choose full generation when**:
- Want production-ready code
- Need custom flows
- Want automated implementation
- Following full workflow

## Conclusion

Scaffolding provides a **powerful quick-start mechanism** for connector development. Combined with the full workflow, it gives you flexibility to:
- Start quickly with scaffolding
- Build fully with the complete workflow
- Use skills independently or orchestrated

**Best Practice**: Scaffold for exploration, use full workflow for production.