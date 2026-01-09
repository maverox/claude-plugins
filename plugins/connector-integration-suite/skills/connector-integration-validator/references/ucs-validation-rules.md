# UCS Validation Rules Reference

**Version**: 1.0.0
**Purpose**: UCS (Universal Connector Service) architecture validation rules and requirements

---

## Type System Requirements

### Router Data Types

**MUST USE** (✅):
```rust
use domain_types::router_data_v2::RouterDataV2;
use interfaces::connector_integration_v2::ConnectorIntegrationV2;
```

**MUST NOT USE** (❌):
```rust
use hyperswitch_domain_models::RouterData;  // DEPRECATED
use interfaces::ConnectorIntegration;  // DEPRECATED
```

**Validation Check**:
```bash
# Should NOT find old types
grep -r "use.*RouterData[^V]" backend/connector-integration/src/connectors/*.rs
# Empty output = PASS

# Should find new types
grep -r "use.*RouterDataV2" backend/connector-integration/src/connectors/*.rs
# Non-empty output = PASS
```

---

### Flow Types

**MUST USE** (✅):
```rust
use domain_types::router_flow_type::{
    Authorize,
    Capture,
    Void,
    Refund,
    PSync,  // Payment Sync
    RSync,  // Refund Sync
    SetupMandate,
    CompleteAuthorize,
};
```

**Example Usage**:
```rust
impl ConnectorIntegrationV2<Authorize, PaymentFlowData, PaymentAuthorizeData>
    for Stripe<Authorize>
{
    // Implementation
}
```

---

### Amount Types

**MUST USE** (✅):
```rust
use domain_types::MinorUnit;

pub struct Request {
    pub amount: MinorUnit,  // For minor units (cents, etc.)
}
```

**MUST NOT USE** (❌):
```rust
pub struct Request {
    pub amount: i64,    // WRONG - primitive type
    pub amount: f64,    // WRONG - floating point for money
    pub amount: String, // WRONG - unless using StringMinorUnit converter
}
```

**Exception**: When using amount converters:
```rust
// With StringMinorUnit converter
pub struct Request {
    pub amount: String,  // OK with converter
}

macros::create_all_prerequisites!(
    amount_converters: [amount_converter: StringMinorUnit],
);
```

---

## Macro Usage Patterns

### Prerequisites Macro (REQUIRED)

**Location**: After struct definition, before implementations

**Format**:
```rust
macros::create_all_prerequisites!(
    connector_name: ConnectorName,
    api: [
        (flow: FlowType, resource_common_data: CommonDataType),
        // ... all supported flows
    ],
    amount_converters: [amount_converter: ConverterType],
);
```

**Full Example**:
```rust
pub struct Stripe<T> {
    _phantom: PhantomData<T>,
}

macros::create_all_prerequisites!(
    connector_name: Stripe,
    api: [
        (flow: Authorize, resource_common_data: PaymentFlowData),
        (flow: Capture, resource_common_data: PaymentFlowData),
        (flow: Void, resource_common_data: PaymentFlowData),
        (flow: Refund, resource_common_data: RefundFlowData),
        (flow: PSync, resource_common_data: PaymentFlowData),
        (flow: RSync, resource_common_data: RefundFlowData),
    ],
    amount_converters: [amount_converter: StringMinorUnit],
);
```

**Validation Rules**:
- [ ] Macro must be present
- [ ] All implemented flows must be declared
- [ ] `resource_common_data` must match flow type:
  - Payment flows → `PaymentFlowData`
  - Refund flows → `RefundFlowData`
  - Mandate flows → `MandateFlowData`
- [ ] Amount converter declared (if non-MinorUnit)

---

### Implementation Macro (REQUIRED per Flow)

**Format**:
```rust
macros::macro_connector_implementation!(
    connector: ConnectorName,
    flow_name: FlowType,
    resource_common_data: CommonDataType,
    resource_specific_data: SpecificDataType,
    connector_request: RequestType,
    connector_response: ResponseType,
    headers: [(header_name, header_value), ...],
    authentication: auth_method,
);
```

**Full Example**:
```rust
macros::macro_connector_implementation!(
    connector: Stripe,
    flow_name: Authorize,
    resource_common_data: PaymentFlowData,
    resource_specific_data: PaymentAuthorizeData,
    connector_request: AuthorizeRequest,
    connector_response: AuthorizeResponse,
    headers: [("Stripe-Version", "2023-10-16")],
    authentication: auth_type,
);
```

**Validation Rules**:
- [ ] One macro call per flow
- [ ] `connector` matches struct name
- [ ] `flow_name` matches flow type
- [ ] `resource_common_data` matches prerequisites declaration
- [ ] `resource_specific_data` matches flow:
  - Authorize → `PaymentAuthorizeData`
  - Capture → `PaymentCaptureData`
  - Void → `PaymentVoidData`
  - Refund → `RefundExecuteData`
  - PSync → `PaymentSyncData`
  - RSync → `RefundSyncData`
