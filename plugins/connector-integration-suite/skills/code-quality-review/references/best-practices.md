# Best Practices Reference

**Version**: 1.0.0
**Purpose**: Project conventions, coding style, and organizational best practices

---

## Rust Naming Conventions

### Standard Naming

| Item | Convention | Example |
|------|------------|---------|
| Structs | `PascalCase` | `AuthorizeRequest` |
| Enums | `PascalCase` | `PaymentMethod` |
| Enum Variants | `PascalCase` | `CreditCard`, `BankTransfer` |
| Functions | `snake_case` | `build_request()` |
| Methods | `snake_case` | `process_payment()` |
| Variables | `snake_case` | `api_key`, `payment_id` |
| Constants | `SCREAMING_SNAKE_CASE` | `API_VERSION`, `MAX_RETRIES` |
| Type Parameters | Single uppercase | `T`, `E`, `R` |
| Lifetimes | Short lowercase | `'a`, `'b` |
| Modules | `snake_case` | `connector`, `transformers` |

### Project-Specific Naming

**Connectors**:
```rust
// Struct name = Connector name
pub struct Stripe<T> { ... }
pub struct PayPal<T> { ... }

// Module path matches connector name
// backend/connector-integration/src/connectors/stripe.rs
// backend/connector-integration/src/connectors/stripe/transformers.rs
```

**Flows**:
```rust
// Use domain flow types
use domain_types::router_flow_type::{Authorize, Capture, Void, Refund};

// Request/Response naming
pub struct AuthorizeRequest { ... }  // <Flow>Request
pub struct AuthorizeResponse { ... } // <Flow>Response
```

---

## Code Organization

### File Structure

**Connector Module**:
```
backend/connector-integration/src/connectors/
├── stripe.rs              # Main connector implementation
└── stripe/
    └── transformers.rs    # Request/response transformers
```

**Main File (stripe.rs)**:
```rust
// 1. Module declarations
mod transformers;

// 2. Imports (grouped)
// 2.1 Standard library
use std::marker::PhantomData;

// 2.2 External crates
use serde::{Deserialize, Serialize};

// 2.3 Domain types
use domain_types::router_data_v2::RouterDataV2;
use domain_types::router_flow_type::Authorize;

// 2.4 Interfaces
use interfaces::connector_integration_v2::ConnectorIntegrationV2;

// 3. Type definitions
pub struct Stripe<T> {
    _phantom: PhantomData<T>,
}

// 4. Macro invocations
macros::create_all_prerequisites!(...);
macros::macro_connector_implementation!(...);

// 5. Custom trait implementations (if needed)
```

**Transformers File (transformers.rs)**:
```rust
// 1. Imports
use domain_types::router_data_v2::RouterDataV2;
use serde::{Deserialize, Serialize};

// 2. Request types
#[derive(Serialize)]
pub struct AuthorizeRequest { ... }

// 3. Response types
#[derive(Deserialize)]
pub struct AuthorizeResponse { ... }

// 4. Request transformers (TryFrom RouterDataV2)
impl TryFrom<&RouterDataV2<...>> for AuthorizeRequest { ... }

// 5. Response transformers (TryFrom API Response)
impl<F> TryFrom<ResponseRouterData<F, AuthorizeResponse, ...>>
    for RouterDataV2<F, ..., ...> { ... }
```

---

### Import Organization

**Good** (✅):
```rust
// Grouped and sorted
use std::collections::HashMap;
use std::marker::PhantomData;

use serde::{Deserialize, Serialize};
use serde_json::Value;

use domain_types::router_data_v2::RouterDataV2;
use domain_types::router_flow_type::Authorize;
use domain_types::MinorUnit;

use interfaces::connector_integration_v2::ConnectorIntegrationV2;
```

**Bad** (❌):
```rust
// Scattered and unsorted
use serde::{Deserialize, Serialize};
use domain_types::router_data_v2::RouterDataV2;
use std::marker::PhantomData;
use interfaces::connector_integration_v2::ConnectorIntegrationV2;
use domain_types::MinorUnit;
```

---

## Documentation Standards

### Module-Level Documentation

```rust
//! Stripe connector implementation
//!
//! Supports payment flows: Authorize, Capture, Void, Refund
//!
//! # Authentication
//! Uses API Key authentication via header
//!
//! # API Version
//! 2023-10-16
//!
//! # Reference
//! <https://stripe.com/docs/api>
```

### Struct Documentation

```rust
/// Stripe connector for payment processing
///
/// This connector implements the following flows:
/// - Authorize: Create a payment authorization
/// - Capture: Capture a previously authorized payment
/// - Void: Cancel an authorization
/// - Refund: Refund a captured payment
///
/// # Type Parameter
/// * `T` - Flow type marker (Authorize, Capture, etc.)
pub struct Stripe<T> {
    _phantom: PhantomData<T>,
}
```

### Function Documentation

