# Comprehensive Connector Integration Guide

This guide serves as the central reference for the entire connector integration lifecycle. It is designed to guide the **Classifier**, **Research**, **Planner**, and **Coder-Reviewer-Tester** agents through their respective responsibilities.

---

## 1. For the Classifier Agent: Flow Segregation

**Objective:** Accurately identify and segregate API calls into distinct connector flows.

### Flow Identification Strategy

The Classifier Agent should analyze API endpoints and payloads to map them to the following standard flows. Use the semantic meanings and data structures below to make accurate classifications.

| Flow Name | Semantic Meaning | Key Characteristics |
| :--- | :--- | :--- |
| **Authorize** | Verifies payment details and reserves funds. | **Input:** Card details, Token, Amount.<br>**Output:** Transaction ID, Status (Authorized/Pending). |
| **Capture** | Captures previously authorized funds. | **Input:** Payment ID, Amount.<br>**Output:** Status (Succeeded). |
| **Void** | Cancels an authorized but uncaptured payment. | **Input:** Payment ID.<br>**Output:** Status (Cancelled). |
| **Refund** | Returns funds to the customer. | **Input:** Payment ID, Amount.<br>**Output:** Refund ID, Status. |
| **PSync** (Payment Sync) | Retrieves the current status of a payment. | **Input:** Payment ID.<br>**Output:** Current Status. |
| **RSync** (Refund Sync) | Retrieves the current status of a refund. | **Input:** Refund ID.<br>**Output:** Current Status. |
| **SetupMandate** | Sets up a recurring payment agreement. | **Input:** Customer ID, Payment Method.<br>**Output:** Mandate ID. |
| **CreateConnectorCustomer** | Creates a customer record on the connector side. | **Input:** Customer Details.<br>**Output:** Connector Customer ID. |
| **AcceptDispute** | Accepts a chargeback/dispute. | **Input:** Dispute ID.<br>**Output:** Status (Lost). |
| **DefendDispute** | Submits evidence to challenge a dispute. | **Input:** Dispute ID, Evidence File.<br>**Output:** Status (Under Review). |
| **PreAuthenticate** | Pre-auth setup (e.g., 3DS). | **Input:** Payment Data.<br>**Output:** 3DS Data/Status. |
| **Authenticate** | Core authentication challenge. | **Input:** Challenge Data.<br>**Output:** Auth Status. |
| **PostAuthenticate** | Post-auth finalization. | **Input:** Auth Result.<br>**Output:** Payment Status. |
| **CreateSessionToken** | Generates client-side session token. | **Input:** Payment/Customer Data.<br>**Output:** Session Token. |
| **CreateAccessToken** | Retrieves API access token. | **Input:** Auth Credentials.<br>**Output:** Access Token. |

**Note:** Refer to `connector_flows_analysis.md` for a complete list of all 26 flows and their detailed data structures.

---

## 2. For the Research Agent: Capability Mapping

**Objective:** Understand the semantic meaning of flows and map them to specific connector capabilities.

### Research Checklist

1.  **Endpoint Mapping:** For each flow identified by the Classifier, find the corresponding endpoint in the connector's official API documentation.
2.  **Field Mapping:** Map the connector's request/response fields to the Hyperswitch domain types (e.g., `PaymentsAuthorizeData`, `PaymentsResponseData`).
3.  **Auth Type:** Identify the authentication mechanism (API Key, Basic Auth, Signature, etc.) and map it to `ConnectorAuthType`.
4.  **Status Mapping:** Create a mapping table between the connector's status codes/strings and Hyperswitch's `AttemptStatus` (e.g., "succeeded" -> `Charged`, "requires_action" -> `AuthenticationPending`).
5.  **Refactor Compliance:** Ensure the mapping aligns with the new proto definitions (e.g., `request_ref_id` instead of `connector_request_reference_id`) as outlined in the `refactor-docs`.

---

## 3. For the Planner Agent: Integration Strategy

**Objective:** Plan the implementation using the Macro Framework to ensure consistency and reduce boilerplate.

### Implementation Plan Template

The Planner should generate an `implementation_plan.md` that follows this structure:

1.  **Prerequisites Setup (`create_all_prerequisites!`)**
    *   Define the `Connector` struct.
    *   List all supported flows in the `api` array.
    *   Define `member_functions` for common logic (headers, base URL).

2.  **Transformer Implementation (`transformers.rs`)**
    *   Plan the Request Structs (implementing `Serialize`).
    *   Plan the Response Structs (implementing `Deserialize`).
    *   Plan the `TryFrom` implementations for converting `RouterData` -> `Request` and `Response` -> `RouterData`.

3.  **Flow Implementation (`macro_connector_implementation!`)**
    *   For each flow, define the `macro_connector_implementation!` block.
    *   Specify `curl_request` (Json/Form) and `curl_response`.
    *   Define `get_url` and any specific `get_headers` logic.

