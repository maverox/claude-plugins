# Connector Patterns Reference

**Version**: 1.0.0
**Purpose**: Common connector implementation patterns and templates

---

## Authentication Patterns

### Pattern 1: API Key in Header

**Common For**: Most REST APIs (Stripe, Square, Adyen, etc.)

**API Documentation Example**:
```
Authorization: Bearer sk_test_EXAMPLE
```

**Implementation**:
```rust
use domain_types::connector_auth_type::ConnectorAuthType;

// Extract auth
let api_key = match &router_data.connector_auth_type {
    ConnectorAuthType::HeaderKey { api_key } => api_key,
    _ => return Err(errors::ConnectorError::InvalidAuthType)?,
};

// Use in headers
headers: [("Authorization", format!("Bearer {}", api_key))],
// Or in macro
headers: [("Authorization", format!("Bearer {}", api_key))],
```

---

### Pattern 2: API Key in Query Parameter

**Common For**: Some payment gateways

**API Documentation Example**:
```
GET /payment?api_key=abc123
```

**Implementation**:
```rust
let api_key = match &router_data.connector_auth_type {
    ConnectorAuthType::HeaderKey { api_key } => api_key,
    _ => return Err(errors::ConnectorError::InvalidAuthType)?,
};

// Add to URL
let url = format!("{}?api_key={}", base_url, api_key);
```

---

### Pattern 3: Multiple Keys (API Key + Secret)

**Common For**: Signature-based auth (PayPal, Authorize.net)

**API Documentation Example**:
```
Authorization: Basic base64(api_key:api_secret)
```

**Implementation**:
```rust
use domain_types::connector_auth_type::ConnectorAuthType;
use base64::{Engine as _, engine::general_purpose};

let (api_key, api_secret) = match &router_data.connector_auth_type {
    ConnectorAuthType::BodyKey { api_key, key_1 } => (api_key, key_1),
    _ => return Err(errors::ConnectorError::InvalidAuthType)?,
};

// Create Basic auth
let credentials = format!("{}:{}", api_key, api_secret);
let encoded = general_purpose::STANDARD.encode(credentials.as_bytes());
let auth_header = format!("Basic {}", encoded);

// Use in headers
headers: [("Authorization", auth_header)],
```

---

### Pattern 4: OAuth Bearer Token

**Common For**: OAuth-based APIs

**API Documentation Example**:
```
Authorization: Bearer {access_token}
```

**Implementation**:
```rust
let access_token = match &router_data.connector_auth_type {
    ConnectorAuthType::HeaderKey { api_key } => api_key,  // access_token stored as api_key
    _ => return Err(errors::ConnectorError::InvalidAuthType)?,
};

headers: [("Authorization", format!("Bearer {}", access_token))],
```

---

### Pattern 5: Signature-Based Authentication

**Common For**: High-security APIs (Cybersource, Worldpay)

**API Documentation Example**:
```
X-Signature: sha256(payload + secret)
```

**Implementation**:
```rust
use hmac::{Hmac, Mac};
use sha2::Sha256;

let (api_key, api_secret) = match &router_data.connector_auth_type {
    ConnectorAuthType::SignatureKey { api_key, api_secret, .. } => (api_key, api_secret),
    _ => return Err(errors::ConnectorError::InvalidAuthType)?,
};

// Create signature
type HmacSha256 = Hmac<Sha256>;
let mut mac = HmacSha256::new_from_slice(api_secret.as_bytes())
    .map_err(|_| errors::ConnectorError::InvalidAuthType)?;
mac.update(payload.as_bytes());
let signature = hex::encode(mac.finalize().into_bytes());

headers: [
    ("X-API-Key", api_key.to_string()),
    ("X-Signature", signature),
],
```

---

## Amount Converter Patterns

### Pattern 1: Integer Minor Units (Default)

**Common For**: APIs expecting cents/pence as integer

**API Format**: `1000` (for $10.00)

**Implementation**:
```rust
// In prerequisites
amount_converters: [amount_converter: MinorUnit],

// In transformer
impl TryFrom<&RouterDataV2<...>> for Request {
    fn try_from(router_data: &RouterDataV2<...>) -> Result<Self, Error> {
        Ok(Self {
            amount: router_data.request.amount.get_amount_as_i64(),
            currency: router_data.request.currency,
        })
    }
}
```

