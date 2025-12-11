# UCS Architecture Rules - Implementation Reference

## Core Architecture Requirements

### Critical Types (MUST Use)

#### ✅ CORRECT Types
```rust
// Use these types - NEVER the legacy alternatives
use domain_types::router_data_v2::RouterDataV2;
use interfaces::connector_integration_v2::ConnectorIntegrationV2;
use api_models::enums::AttemptStatus;

// Amount types
use types::{MinorUnit, MajorUnit};

// Connector auth
use types::{ConnectorAuthType, ConnectorCustomerData};

// Security
use common_utils::pii::Secret;
```

#### ❌ WRONG Types (NEVER Use)
```rust
// ❌ Legacy types - DO NOT USE
use hyperswitch_domain_models::RouterData;
use interfaces::ConnectorIntegration;

// ❌ Primitive types for amounts
let amount: i64 = 1000;
let amount: f64 = 10.50;
```

### Generic Connector Struct Pattern

```rust
// ✅ CORRECT - With generic type
struct Stripe<T> { }

// ❌ WRONG - Without generic type
struct Stripe { }
```

The generic `<T>` is required for trait bounds:
- `T: crate::utils:: jwt::JwtSigner`
- `T: crate::utils:: hypervisor_http_client::Hypervisor`

### Import Organization

```rust
// Standard imports (domain types first)
use domain_types::router_data_v2::RouterDataV2;
use interfaces::connector_integration_v2::ConnectorIntegrationV2;

// UCS API types
use api_models::enums::AttemptStatus;
use types::{MinorUnit, MajorUnit};

// External types
use serde::{Deserialize, Serialize};
use error_stack::{ResultExt, IntoReport};

// Local imports
use crate::connectors::{connector_name}::transformers::{ConnectorName, PaymentFlowData};
use super::types;

// Error type
use crate::core::errors::{ConnectorErrorExt, UtilsWorkflowExt};
```

## Critical Implementation Patterns

### 1. Reference ID Handling

#### ✅ CORRECT - Extract from Response
```rust
// Extract reference ID from connector response
let payment_id = response.id.clone();
let router_data = RouterDataV2 {
    payment_id: Some(payment_id.clone()),
    ..router_data
};
```

#### ❌ WRONG - Hardcode or Mutate
```rust
// ❌ WRONG - Hardcoding
let payment_id = "hardcoded_id_123";

// ❌ WRONG - Mutating reference ID
let mut router_data = router_data;
router_data.payment_id = Some("mutated_id");
```

### 2. Amount Handling

#### ✅ CORRECT - Use MinorUnit
```rust
// Extract amount using converter
let amount = MinorUnit::new(router_data.amount, router_data.currency)
    .into_report()
    .change_context(ConnectorError::RequestEncodingFailed)?;

// Use in request
let request = PaymentRequest {
    amount: amount.to_string(),
    currency: router_data.currency.to_string(),
};
```

#### ❌ WRONG - Use Primitives
```rust
// ❌ WRONG - Using i64
let amount: i64 = router_data.amount;

// ❌ WRONG - Using f64
let amount: f64 = router_data.amount / 100.0;
```

### 3. Status Mapping

#### ✅ CORRECT - Proper Mapping
```rust
fn map_status(connector_status: &str) -> AttemptStatus {
    match connector_status {
        "succeeded" | "success" | "completed" => AttemptStatus::Charged,
        "pending" | "processing" | "authorized" => AttemptStatus::Pending,
        "failed" | "declined" | "rejected" => AttemptStatus::Failed,
        "canceled" | "cancelled" | "voided" => AttemptStatus::Failed,
        // Unknown statuses map to Pending, NOT Failed
        _ => AttemptStatus::Pending,
    }
}
```

#### ❌ WRONG - Incorrect Mapping
```rust
// ❌ WRONG - Unknown maps to Failed
_ => AttemptStatus::Failed,

// ❌ WRONG - All failures are Failed (no differentiation)
"failed" | "canceled" => AttemptStatus::Failed,
```

### 4. Error Handling

#### ✅ CORRECT - Use ? Operator
```rust
fn authorize(
    &self,
    request: &RouterDataV2<T>,
) -> Result<Self::AuthorizeRouterData, ConnectorError> {
    let connector_request = PaymentFlowData::from(request)?;
    let response = self
        .api_client
        .post(&self.base_url)
        .json(&connector_request)
        .send()
        .await
        .change_context(ConnectorError::RequestEncodingFailed)?;

    Ok(response)
}
```

#### ❌ WRONG - Unwrap or Manual Matching
```rust
// ❌ WRONG - Using unwrap
let response = self.api_client.post().unwrap();

// ❌ WRONG - Manual error propagation
let response = match self.api_client.post().await {
    Ok(r) => r,
    Err(e) => return Err(e.into()),
};
```

### 5. Security

#### ✅ CORRECT - Use Secret<T>
```rust
struct StripeConfig {
    pub api_key: Secret<String>,
    pub merchant_id: Secret<String>,
}

// Access safely
let api_key = &self.config.api_key;
```

#### ❌ WRONG - Unsafe Code
```rust
// ❌ WRONG - unsafe blocks
unsafe { /* any unsafe code */ }

// ❌ WRONG - Exposing secrets
pub api_key: String,
```

## Macro Framework Usage

### create_all_prerequisites!