- [ ] Request/Response types defined
- [ ] Headers optional but should include API version if applicable
- [ ] Authentication method: `auth_type` (most common)

---

## Reference ID Handling

### Extraction (REQUIRED)

**MUST USE** (✅):
```rust
// Direct extraction
reference_id: router_data.connector_request_reference_id.clone()

// Or as reference
let reference = &router_data.connector_request_reference_id;

// In transformers
impl TryFrom<&RouterDataV2<...>> for Request {
    fn try_from(router_data: &RouterDataV2<...>) -> Result<Self, Error> {
        Ok(Self {
            reference_id: router_data.connector_request_reference_id.clone(),
            // ... other fields
        })
    }
}
```

**MUST NOT USE** (❌):
```rust
// Hardcoded
reference_id: "TEST123".to_string()  // CRITICAL VIOLATION

// Generated
reference_id: uuid::Uuid::new_v4().to_string()  // CRITICAL VIOLATION

// Mutated
let mut ref_id = router_data.connector_request_reference_id.clone();
ref_id.push_str("-retry");  // CRITICAL VIOLATION
```

**Validation Check**:
```bash
# Check for hardcoded reference IDs
grep -n '"[A-Z0-9_]\{8,\}"' backend/connector-integration/src/connectors/*.rs

# Check for UUID generation
grep -n "Uuid::new_v4" backend/connector-integration/src/connectors/*.rs

# Both should be empty = PASS
```

---

## Status Mapping Rules

### Payment Status Mapping

**Rule**: Map unknown/unmapped statuses to `Pending` (NOT `Failure`)

**Correct** (✅):
```rust
use domain_types::router_enums::AttemptStatus;

status: match api_status.as_str() {
    "success" | "succeeded" | "completed" => AttemptStatus::Charged,
    "pending" | "processing" => AttemptStatus::Pending,
    "failed" | "rejected" | "declined" => AttemptStatus::Failure,
    "requires_action" | "requires_auth" => AttemptStatus::AuthenticationPending,
    "cancelled" | "voided" => AttemptStatus::Voided,
    "unknown" | _ => AttemptStatus::Pending,  // Unknown → Pending
}
```

**Incorrect** (❌):
```rust
status: match api_status.as_str() {
    "success" => AttemptStatus::Charged,
    "pending" => AttemptStatus::Pending,
    "failed" => AttemptStatus::Failure,
    _ => AttemptStatus::Failure,  // WRONG - should be Pending
}
```

**Rationale**: Unknown statuses are temporary states, not failures

---

### Refund Status Mapping

**Rule**: When amount_captured exists, compare refund amount

**Correct** (✅):
```rust
use domain_types::router_enums::RefundStatus;

status: match api_status.as_str() {
    "succeeded" | "completed" => {
        // Check if full refund
        if refund_amount == amount_captured {
            RefundStatus::Success
        } else {
            RefundStatus::Pending  // Partial refund in progress
        }
    }
    "pending" | "processing" => RefundStatus::Pending,
    "failed" | "rejected" => RefundStatus::Failure,
    "unknown" | _ => RefundStatus::Pending,  // Unknown → Pending
}
```

**Special Case**: Partial Refunds
```rust
// If API returns refunded_amount
if refunded_amount < original_amount {
    RefundStatus::Pending  // More refunds possible
} else {
    RefundStatus::Success  // Fully refunded
}
```

---

## Error Handling Rules

### No unwrap/expect (CRITICAL)

**MUST USE** (✅):
```rust
fn process() -> Result<Response, Error> {
    let data = fetch_data()?;  // Propagate with ?
    let transformed = transform(data)?;
    Ok(transformed)
}

// Or with map_err for context
fn process() -> Result<Response, Error> {
    fetch_data()
        .map_err(|e| Error::FetchFailed(e.to_string()))?;
    // ...
}
```

**MUST NOT USE** (❌):
```rust
fn process() -> Response {
    let data = fetch_data().unwrap();  // CRITICAL VIOLATION
    let transformed = transform(data).expect("transform failed");  // CRITICAL VIOLATION
    transformed
}
```

**Validation Check**:
```bash
# Check for unwrap/expect
grep -rn "\.unwrap()" backend/connector-integration/src/connectors/*.rs
grep -rn "\.expect(" backend/connector-integration/src/connectors/*.rs

# Both should be empty = PASS
```

---

### Proper Error Types

**MUST USE** (✅):
```rust
use error_stack::{Report, ResultExt};

fn build_request(router_data: &RouterDataV2<...>)
    -> Result<Request, Report<errors::ConnectorError>>
{
    let amount = router_data.request.amount;
    if amount.is_zero() {
        return Err(Report::new(errors::ConnectorError::InvalidAmount))
            .attach_printable("Amount cannot be zero");
    }

    Ok(Request { amount, ... })
}
```