---

### Pattern 2: String Minor Units

**Common For**: APIs expecting cents as string

**API Format**: `"1000"` (for $10.00)

**Implementation**:
```rust
// In prerequisites
amount_converters: [amount_converter: StringMinorUnit],

// In transformer
impl TryFrom<&RouterDataV2<...>> for Request {
    fn try_from(router_data: &RouterDataV2<...>) -> Result<Self, Error> {
        Ok(Self {
            amount: router_data.request.amount.to_string(),
            currency: router_data.request.currency,
        })
    }
}
```

---

### Pattern 3: Decimal Amount

**Common For**: APIs expecting decimal strings

**API Format**: `"10.50"` (for $10.50)

**Implementation**:
```rust
// In prerequisites
amount_converters: [amount_converter: DecimalAmount],

// In transformer
use domain_types::MinorUnit;

impl TryFrom<&RouterDataV2<...>> for Request {
    fn try_from(router_data: &RouterDataV2<...>) -> Result<Self, Error> {
        let amount_decimal = router_data.request.amount.get_amount_as_f64() / 100.0;

        Ok(Self {
            amount: format!("{:.2}", amount_decimal),
            currency: router_data.request.currency,
        })
    }
}
```

---

### Pattern 4: Major Units

**Common For**: Some currencies (JPY, KRW - no decimal places)

**API Format**: `1050` (for ¥1050)

**Implementation**:
```rust
// Check if zero-decimal currency
fn get_amount_value(amount: MinorUnit, currency: Currency) -> String {
    if is_zero_decimal_currency(currency) {
        // No conversion needed for JPY, KRW, etc.
        amount.get_amount_as_i64().to_string()
    } else {
        // Convert minor to major units
        let major = amount.get_amount_as_f64() / 100.0;
        format!("{:.2}", major)
    }
}
```

---

## Status Mapping Patterns

### Pattern 1: Simple Status Mapping

**Common For**: APIs with clear success/pending/failed states

```rust
use domain_types::router_enums::AttemptStatus;

status: match response.status.as_str() {
    "success" | "succeeded" | "approved" => AttemptStatus::Charged,
    "pending" | "processing" | "in_progress" => AttemptStatus::Pending,
    "failed" | "rejected" | "declined" => AttemptStatus::Failure,
    "cancelled" | "voided" => AttemptStatus::Voided,
    _ => AttemptStatus::Pending,  // Unknown → Pending
}
```

---

### Pattern 2: Code-Based Status

**Common For**: APIs using numeric status codes

```rust
status: match response.status_code {
    200 | 201 => AttemptStatus::Charged,
    202 | 204 => AttemptStatus::Pending,
    400..=499 => AttemptStatus::Failure,
    _ => AttemptStatus::Pending,
}
```

---

### Pattern 3: 3DS Authentication

**Common For**: APIs supporting 3D Secure

```rust
status: match (response.status.as_str(), response.requires_3ds) {
    ("success", false) => AttemptStatus::Charged,
    ("success", true) | ("requires_authentication", _) => {
        AttemptStatus::AuthenticationPending
    }
    ("pending", _) => AttemptStatus::Pending,
    ("failed", _) => AttemptStatus::Failure,
    _ => AttemptStatus::Pending,
}
```

---

### Pattern 4: Refund Status with Partial Support

**Common For**: APIs supporting partial refunds

```rust
use domain_types::router_enums::RefundStatus;

status: match response.status.as_str() {
    "succeeded" => {
        // Check if fully refunded
        if response.refunded_amount >= response.original_amount {
            RefundStatus::Success
        } else {
            RefundStatus::Pending  // Partial refund, more possible
        }
    }
    "pending" | "processing" => RefundStatus::Pending,
    "failed" | "rejected" => RefundStatus::Failure,
    _ => RefundStatus::Pending,
}
```

---

## Request Structure Patterns

### Pattern 1: Simple JSON Request

**Common For**: Most REST APIs

```rust
#[derive(Serialize)]
pub struct AuthorizeRequest {
    pub amount: String,
    pub currency: String,
    pub reference: String,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}
```

---

### Pattern 2: Nested Card Data

**Common For**: Card payment requests

