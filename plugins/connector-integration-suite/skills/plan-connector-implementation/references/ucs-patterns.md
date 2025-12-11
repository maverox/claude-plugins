# UCS Architecture Patterns for Planning

## Overview

This reference helps planners map connector API requirements to UCS (Universal Connector Service) architecture patterns.

## Standard Flow Classifications

### Core Payment Flows

#### 1. Authorize
**Definition**: Reserve funds on customer's payment method without capturing
**Characteristics**:
- Funds held but not transferred
- Authorization has expiration time
- Later captured (full or partial) or voided
**Connector Signals**:
- Separate capture endpoint
- "authorization" ID in responses
- Capture parameter or flow
- Authorization expiry mentioned

#### 2. Capture
**Definition**: Transfer reserved funds to merchant account
**Characteristics**:
- References previous authorization
- Can be full or partial capture
- Finalizes the payment
**Connector Signals**:
- "capture" endpoint or method
- References authorization ID
- Captured amount parameter

#### 3. Void
**Definition**: Cancel authorization before capture
**Characteristics**:
- Only before capture
- Releases reserved funds
- Cannot be undone
**Connector Signals**:
- "void" or "cancel" terminology
- References authorization ID
- Pre-capture only

#### 4. Refund
**Definition**: Return captured funds to customer
**Characteristics**:
- After successful capture
- Can be full or partial
- Creates negative transaction
**Connector Signals**:
- "refund" endpoint or method
- References payment or capture ID
- Refund amount parameter

### Status Sync Flows

#### 5. PSync (Payment Sync)
**Definition**: Get current status of a payment
**Characteristics**:
- Retrieval of payment by ID
- Returns current state
- No state changes
**Connector Signals**:
- "get payment" endpoint
- Payment ID parameter
- Status field in response

#### 6. RSync (Refund Sync)
**Definition**: Get current status of a refund
**Characteristics**:
- Retrieval of refund by ID
- Returns current state
- No state changes
**Connector Signals**:
- "get refund" endpoint
- Refund ID parameter
- Status field in response

### Authentication Flows

#### 7. PreAuthenticate
**Definition**: Setup/verify payment method without authorization
**Characteristics**:
- 3DS or verification only
- No funds reserved
- Creates token for future use
**Connector Signals**:
- "verify" terminology
- Token in response
- No amount in request

#### 8. Authenticate
**Definition**: Complete authentication/verification step
**Characteristics**:
- Part of 3DS flow
- Confirms customer identity
- May require customer interaction
**Connector Signals**:
- "authenticate" or "verify"
- 3DS references
- Customer interaction mentioned

#### 9. PostAuthenticate
**Definition**: Complete post-authentication step
**Characteristics**:
- After 3DS verification
- Finalizes setup
- May create mandate
**Connector Signals**:
- "post-authenticate"
- Following PreAuthenticate
- Mandate creation

#### 10. CreateAccessToken
**Definition**: Obtain OAuth access token
**Characteristics**:
- Separate auth flow
- Client credentials required
- Token expires
**Connector Signals**:
- OAuth terminology
- "access_token" in response
- Token expiry mentioned
- Client ID/secret required

#### 11. CreateSessionToken
**Definition**: Create session-specific token
**Characteristics**:
- Temporary token
- Session-scoped
- Not OAuth
**Connector Signals**:
- "session token"
- Temporary/short-lived
- No OAuth flow

### Recurring Payment Flows

#### 12. CreateMandate
**Definition**: Setup recurring payment authorization
**Characteristics**:
- Customer consent for recurring
- Payment method token required
- Future payments reference mandate
**Connector Signals**:
- "mandate" or "recurring"
- Subscription references
- Payment method token
- Customer consent

#### 13. UpdateMandate
**Definition**: Modify existing mandate
**Characteristics**:
- References existing mandate
- Changes parameters
- Requires prior mandate ID
**Connector Signals**:
- "update mandate"
- Mandate ID required
- Parameter changes

#### 14. RevokeMandate
**Definition**: Cancel recurring payment authorization
**Characteristics**:
- Stops future payments
- Cannot be undone
- May need customer confirmation
**Connector Signals**:
- "revoke" or "cancel"
- Mandate ID required
- Final/stopping action

## Authentication Type Mapping

### HeaderKey
**Pattern**: Static API key in headers
**UCS Mapping**: `ConnectorAuthType::HeaderKey`
**Connector Examples**:
- Header: `x-api-key: {key}`
- Header: `Authorization: Bearer {key}`
- Header: `api-key: {key}`

**Planning Notes**:
- No token refresh needed
- Single credential type
- Simple header configuration

### CreateAccessToken
**Pattern**: OAuth with separate token endpoint
**UCS Mapping**: `ConnectorAuthType::CreateAccessToken`
**Connector Examples**:
- POST to `/oauth/token` with client_id/secret
- Returns `access_token` with expiry
- Refresh token provided
- Separate credential management

**Planning Notes**:
- Requires token refresh logic
- Multiple credential types
- Token lifecycle management
- Add `CreateAccessToken` flow

### Signature
**Pattern**: Request signing (HMAC or similar)
**UCS Mapping**: `ConnectorAuthType::Signature`
**Connector Examples**:
- Signs request body
- Includes signature in headers
- Uses secret key
- Timestamp verification

**Planning Notes**:
- Custom signing logic needed
- Secret key management
- Timestamp handling