4.  **Refactor Alignment**
    *   Ensure the plan accounts for the "Phase 5: Connector & Client Updates" requirements.
    *   **Critical:** Plan for `PaymentMethod` oneof structure updates and field renames (e.g., `connector_request_reference_id` -> `request_ref_id`).

---

## 5. File Structure Pattern

Every connector integration requires changes to these files:

```
backend/connector-integration/src/
├── connectors.rs              # Add module declaration
├── connectors/
│   └── <connector_name>.rs    # Main connector implementation
│   └── <connector_name>/
│       └── transformers.rs    # Request/response transformers
├── types.rs                   # Add connector type alias

backend/domain_types/src/
├── connector_types.rs         # Add connector enum variant
├── types.rs                   # Add connector config

config/
├── development.toml           # Add base_url
├── production.toml            # Add base_url (different from sandbox!)
├── sandbox.toml               # Add base_url
```

---

## 6. Core UCS Architecture Rules

### CRITICAL: Types to Use

```rust
// ✅ CORRECT
use domain_types::router_data_v2::RouterDataV2;
use interfaces::connector_integration_v2::ConnectorIntegrationV2;
use domain_types::MinorUnit;  // For all amount fields

// ❌ WRONG - Never use these
use hyperswitch_domain_models::RouterData;  // Legacy
use interfaces::ConnectorIntegration;       // Legacy
pub amount: i64;  // Use MinorUnit instead
pub amount: f64;  // Never use floats for money
```

### Generic Connector Struct

```rust
// Connector must be generic over payment method data
pub struct ConnectorName<T: PaymentMethodDataTypes + Debug + Sync + Send + 'static + Serialize> {
    _marker: std::marker::PhantomData<T>,
}
```

---

## 7. Quality Checklist

Before submitting, ensure the following:

- [ ] Using `RouterDataV2` (not `RouterData`)
- [ ] Using `ConnectorIntegrationV2` (not `ConnectorIntegration`)
- [ ] All amounts use `MinorUnit` type
- [ ] Amount converters declared (not empty)
- [ ] Currency uses `common_enums::Currency` enum
- [ ] Status mapping uses enum with `From` impl
- [ ] Reference IDs extracted from router_data (never hardcoded/mutated)
- [ ] No `unwrap()` - use `?` operator
- [ ] Errors include `attach_printable` context
- [ ] PII fields wrapped in `Secret<>`
- [ ] Production URL differs from sandbox in config
- [ ] No `skip_serializing_if` on response structs
- [ ] Using utility functions (get_billing_country, etc.)

---

## 8. For the Coder-Reviewer-Tester Loop

**Objective:** Execute the plan, review the code against strict standards, and validate functionality.

### Coder Guidelines

*   **Use Macros:** Strictly adhere to the `macro_framework.md`. Do not manually implement `ConnectorIntegrationV2` unless absolutely necessary.
*   **Refactor-Ready Code:** Write code that is compatible with the new proto definitions.
    *   Use `PaymentMethod` oneof pattern.
    *   Use updated field names (`request_ref_id`, `response_ref_id`).
*   **Error Handling:** Implement robust error mapping in `build_error_response`. Ensure all connector errors are mapped to standard `ErrorResponse` codes.

### Reviewer Checklist

*   [ ] **Macro Usage:** Is `create_all_prerequisites!` used correctly? Are flows defined using `macro_connector_implementation!`?
*   [ ] **Type Safety:** Are `TryFrom` implementations used for all data conversions?
*   [ ] **Refactor Compliance:** Does the code use the new `PaymentMethod` structure? Are legacy field names avoided?
*   [ ] **Security:** Are sensitive fields (API keys, card numbers) handled using `Secret<T>`?
*   [ ] **Completeness:** Are all flows identified in the Research phase implemented?

### Tester & Validation Strategy

Refer to `refactor-docs/07-phase6-testing-validation.md` for detailed procedures.

1.  **Integration Tests:**
    *   Run `cargo test <connector_name>_integration_test`.
    *   Verify all flows (Authorize, Capture, Refund, etc.) pass.

2.  **Manual Verification (if needed):**
    *   Use the `browser` tool to verify UI flows if applicable.
    *   Trigger webhooks manually and verify `WebhookProcessor` handles them correctly.

3.  **gRPC Testing (`grpcurl`):**
    *   Construct `grpcurl` commands for each flow by inspecting the proto contract (`payment.proto`, `services.proto`).
    *   Verify successful responses and correct field mappings for all flows.
    *   **Required Headers:** Ensure you include necessary headers like `x-tenant-id` (usually `default`), `x-merchant-id`, or any other required metadata.
    *   Example: `grpcurl -plaintext -H "x-tenant-id: default" -d '{"request_ref_id": {"id": "123"}, ...}' localhost:50051 payment.PaymentService/Authorize`

4.  **Performance Check:**
    *   Ensure no significant latency regression.
    *   Verify memory usage is within limits.

---

## Reference Documents

*   **Flow Analysis:** `connector_flows_analysis.md`
*   **Macro Guide:** `connector_integration_macros.md`
