# Capability Mapping for Research Agent

## Overview

This guide helps the research agent understand what information to extract for each payment flow supported by a connector.

## Standard Flow Types

### 1. Authorize
**Purpose**: Pre-authorize a payment (hold funds without capturing)

**What to Look For**:
- Endpoint for payment creation with `capture` parameter or separate capture flow
- Request fields: amount, currency, payment method, customer info
- Response fields: authorization ID, status, amount authorized
- Status codes: pending/succeeded/failed

**Auto-Capture Signals**:
- "capture" parameter = false → Authorize
- Separate capture endpoint → Authorize

### 2. Capture
**Purpose**: Capture previously authorized funds

**What to Look For**:
- Endpoint to capture an authorization
- Request fields: authorization ID, amount to capture (partial or full)
- Response fields: capture ID, captured amount, status
- Status codes: pending/succeeded/failed

**Signals**:
- Separate capture endpoint
- Reference to "authorization" or "auth" ID

### 3. Void
**Purpose**: Cancel an authorization before capture

**What to Look For**:
- Endpoint to void/cancel authorizations
- Request fields: authorization ID
- Response fields: void ID, status
- Status codes: succeeded/failed

**Signals**:
- "void" or "cancel" terminology
- References to canceling pending authorizations

### 4. Refund
**Purpose**: Refund captured funds

**What to Look For**:
- Endpoint for refunds (full or partial)
- Request fields: payment/capture ID, amount, reason
- Response fields: refund ID, refund amount, status
- Status codes: pending/succeeded/failed

**Signals**:
- "refund" terminology
- References to returning funds to customer

### 5. PSync (Payment Sync)
**Purpose**: Get current status of a payment

**What to Look For**:
- Endpoint to retrieve payment by ID
- Request fields: payment ID or reference
- Response fields: current status, updated timestamp
- Status codes: succeeded/failed/pending

**Signals**:
- "retrieve payment" endpoint
- "get payment status" endpoint
- References to checking payment state

### 6. RSync (Refund Sync)
**Purpose**: Get current status of a refund

**What to Look For**:
- Endpoint to retrieve refund by ID
- Request fields: refund ID
- Response fields: current status, updated timestamp
- Status codes: succeeded/failed/pending

**Signals**:
- "retrieve refund" endpoint
- "get refund status" endpoint

### 7. Mandate (Recurring Payments)
**Purpose**: Set up recurring payment mandates

**What to Look For**:
- Endpoint to create mandates/subscriptions
- Request fields: customer info, payment method, frequency
- Response fields: mandate ID, status, next charge date
- Status codes: active/inactive/failed

**Signals**:
- "subscription" terminology
- "recurring payment" references
- "mandate" or "token" for payment methods

### 8. Verify
**Purpose**: Verify payment method without charging

**What to Look For**:
- Endpoint for payment method verification
- Request fields: payment method details
- Response fields: verification status, error codes
- Status codes: verified/failed/pending

**Signals**:
- "verify" or "validate" terminology
- References to checking payment method validity

## Authentication Patterns to Identify

### 1. HeaderKey
**Signals**:
- Headers like `x-api-key`, `Authorization: Bearer <token>`, `api-key`
- Single static API key for all requests

**Documentation Clues**:
- "Include your API key in the request header"
- "Add x-api-key header with your key"

### 2. CreateAccessToken (OAuth)
**Signals**:
- Separate token endpoint
- Client ID and secret
- "access_token" in responses
- Token refresh mentioned

**Documentation Clues**:
- "Obtain an access token using OAuth"
- "Refresh your token periodically"
- "Token expires after X hours"

### 3. Basic Auth
**Signals**:
- Username and password (API key and secret)
- Base64 encoded credentials in header

**Documentation Clues**:
- "Use HTTP Basic authentication"
- "Include username and password"

## Amount Format Patterns

### StringMinorUnit
**Format**: String with no decimals (e.g., "1000" = $10.00)
**Signals**:
- Amount shown as integers in examples
- "amount_cents" terminology
- Amounts without decimal points
- Documentation says to "pass amounts in cents"

**Example**:
```json
{
  "amount": "1000",
  "currency": "USD"
}
```

### StringMajorUnit
**Format**: String with decimals (e.g., "10.00")
**Signals**:
- Amount shown with decimal point in strings
- Two decimal places in examples
- String type specified

**Example**:
```json
{
  "amount": "10.00",
  "currency": "USD"
}
```

### FloatMajorUnit
**Format**: Number with decimals (e.g., 10.00)
**Signals**:
- Number type (not string)
- Decimals in examples
- Float or number specified

**Example**:
```json
{
  "amount": 10.00,
  "currency": "USD"
}
```

## Status Code Mapping to UCS

| Connector Status | UCS Status | Notes |
|------------------|------------|-------|
| succeeded, success, completed, completed_success | Charged | Payment completed successfully |
| pending, processing, authorized | Pending | Payment in progress |
| failed, declined, error, rejected | Failed | Payment failed |
| canceled, cancelled, voided | Failed | Payment canceled |
| refunded, refund_succeeded | Refunded | Refund completed |
| partially_refunded | Refunded | Partial refund |
| refunded_pending | Pending | Refund processing |

**Unknown Statuses**: Map to `Pending` (not `Failed`)

## Quick Pattern Recognition Checklist

When scraping docs, note:
- [ ] Authentication method (HeaderKey, OAuth, Basic)
- [ ] Amount format (StringMinorUnit, StringMajorUnit, FloatMajorUnit)
- [ ] Which flows are supported (Authorize, Capture, Refund, etc.)
- [ ] Base URLs (sandbox vs production)
- [ ] Rate limits
- [ ] Error response format
- [ ] Webhook support (for notifications)
- [ ] Test/sandbox credentials availability

## Output for Planning Agent

Add a "Quick Pattern Notes" section to spec.md:

```markdown
## Quick Pattern Notes (for planning agent)

**Auth Signals Observed**:
- {what you saw that indicates auth type}

**Amount Format Observed**:
- {actual example from API: "amount": "value"}
- Suggested converter: {based on pattern recognition}

**Flows Confirmed**:
- Authorize: {yes/no}
- Capture: {yes/no}
- Refund: {yes/no}
- Void: {yes/no}
- PSync: {yes/no}
- RSync: {yes/no}

**Additional Notes**:
- {any connector-specific quirks or patterns}
```