```rust
#[derive(Serialize)]
pub struct AuthorizeRequest {
    pub amount: MinorUnit,
    pub currency: Currency,
    pub card: CardDetails,
}

#[derive(Serialize)]
pub struct CardDetails {
    pub number: Secret<String>,
    pub exp_month: Secret<String>,
    pub exp_year: Secret<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub cvv: Option<Secret<String>>,
}
```

---

### Pattern 3: Multiple Payment Methods

**Common For**: APIs supporting various payment methods

```rust
#[derive(Serialize)]
#[serde(tag = "payment_method")]
pub enum PaymentMethodData {
    #[serde(rename = "card")]
    Card { card: CardDetails },

    #[serde(rename = "bank_transfer")]
    BankTransfer { bank: BankDetails },

    #[serde(rename = "wallet")]
    Wallet { wallet: WalletDetails },
}

#[derive(Serialize)]
pub struct AuthorizeRequest {
    pub amount: MinorUnit,
    pub currency: Currency,

    #[serde(flatten)]
    pub payment_method: PaymentMethodData,
}
```

---

### Pattern 4: Form-Encoded Requests

**Common For**: Some legacy APIs

```rust
#[derive(Serialize)]
pub struct AuthorizeRequest {
    #[serde(rename = "paymentAmount")]
    pub amount: String,

    #[serde(rename = "currencyCode")]
    pub currency: String,

    #[serde(rename = "cardNumber")]
    pub card_number: Secret<String>,
}

// In connector
content_type: "application/x-www-form-urlencoded",
```

---

## Response Parsing Patterns

### Pattern 1: Simple JSON Response

```rust
#[derive(Deserialize)]
pub struct AuthorizeResponse {
    pub transaction_id: String,
    pub status: String,

    #[serde(default)]
    pub message: Option<String>,
}
```

---

### Pattern 2: Nested Response

```rust
#[derive(Deserialize)]
pub struct AuthorizeResponse {
    pub data: ResponseData,
    pub status: String,
}

#[derive(Deserialize)]
pub struct ResponseData {
    pub id: String,
    pub amount: String,
    pub currency: String,
}
```

---

### Pattern 3: Error Response

```rust
#[derive(Deserialize)]
#[serde(untagged)]
pub enum ApiResponse {
    Success(SuccessResponse),
    Error(ErrorResponse),
}

#[derive(Deserialize)]
pub struct SuccessResponse {
    pub transaction_id: String,
    pub status: String,
}

#[derive(Deserialize)]
pub struct ErrorResponse {
    pub error: ErrorDetails,
}

#[derive(Deserialize)]
pub struct ErrorDetails {
    pub code: String,
    pub message: String,
}

// In transformer
impl TryFrom<ResponseRouterData<...>> for RouterDataV2<...> {
    fn try_from(item: ResponseRouterData<...>) -> Result<Self, Error> {
        match item.response {
            ApiResponse::Success(success) => {
                // Handle success
                Ok(Self { ... })
            }
            ApiResponse::Error(error) => {
                // Return error
                Err(errors::ConnectorError::ResponseError {
                    code: error.error.code,
                    message: error.error.message,
                })?
            }
        }
    }
}
```

---

### Pattern 4: Response with Metadata

```rust
#[derive(Deserialize)]
pub struct AuthorizeResponse {
    pub id: String,
    pub status: String,

    #[serde(flatten)]
    pub metadata: HashMap<String, serde_json::Value>,
}
```

---

## Flow Implementation Patterns

### Pattern 1: Authorize Flow

**Purpose**: Create payment authorization

**Request Builder**:
```rust
impl TryFrom<&RouterDataV2<Authorize, PaymentFlowData, PaymentAuthorizeData>>
    for AuthorizeRequest
{
    fn try_from(router_data: &RouterDataV2<...>) -> Result<Self, Error> {
        Ok(Self {
            amount: router_data.request.amount,
            currency: router_data.request.currency,
            reference: router_data.connector_request_reference_id.clone(),
            payment_method: get_payment_method_data(&router_data.request.payment_method_data)?,
        })
    }
}
```