```rust
/// Build an authorization request from router data
///
/// # Arguments
/// * `router_data` - Payment data from the router
///
/// # Returns
/// * `Ok(AuthorizeRequest)` - Successfully built request
/// * `Err(Error)` - Missing required fields or invalid data
///
/// # Errors
/// Returns error if:
/// - Amount is zero or negative
/// - Currency is not supported
/// - Required card data is missing
fn build_authorize_request(router_data: &RouterDataV2<...>)
    -> Result<AuthorizeRequest, Error> {
    // Implementation
}
```

### Field Documentation

```rust
pub struct AuthorizeRequest {
    /// Payment amount in minor units (e.g., cents for USD)
    pub amount: MinorUnit,

    /// ISO 4217 currency code (e.g., "USD", "EUR")
    pub currency: Currency,

    /// Reference ID for tracking this payment
    /// Must be unique per payment attempt
    pub reference_id: String,
}
```

---

## Error Handling Patterns

### Use Result Types

**Good** (✅):
```rust
fn process_payment(data: PaymentData) -> Result<Payment, Error> {
    let validated = validate(data)?;
    let charged = charge(validated)?;
    let recorded = record(charged)?;
    Ok(recorded)
}
```

**Bad** (❌):
```rust
fn process_payment(data: PaymentData) -> Payment {
    let validated = validate(data).unwrap();  // WRONG
    let charged = charge(validated).expect("charge failed");  // WRONG
    record(charged).unwrap()  // WRONG
}
```

### Custom Error Types

```rust
#[derive(Debug, thiserror::Error)]
pub enum ConnectorError {
    #[error("Missing required field: {field}")]
    MissingField { field: String },

    #[error("Invalid amount: {0}")]
    InvalidAmount(String),

    #[error("Authentication failed")]
    AuthenticationFailed,

    #[error("Network error: {0}")]
    NetworkError(#[from] reqwest::Error),
}
```

### Error Context

```rust
use error_stack::{Report, ResultExt};

fn fetch_data() -> Result<Data, Report<Error>> {
    http_client
        .get(url)
        .send()
        .change_context(Error::NetworkError)
        .attach_printable(format!("Failed to fetch from {}", url))?;

    // More context
}
```

---

## Testing Best Practices

### Test Organization

```rust
#[cfg(test)]
mod tests {
    use super::*;

    // Helper functions at top
    fn build_test_router_data() -> RouterDataV2<...> {
        // Build test data
    }

    // Group tests by functionality
    mod authorize_tests {
        use super::*;

        #[test]
        fn test_successful_authorization() { ... }

        #[test]
        fn test_authorization_with_missing_data() { ... }
    }

    mod capture_tests {
        use super::*;

        #[test]
        fn test_successful_capture() { ... }
    }
}
```

### Test Naming

```rust
// Pattern: test_<functionality>_<scenario>
#[test]
fn test_authorize_successful() { ... }

#[test]
fn test_authorize_invalid_card() { ... }

#[test]
fn test_capture_already_captured() { ... }

#[test]
fn test_refund_partial_amount() { ... }
```

### Test Structure (AAA Pattern)

```rust
#[test]
fn test_authorize_request_building() {
    // Arrange
    let router_data = build_test_router_data();
    let expected_amount = MinorUnit::new(1000);

    // Act
    let request = AuthorizeRequest::try_from(&router_data)
        .expect("Failed to build request");

    // Assert
    assert_eq!(request.amount, expected_amount);
    assert_eq!(request.currency, Currency::USD);
    assert!(!request.reference_id.is_empty());
}
```

---

## Macro Usage Patterns

### Prerequisites Macro

```rust
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
```

**Rules**:
- Always declare ALL supported flows
- Match `resource_common_data` to flow type
- Declare amount converter if non-standard
- Place after struct definition, before implementations

### Implementation Macro

```rust
macros::macro_connector_implementation!(
    connector: Stripe,
    flow_name: Authorize,
    resource_common_data: PaymentFlowData,
    resource_specific_data: PaymentAuthorizeData,
    connector_request: AuthorizeRequest,
    connector_response: AuthorizeResponse,
    headers: [("X-API-Version", "2023-10-16")],
    authentication: auth_type,
);
```

**Rules**:
- One macro call per flow
- Match all type parameters exactly
- Include headers if needed
- Specify authentication method

---

## Type Usage Patterns

### Use Strong Types

**Good** (✅):
```rust
use domain_types::MinorUnit;
use domain_types::Currency;
use domain_types::ConnectorTransactionId;

pub struct Payment {
    pub amount: MinorUnit,        // NOT i64
    pub currency: Currency,        // NOT String
    pub transaction_id: ConnectorTransactionId,  // NOT String
}
```

**Bad** (❌):
```rust
pub struct Payment {
    pub amount: i64,      // WEAK - what unit?
    pub currency: String, // WEAK - any string valid?
    pub transaction_id: String,  // WEAK - no type safety
}
```

### Enums Over Strings