```rust
// Foundation macro - defines connector structure
macros::create_all_prerequisites!(
    connector_name: Stripe,  // Note: Capitalized struct name
    api: [
        // List all supported flows
        (flow: Authorize, request_type: PaymentFlowData, response_type: PaymentResponseData),
        (flow: Capture, request_type: CaptureFlowData, response_type: CaptureResponseData),
        (flow: Refund, request_type: RefundFlowData, response_type: RefundResponseData),
        (flow: Void, request_type: VoidFlowData, response_type: VoidResponseData),
        (flow: PSync, request_type: SyncFlowData, response_type: SyncResponseData),
    ],
    amount_converters: [
        amount_converter: StringMinorUnit,  // From implementation plan
    ],
);
```

### macro_connector_implementation!

```rust
// Flow implementation macro - implements specific flow
macros::macro_connector_implementation!(
    connector: Stripe,
    flow_name: Authorize,
    resource_common_data: PaymentFlowData,
    request_transformer: PaymentFlowData::from,
    response_transformer: PaymentResponseData::try_from,
);
```

### Available Flows

Supported flow types (use exact names):
- `Authorize`
- `Capture`
- `Refund`
- `Void`
- `PSync`
- `RSync`
- `PreAuthenticate`
- `Authenticate`
- `PostAuthenticate`
- `CreateAccessToken`
- `CreateSessionToken`

## File Structure

### Main Connector File
```
backend/connector-integration/src/connectors/stripe.rs
```

Contains:
- Config struct
- Connector struct with generic `<T>`
- `ConnectorIntegrationV2` trait implementation
- HTTP client setup

### Transformers File
```
backend/connector-integration/src/connectors/stripe/transformers.rs
```

Contains:
- Request transformer structs (one per flow)
- Response transformer structs
- `From<&RouterDataV2<T>>` implementations
- `TryFrom<ConnectorResponse>` implementations

### Module Declaration

Update `backend/connector-integration/src/connectors.rs`:
```rust
pub mod stripe;

#[cfg(feature = "connector_stripe")]
pub use stripe::Stripe;
```

### Development Config

Update `config/development.toml`:
```toml
[stripe]
base_url = "https://api.stripe.com"
```

## Common Implementation Mistakes

### Mistake 1: Wrong Type Imports
```rust
// ❌ WRONG
use hyperswitch_domain_models::RouterData;
use interfaces::ConnectorIntegration;

// ✅ CORRECT
use domain_types::router_data_v2::RouterDataV2;
use interfaces::connector_integration_v2::ConnectorIntegrationV2;
```

### Mistake 2: Missing Generic Type
```rust
// ❌ WRONG
struct Stripe { }

// ✅ CORRECT
struct Stripe<T> { }
```

### Mistake 3: Primitive Amount Types
```rust
// ❌ WRONG
fn get_amount(&self, data: &RouterDataV2<T>) -> i64 {
    data.amount
}

// ✅ CORRECT
fn get_amount(&self, data: &RouterDataV2<T>) -> MinorUnit {
    MinorUnit::new(data.amount, data.currency)
        .into_report()
        .change_context(ConnectorError::RequestEncodingFailed)
        .attach_printable("Failed to convert amount")
}
```

### Mistake 4: Incorrect Status Mapping
```rust
// ❌ WRONG
fn map_status(s: &str) -> AttemptStatus {
    match s {
        "succeeded" => AttemptStatus::Charged,
        "failed" => AttemptStatus::Failed,
        _ => AttemptStatus::Failed,  // Unknown -> Failed (wrong!)
    }
}

// ✅ CORRECT
fn map_status(s: &str) -> AttemptStatus {
    match s {
        "succeeded" | "success" => AttemptStatus::Charged,
        "pending" | "processing" => AttemptStatus::Pending,
        "failed" | "declined" => AttemptStatus::Failed,
        _ => AttemptStatus::Pending,  // Unknown -> Pending (correct!)
    }
}
```

### Mistake 5: No Error Propagation
```rust
// ❌ WRONG
fn authorize(&self, data: &RouterDataV2<T>) -> Result<AuthorizeResponse, ConnectorError> {
    let response = self.client.post().send().unwrap();  // unwrap!
    Ok(response)
}

// ✅ CORRECT
fn authorize(&self, data: &RouterDataV2<T>) -> Result<AuthorizeResponse, ConnectorError> {
    let response = self.client
        .post()
        .send()
        .await
        .change_context(ConnectorError::RequestEncodingFailed)?;
    Ok(response)
}
```

## Build Validation Checklist

Before marking as complete, verify:
- [ ] `cargo build` compiles without errors
- [ ] `cargo clippy` shows no warnings
- [ ] All types are from `domain_types` and `interfaces`
- [ ] No unwrap() calls
- [ ] No unsafe blocks
- [ ] Generic type `<T>` present on connector struct
- [ ] Amount converter declared in `create_all_prerequisites!`
- [ ] Status mapping handles unknown statuses correctly
- [ ] Reference IDs extracted from responses
- [ ] Module declarations updated in connectors.rs

## Pattern Templates

See flow-specific templates in:
- `.claude/skills/generate-connector-code/references/flow-templates/authorize.md`
- `.claude/skills/generate-connector-code/references/flow-templates/capture.md`
- `.claude/skills/generate-connector-code/references/flow-templates/refund.md`
- etc.