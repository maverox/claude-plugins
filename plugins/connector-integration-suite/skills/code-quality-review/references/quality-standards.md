# Quality Standards Reference

**Version**: 1.0.0
**Purpose**: Project-specific code quality standards and validation rules

---

## Connector Integration Standards

### Critical Requirements (Auto-Fail if Violated)

#### 1. Type System Compliance

**Correct Types** (✅):
```rust
use domain_types::router_data_v2::RouterDataV2;
use interfaces::connector_integration_v2::ConnectorIntegrationV2;
use domain_types::router_flow_type::{Authorize, Capture, Void, Refund};
```

**Incorrect Types** (❌):
```rust
use hyperswitch_domain_models::RouterData;  // WRONG
use interfaces::ConnectorIntegration;  // WRONG
```

**Validation**:
- Grep for `use.*RouterData[^V]` → ERROR
- Grep for `use.*ConnectorIntegration[^V]` → ERROR
- Require `RouterDataV2` and `ConnectorIntegrationV2`

---

#### 2. Amount Handling

**Correct** (✅):
```rust
use domain_types::MinorUnit;

// In request struct
pub struct AuthorizeRequest {
    pub amount: MinorUnit,
    pub currency: Currency,
}

// In transformer
amount: router_data.request.amount,  // MinorUnit type
```

**Incorrect** (❌):
```rust
pub struct AuthorizeRequest {
    pub amount: i64,  // WRONG
    // or
    pub amount: f64,  // WRONG
    // or
    pub amount: String,  // WRONG (unless StringMinorUnit converter)
}
```

**Validation**:
- Check all amount fields use `MinorUnit`
- Verify amount converter in `create_all_prerequisites!`
- No primitive types (`i64`, `f64`) for money amounts
- Exception: `StringMinorUnit` converter for string-based APIs

---

#### 3. Reference ID Handling

**Correct** (✅):
```rust
// Extract from router_data
reference_id: router_data.connector_request_reference_id.clone()

// Or use directly
router_data.connector_request_reference_id
```

**Incorrect** (❌):
```rust
// Hardcoded
reference_id: "TEST123".to_string()  // WRONG

// Generated
reference_id: uuid::Uuid::new_v4().to_string()  // WRONG

// Mutated
let mut ref_id = router_data.connector_request_reference_id.clone();
ref_id.push_str("-suffix");  // WRONG
```

**Validation**:
- Grep for hardcoded reference IDs (literals)
- Check for ID generation (`uuid`, `random`)
- Ensure no mutation of reference IDs

---

#### 4. Error Handling

**Correct** (✅):
```rust
fn process() -> Result<Response, Error> {
    let data = fetch_data()?;  // Propagate with ?
    let result = transform(data)?;
    Ok(result)
}
```

**Incorrect** (❌):
```rust
// Using unwrap
let data = fetch_data().unwrap();  // WRONG

// Using expect
let data = fetch_data().expect("Failed");  // WRONG

// Ignoring errors
let data = fetch_data().ok();  // WRONG (unless intentional)
```

**Validation**:
- Grep for `.unwrap()` → ERROR
- Grep for `.expect(` → ERROR
- Check proper `Result` types
- Verify `?` operator usage

---

#### 5. No Unsafe Code

**Correct** (✅):
```rust
// Safe Rust only
fn process(data: &[u8]) -> Result<String, Error> {
    String::from_utf8(data.to_vec())
        .map_err(|e| Error::EncodingError(e))
}
```

**Incorrect** (❌):
```rust
unsafe {
    // ANY unsafe block is wrong
}
```

**Validation**:
- Grep for `unsafe` keyword → ERROR
- No exceptions

---

#### 6. Authentication Handling

**Correct** (✅):
```rust
// Extract from auth_type
let auth = AuthType::try_from(&router_data.connector_auth_type)?;

// Or with pattern matching
let api_key = match &router_data.connector_auth_type {
    ConnectorAuthType::HeaderKey { api_key } => api_key,
    _ => Err(errors::ConnectorError::InvalidAuthType)?
};
```

**Incorrect** (❌):
```rust
// Hardcoded credentials
let api_key = "sk_test_123456";  // WRONG

// From environment
let api_key = std::env::var("API_KEY").unwrap();  // WRONG
```

**Validation**:
- Check auth extraction from `connector_auth_type`
- No hardcoded credentials
- No environment variables in connector code