**Good** (✅):
```rust
#[derive(Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PaymentMethod {
    CreditCard,
    DebitCard,
    BankTransfer,
    Wallet,
}

pub struct Request {
    pub payment_method: PaymentMethod,
}
```

**Bad** (❌):
```rust
pub struct Request {
    pub payment_method: String,  // Any string accepted!
}
```

---

## Performance Best Practices

### Avoid Unnecessary Cloning

**Good** (✅):
```rust
// Use references when possible
fn process(data: &PaymentData) -> Result<Response, Error> {
    let amount = data.amount;  // Copy small types
    let reference = &data.reference_id;  // Borrow strings
    // ...
}
```

**Bad** (❌):
```rust
fn process(data: PaymentData) -> Result<Response, Error> {
    // Takes ownership unnecessarily
    // ...
}
```

### Use Appropriate Collection Types

```rust
// HashMap for key-value lookups (O(1))
use std::collections::HashMap;
let mut map: HashMap<String, Value> = HashMap::new();

// Vec for ordered lists
let items: Vec<Item> = vec![...];

// BTreeMap for sorted keys
use std::collections::BTreeMap;
let sorted: BTreeMap<String, Value> = BTreeMap::new();
```

---

## Code Clarity

### Prefer Explicit Over Implicit

**Good** (✅):
```rust
// Explicit type for clarity
let amount: MinorUnit = router_data.request.amount;

// Explicit error conversion
.map_err(|e| Error::NetworkError(e.to_string()))?
```

**Acceptable** (when obvious):
```rust
// Obvious from context
let amount = router_data.request.amount;
```

### Avoid Deep Nesting

**Good** (✅):
```rust
fn process(data: PaymentData) -> Result<Response, Error> {
    // Early returns reduce nesting
    if !data.is_valid() {
        return Err(Error::InvalidData);
    }

    let amount = data.amount;
    if amount.is_zero() {
        return Err(Error::ZeroAmount);
    }

    // Main logic at low nesting level
    charge(amount)
}
```

**Bad** (❌):
```rust
fn process(data: PaymentData) -> Result<Response, Error> {
    if data.is_valid() {
        let amount = data.amount;
        if !amount.is_zero() {
            // Deep nesting makes it hard to follow
            charge(amount)
        } else {
            Err(Error::ZeroAmount)
        }
    } else {
        Err(Error::InvalidData)
    }
}
```

---

## Serde Patterns

### Rename Fields

```rust
#[derive(Serialize, Deserialize)]
pub struct ApiRequest {
    #[serde(rename = "paymentAmount")]
    pub payment_amount: MinorUnit,

    #[serde(rename = "currencyCode")]
    pub currency_code: Currency,
}
```

### Handle Optional Fields

```rust
#[derive(Serialize, Deserialize)]
pub struct Request {
    pub required_field: String,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub optional_field: Option<String>,
}
```

### Default Values

```rust
#[derive(Deserialize)]
pub struct Config {
    #[serde(default = "default_timeout")]
    pub timeout: u64,
}

fn default_timeout() -> u64 {
    30
}
```

---

## Common Pitfalls to Avoid

### 1. Mutating Reference IDs

```rust
// WRONG
let mut ref_id = router_data.connector_request_reference_id.clone();
ref_id.push_str("-retry");  // DON'T MUTATE

// RIGHT
let ref_id = router_data.connector_request_reference_id.clone();
```

### 2. Using Primitive Types for Money

```rust
// WRONG
let amount: i64 = 1000;

// RIGHT
let amount: MinorUnit = MinorUnit::new(1000);
```

### 3. Ignoring Errors

```rust
// WRONG
let data = fetch_data().ok();  // Silently ignores error

// RIGHT
let data = fetch_data()?;  // Propagates error
```

### 4. Overly Generic Error Messages

```rust
// WRONG
return Err("Error".to_string());

// RIGHT
return Err(Error::MissingRequiredField {
    field: "card_number".to_string()
});
```

---

## Code Review Checklist

Before submitting PR:

**Code Quality**:
- [ ] Follows naming conventions
- [ ] Properly organized imports
- [ ] No unwrap/expect
- [ ] Proper error handling
- [ ] No hardcoded values
- [ ] No unsafe blocks

**Documentation**:
- [ ] Public items have doc comments
- [ ] Complex logic is explained
- [ ] Examples provided where helpful

**Testing**:
- [ ] Tests for happy path
- [ ] Tests for error cases
- [ ] Tests for edge cases

**Performance**:
- [ ] No unnecessary allocations
- [ ] Appropriate data structures
- [ ] No obvious inefficiencies

**Security**:
- [ ] Input validation
- [ ] No credential leaks
- [ ] Proper error messages (no info leakage)

---

## Version History

- **1.0.0** (2025-12-09): Initial best practices
  - Naming conventions
  - Code organization
  - Documentation standards
  - Error handling patterns
  - Testing best practices
  - Macro usage
  - Common pitfalls