### MultiHeaderKey
**Pattern**: Multiple header fields
**UCS Mapping**: `ConnectorAuthType::MultiHeaderKey`
**Connector Examples**:
- API key: `x-api-key`
- API secret: `x-api-secret`
- Merchant ID: `x-merchant-id`

**Planning Notes**:
- Multiple credential fields
- Complex header structure
- Validate all required headers

## Amount Converter Selection

### StringMinorUnit
**UCS Type**: `StringMinorUnitConverter`
**Format**: Strings without decimals (e.g., "1000" = $10.00)
**Connector Examples**:
```json
"amount": "1000"
"amount_cents": 1000
```

**Planning Notes**:
- Amounts in smallest currency unit
- No decimal point
- Integer values in strings
- Common for older APIs

### StringMajorUnit
**UCS Type**: `StringMajorUnitConverter`
**Format**: Strings with decimals (e.g., "10.00")
**Connector Examples**:
```json
"amount": "10.00"
"amount": "10.5"
```

**Planning Notes**:
- Decimal point in strings
- Always specify decimal places
- String type, not number

### FloatMajorUnit
**UCS Type**: `FloatMajorUnitConverter`
**Format**: Numbers with decimals (e.g., 10.00)
**Connector Examples**:
```json
"amount": 10.00
"amount": 10.5
```

**Planning Notes**:
- Number type, not string
- Decimal precision varies
- May lose precision with large amounts

## Status Mapping Patterns

### Payment Statuses

| Connector Status | UCS AttemptStatus | Notes |
|------------------|-------------------|-------|
| succeeded, success, completed | `Charged` | ✅ Payment complete |
| pending, processing, authorized | `Pending` | ⏳ In progress |
| failed, declined, error, rejected | `Failed` | ❌ Payment failed |
| canceled, cancelled, voided | `Failed` | ❌ User canceled |
| requires_action, 3ds_required | `Pending` | ⏳ Additional auth needed |

**Rule**: Unknown statuses → `Pending` (never `Failed`)

### Refund Statuses

| Connector Status | UCS RefundStatus | Notes |
|------------------|------------------|-------|
| succeeded, success, completed | `Refunded` | ✅ Refund complete |
| pending, processing | `Pending` | ⏳ In progress |
| failed, declined | `Failed` | ❌ Refund failed |

### Void Statuses

| Connector Status | UCS VoidStatus | Notes |
|------------------|----------------|-------|
| succeeded, success, completed | `Voided` | ✅ Void complete |
| pending, processing | `Pending` | ⏳ In progress |
| failed, declined | `Failed` | ❌ Void failed |

## Reference ID Extraction

### Payment Reference
**UCS Field**: `payment_id`
**Extraction**: From response field (e.g., `id`, `payment_id`, `transaction_id`)
**Usage**: For PSync, Capture, Refund operations

### Authorization Reference
**UCS Field**: `authorization_id`
**Extraction**: From response field (e.g., `authorization_id`, `auth_id`)
**Usage**: For Capture, Void operations

### Refund Reference
**UCS Field**: `refund_id`
**Extraction**: From response field (e.g., `refund_id`, `id`)
**Usage**: For RSync operations

**Planning Rules**:
1. Always extract from responses (never generate)
2. Store exactly as received (no mutation)
3. Use for subsequent API calls
4. Document extraction field clearly

## Implementation Plan Template

```markdown
# Implementation Plan - {Connector Name}

## 1. Architecture Choices
- **Auth Type**: {HeaderKey/CreateAccessToken/Signature/MultiHeaderKey}
  - Pattern: {Pattern name from above}
  - Headers: {List required headers}
  - Credentials: {What credentials needed}
- **Amount Converter**: {StringMinorUnit/StringMajorUnit/FloatMajorUnit}
  - Based on: {Evidence from API}
  - Examples: {Actual examples}
- **Base URL**: {Sandbox/Production URLs}

## 2. Flow Mapping
| Flow Type | Endpoint | HTTP Method | UCS Flow | Status Mapping |
|-----------|----------|-------------|----------|----------------|
| {Flow} | {Path} | {Method} | {Flow Name} | {connector_status→UCS_status} |
| ... | ... | ... | ... | ... |

## 3. Reference ID Strategy
- **Payment ID**: Extract from `{field_name}` in response
- **Authorization ID**: Extract from `{field_name}` in response
- **Refund ID**: Extract from `{field_name}` in response

## 4. Data Transformations
- **Customer Data**: {How to map customer fields}
- **Metadata**: {How to handle additional data}
- **Error Mapping**: {How to map connector errors to UCS errors}

## 5. Special Instructions
- {Connector-specific requirements}
- {Edge cases to handle}
- {Validation rules}
- {Rate limiting notes}
```

## Common Planning Questions

1. **Flow Classification Ambiguity**
   - Q: "Endpoint returns payment token without amount - is this PreAuthenticate or Authorize?"
   - A: PreAuthenticate (no amount = verification only)

2. **Status Mapping Edge Cases**
   Q: "API returns 'processing' status - what UCS status?"
   A: `Pending` (intermediate statuses map to Pending)

3. **Amount Format Confirmation**
   Q: "API shows 'amount': '1000' - confirm converter?"
   A: StringMinorUnit (string without decimals = minor units)

4. **Auth Flow Validation**
   Q: "API has token endpoint and refresh logic - is this CreateAccessToken?"
   A: Yes, if separate token flow with expiry

5. **Reference ID Issues**
   Q: "API returns 'payment_id' but implementation expects 'id'"
   A: Map in transformer: `router_data.payment_id = response.payment_id`