---

### Warning-Level Requirements

#### 1. Status Mapping

**Correct** (✅):
```rust
use domain_types::router_enums::AttemptStatus;

status: match api_status {
    "success" => AttemptStatus::Charged,
    "pending" => AttemptStatus::Pending,
    "failed" => AttemptStatus::Failure,
    "unknown" => AttemptStatus::Pending,  // Unknown → Pending
    _ => AttemptStatus::Pending,
}
```

**Incorrect** (❌):
```rust
status: match api_status {
    "unknown" => AttemptStatus::Failure,  // WRONG - should be Pending
    _ => AttemptStatus::Failure,  // Too aggressive
}
```

**Refund Status Mapping**:
```rust
// When amount_captured exists
status: if refund_amount == amount_captured {
    RefundStatus::Success
} else {
    RefundStatus::Pending  // Partial refund
}
```

---

#### 2. Enum Usage

**Correct** (✅):
```rust
#[derive(Serialize, Deserialize)]
pub enum PaymentMethod {
    Card,
    BankTransfer,
    Wallet,
}

// Use in struct
pub struct Request {
    pub payment_method: PaymentMethod,
}
```

**Incorrect** (❌):
```rust
pub struct Request {
    pub payment_method: String,  // WRONG - should be enum
}

// Especially for limited value sets
pub payment_type: String  // Only 3-4 values? Use enum!
```

**Validation**:
- Check for String fields with limited values
- Recommend enum conversion

---

#### 3. Required Field Validation

**Validation Layers**:

1. **API Layer**: Validate request structure
2. **Domain Layer**: Validate business rules
3. **Connector Layer**: Only transform, don't validate

**Correct** (✅):
```rust
// In API handler
fn validate_payment_request(req: &PaymentRequest) -> Result<(), ValidationError> {
    if req.amount.is_zero() {
        return Err(ValidationError::InvalidAmount);
    }
    Ok(())
}

// In connector transformer
impl TryFrom<&RouterDataV2<...>> for Request {
    fn try_from(router_data: &RouterDataV2<...>) -> Result<Self, Error> {
        // Just transform, assume data is valid
        Ok(Self {
            amount: router_data.request.amount,
            ...
        })
    }
}
```

**Incorrect** (❌):
```rust
// In connector transformer
impl TryFrom<&RouterDataV2<...>> for Request {
    fn try_from(router_data: &RouterDataV2<...>) -> Result<Self, Error> {
        // Validating in transformer - WRONG layer
        if router_data.request.amount.is_zero() {
            return Err(errors::ConnectorError::MissingRequiredField);
        }
        ...
    }
}
```

---

#### 4. Macro Usage

**Correct Macro Pattern**:

```rust
// Step 1: Prerequisites
macros::create_all_prerequisites!(
    connector_name: Stripe,
    api: [
        (flow: Authorize, resource_common_data: PaymentFlowData),
        (flow: Capture, resource_common_data: PaymentFlowData),
        (flow: Void, resource_common_data: PaymentFlowData),
        (flow: Refund, resource_common_data: RefundFlowData),
    ],
    amount_converters: [amount_converter: StringMinorUnit],
);

// Step 2: Implementation
macros::macro_connector_implementation!(
    connector: Stripe,
    flow_name: Authorize,
    resource_common_data: PaymentFlowData,
    resource_specific_data: PaymentAuthorizeData,
    connector_request: AuthorizeRequest,
    connector_response: AuthorizeResponse,
    // ... other config
);
```

**Common Mistakes**:
- Missing `create_all_prerequisites!`
- Wrong flow type in implementation
- Mismatched `resource_common_data`
- Missing amount converter declaration

---

### Suggestion-Level Improvements

#### 1. Documentation

**Good Documentation** (✅):
```rust
/// Stripe connector implementation for payment processing
///
/// Supports: Authorize, Capture, Void, Refund flows
///
/// Authentication: API Key (Header)
/// API Version: 2023-10-16
pub struct Stripe<T> {
    _phantom: PhantomData<T>,
}

/// Request structure for payment authorization
///
/// # Fields
/// * `amount` - Payment amount in minor units (cents)
/// * `currency` - ISO 4217 currency code
pub struct AuthorizeRequest {
    pub amount: MinorUnit,
    pub currency: Currency,
}
```