---

## Authentication Handling

### Extraction from auth_type (REQUIRED)

**MUST USE** (✅):
```rust
use domain_types::connector_auth_type::ConnectorAuthType;

// Pattern matching
let api_key = match &router_data.connector_auth_type {
    ConnectorAuthType::HeaderKey { api_key } => api_key.clone(),
    ConnectorAuthType::BodyKey { api_key, key_1 } => {
        // Use both keys if needed
        (api_key.clone(), key_1.clone())
    },
    _ => {
        return Err(errors::ConnectorError::InvalidAuthType)?;
    }
};

// Or with try_from
let auth = AuthType::try_from(&router_data.connector_auth_type)?;
```

**MUST NOT USE** (❌):
```rust
// Hardcoded credentials
const API_KEY: &str = "sk_live_EXAMPLE";  // CRITICAL VIOLATION

// From environment
let api_key = std::env::var("API_KEY").unwrap();  // CRITICAL VIOLATION

// From config file
let api_key = config.get("api_key");  // CRITICAL VIOLATION
```

**Authentication Types**:
- `HeaderKey { api_key }` - Single API key in header
- `BodyKey { api_key, key_1 }` - Multiple keys (some in body)
- `SignatureKey { api_key, key_1, api_secret }` - Signature-based auth
- `MultiAuthKey { api_key, key_1, api_secret, key_2 }` - Complex multi-key

---

## Data Flow Requirements

### Request Transformation

**Pattern**:
```rust
impl TryFrom<&RouterDataV2<F, Req, Res>> for ConnectorRequest
where
    F: Clone,
    Req: Clone,
    Res: Clone,
{
    type Error = Report<errors::ConnectorError>;

    fn try_from(router_data: &RouterDataV2<F, Req, Res>) -> Result<Self, Self::Error> {
        Ok(Self {
            amount: router_data.request.amount,
            currency: router_data.request.currency,
            reference_id: router_data.connector_request_reference_id.clone(),
            // Extract all fields from router_data, NEVER hardcode
        })
    }
}
```

**Validation Rules**:
- [ ] All data comes from `router_data`
- [ ] No hardcoded values
- [ ] Proper error handling
- [ ] Type conversions use appropriate converters

---

### Response Transformation

**Pattern**:
```rust
impl<F, Req, Res> TryFrom<ResponseRouterData<F, ConnectorResponse, Req, Res>>
    for RouterDataV2<F, Req, Res>
where
    F: Clone,
    Req: Clone,
    Res: Clone,
{
    type Error = Report<errors::ConnectorError>;

    fn try_from(item: ResponseRouterData<F, ConnectorResponse, Req, Res>)
        -> Result<Self, Self::Error>
    {
        Ok(Self {
            status: match item.response.status.as_str() {
                "success" => AttemptStatus::Charged,
                "pending" => AttemptStatus::Pending,
                _ => AttemptStatus::Pending,
            },
            response: Ok(Res {
                connector_transaction_id: item.response.transaction_id,
                // ... other fields
            }),
            ..item.data
        })
    }
}
```

**Validation Rules**:
- [ ] Status mapping follows UCS conventions
- [ ] Transaction ID extracted from response
- [ ] Error responses handled
- [ ] Original router_data preserved (`..item.data`)

---

## Module Structure Requirements

### File Organization

**MUST HAVE**:
- Main file: `backend/connector-integration/src/connectors/{name}.rs`
- Transformers: `backend/connector-integration/src/connectors/{name}/transformers.rs`

**RECOMMENDED**:
- Tests: `backend/connector-integration/tests/{name}_tests.rs`

### Module Declaration

**In connectors.rs**:
```rust
pub mod stripe;
pub mod paypal;
// ... alphabetically ordered
```

**In connector main file**:
```rust
mod transformers;  // Declare transformers submodule

// Rest of implementation
```

---

## Validation Checklist

### Critical Requirements (Must Pass)

- [ ] Uses RouterDataV2 and ConnectorIntegrationV2
- [ ] Amount fields use MinorUnit (or proper converter)
- [ ] Reference ID from router_data (not hardcoded/generated)
- [ ] No unwrap/expect in code
- [ ] Authentication from connector_auth_type
- [ ] No unsafe code blocks
- [ ] create_all_prerequisites! macro present
- [ ] macro_connector_implementation! for each flow
- [ ] Status mapping: unknown → Pending

### Warning-Level Requirements (Should Pass)

- [ ] All implemented flows declared in prerequisites
- [ ] Proper error types used
- [ ] Test coverage exists
- [ ] Module structure follows conventions
- [ ] Documentation present

---

## Version History

- **1.0.0** (2025-12-09): Initial UCS validation rules
  - Type system requirements
  - Macro usage patterns
  - Reference ID handling rules
  - Status mapping conventions
  - Error handling requirements
  - Authentication patterns
  - Data flow patterns