**Response Handler**:
```rust
impl TryFrom<ResponseRouterData<Authorize, AuthorizeResponse, ...>>
    for RouterDataV2<Authorize, ...>
{
    fn try_from(item: ResponseRouterData<...>) -> Result<Self, Error> {
        Ok(Self {
            status: match item.response.status.as_str() {
                "authorized" => AttemptStatus::Authorized,
                "captured" => AttemptStatus::Charged,
                _ => AttemptStatus::Pending,
            },
            response: Ok(PaymentAuthorizeData {
                connector_transaction_id: item.response.transaction_id,
                ...
            }),
            ..item.data
        })
    }
}
```

---

### Pattern 2: Capture Flow

**Purpose**: Capture previously authorized payment

**Request Builder**:
```rust
impl TryFrom<&RouterDataV2<Capture, PaymentFlowData, PaymentCaptureData>>
    for CaptureRequest
{
    fn try_from(router_data: &RouterDataV2<...>) -> Result<Self, Error> {
        Ok(Self {
            transaction_id: router_data.request.connector_transaction_id.clone(),
            amount: router_data.request.amount_to_capture,
            reference: router_data.connector_request_reference_id.clone(),
        })
    }
}
```

---

### Pattern 3: Void Flow

**Purpose**: Cancel authorization

**Request Builder**:
```rust
impl TryFrom<&RouterDataV2<Void, PaymentFlowData, PaymentVoidData>>
    for VoidRequest
{
    fn try_from(router_data: &RouterDataV2<...>) -> Result<Self, Error> {
        Ok(Self {
            transaction_id: router_data.request.connector_transaction_id.clone(),
            reference: router_data.connector_request_reference_id.clone(),
        })
    }
}
```

---

### Pattern 4: Refund Flow

**Purpose**: Refund captured payment

**Request Builder**:
```rust
impl TryFrom<&RouterDataV2<Refund, RefundFlowData, RefundExecuteData>>
    for RefundRequest
{
    fn try_from(router_data: &RouterDataV2<...>) -> Result<Self, Error> {
        Ok(Self {
            payment_id: router_data.request.connector_transaction_id.clone(),
            amount: router_data.request.refund_amount,
            currency: router_data.request.currency,
            reference: router_data.connector_request_reference_id.clone(),
            reason: router_data.request.reason.clone(),
        })
    }
}
```

**Response Handler**:
```rust
impl TryFrom<ResponseRouterData<Refund, RefundResponse, ...>>
    for RouterDataV2<Refund, ...>
{
    fn try_from(item: ResponseRouterData<...>) -> Result<Self, Error> {
        Ok(Self {
            response: Ok(RefundExecuteData {
                refund_id: item.response.refund_id,
                connector_refund_id: Some(item.response.connector_refund_id),
            }),
            status: match item.response.status.as_str() {
                "succeeded" => RefundStatus::Success,
                "pending" => RefundStatus::Pending,
                _ => RefundStatus::Pending,
            },
            ..item.data
        })
    }
}
```

---

## Error Handling Patterns

### Pattern 1: HTTP Error Mapping

```rust
impl From<reqwest::StatusCode> for errors::ConnectorError {
    fn from(status: reqwest::StatusCode) -> Self {
        match status {
            reqwest::StatusCode::BAD_REQUEST => {
                errors::ConnectorError::InvalidRequest
            }
            reqwest::StatusCode::UNAUTHORIZED => {
                errors::ConnectorError::AuthenticationFailed
            }
            reqwest::StatusCode::NOT_FOUND => {
                errors::ConnectorError::ResourceNotFound
            }
            _ => errors::ConnectorError::UnknownError,
        }
    }
}
```

---

### Pattern 2: API Error Response

```rust
#[derive(Deserialize)]
pub struct ErrorResponse {
    pub error_code: String,
    pub error_message: String,
}

impl TryFrom<ErrorResponse> for errors::ConnectorError {
    fn try_from(error: ErrorResponse) -> Result<Self, Self::Error> {
        Ok(errors::ConnectorError::ResponseError {
            code: error.error_code,
            message: error.error_message,
        })
    }
}
```

---

## Version History

- **1.0.0** (2025-12-09): Initial connector patterns
  - Authentication patterns (5 types)
  - Amount converter patterns (4 types)
  - Status mapping patterns (4 types)
  - Request structure patterns (4 types)
  - Response parsing patterns (4 types)
  - Flow implementation patterns (4 flows)
  - Error handling patterns