**Missing Documentation** (❌):
```rust
pub struct Stripe<T> {  // No doc comment
    _phantom: PhantomData<T>,
}

pub struct AuthorizeRequest {  // No doc comment
    pub amount: MinorUnit,
    pub currency: Currency,
}
```

---

#### 2. Code Organization

**Good Organization** (✅):
```rust
// connector.rs
// 1. Imports
use domain_types::...;
use interfaces::...;

// 2. Type definitions
pub struct Connector<T> { ... }

// 3. Macro invocations
macros::create_all_prerequisites!(...);

// 4. Trait implementations (if custom)

// transformers.rs
// 1. Request transformers
impl TryFrom<&RouterDataV2<...>> for Request { ... }

// 2. Response transformers
impl TryFrom<Response> for Result<...> { ... }
```

**Poor Organization** (❌):
```rust
// Mixed imports
use std::...;
impl Something { ... }
use domain_types::...;  // Imports scattered

// Transformers in main file (should be separate)
```

---

#### 3. Naming Conventions

**Correct Naming**:
- Structs: `PascalCase` (e.g., `AuthorizeRequest`)
- Functions: `snake_case` (e.g., `build_request`)
- Constants: `SCREAMING_SNAKE_CASE` (e.g., `API_VERSION`)
- Enums: `PascalCase` (e.g., `PaymentMethod`)
- Enum variants: `PascalCase` (e.g., `CreditCard`)

**Validation**:
- Check Rust naming conventions
- Use `cargo clippy` for automatic checks

---

## Core Domain Standards

### Type Safety

**Correct** (✅):
```rust
// Strong typing
pub struct PaymentId(String);
pub struct ConnectorId(String);

// No confusion possible
fn process(payment_id: PaymentId, connector_id: ConnectorId) { ... }
```

**Incorrect** (❌):
```rust
// Weak typing
fn process(payment_id: String, connector_id: String) { ... }
// Can accidentally swap arguments!
```

### Serialization

**Correct** (✅):
```rust
#[derive(Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Status {
    Pending,
    Success,
    #[serde(rename = "FAILED")]  // Custom rename if needed
    Failure,
}
```

---

## Testing Requirements

### Minimum Test Coverage

**Required Tests**:
1. **Happy Path**: Each flow with successful response
2. **Error Cases**: At least one failure scenario per flow
3. **Edge Cases**: Zero amounts, unknown statuses, etc.

**Test Structure**:
```rust
#[test]
fn test_authorize_success() {
    // Setup
    let router_data = build_router_data();

    // Execute
    let request = AuthorizeRequest::try_from(&router_data).unwrap();

    // Verify
    assert_eq!(request.amount, router_data.request.amount);
}
```

---

## Quality Scoring Matrix

| Issue Type | Score Impact | Examples |
|------------|--------------|----------|
| Wrong RouterData type | -20 | Using `RouterData` instead of `RouterDataV2` |
| Wrong amount type | -20 | Using `i64` instead of `MinorUnit` |
| Hardcoded reference ID | -20 | `reference_id: "TEST123"` |
| Unsafe code | -20 | `unsafe { ... }` |
| unwrap/expect | -20 | `.unwrap()` calls |
| Wrong status mapping | -5 | Unknown → Failure (should be Pending) |
| String for enum | -5 | Limited values as String |
| Missing validation | -5 | Validation in wrong layer |
| Missing docs | -1 | No doc comments on public items |
| Naming issues | -1 | Non-standard naming |

---

## Automated Checks

### Clippy Rules (Enforced)

```toml
[lints.clippy]
unwrap_used = "deny"
expect_used = "deny"
panic = "deny"
missing_docs_in_public_items = "warn"
```

### Custom Checks

```bash
# Check for RouterData (should be RouterDataV2)
grep -n "use.*RouterData[^V]" backend/connector-integration/src/connectors/*.rs

# Check for unwrap
grep -n "\.unwrap()" backend/connector-integration/src/connectors/*.rs

# Check for hardcoded IDs (simple heuristic)
grep -n '"[A-Z0-9]\{10,\}"' backend/connector-integration/src/connectors/*.rs
```

---

## Version History

- **1.0.0** (2025-12-09): Initial standards
  - UCS architecture requirements
  - Amount handling rules
  - Reference ID handling
  - Error handling patterns
  - Status mapping guidelines
