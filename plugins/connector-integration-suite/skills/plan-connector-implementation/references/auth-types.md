# Authentication Type Reference

## Overview

Guide for identifying and mapping connector authentication methods to UCS ConnectorAuthType patterns.

## Authentication Type Patterns

### 1. HeaderKey
**Definition**: Simple API key passed in request headers
**UCS Mapping**: `ConnectorAuthType::HeaderKey`
**Complexity**: Low

#### Identification Signals
- Single API key credential
- Static key (no expiry)
- Simple header like `x-api-key` or `Authorization: Bearer {key}`
- No separate token request
- Key obtained from dashboard/API keys section

#### Header Patterns
```bash
# Pattern 1: x-api-key
Header: x-api-key: sk_live_...

# Pattern 2: Authorization Bearer
Header: Authorization: Bearer sk_live_...

# Pattern 3: api-key
Header: api-key: your_api_key

# Pattern 4: Custom header
Header: X-MyService-Key: your_key
```

#### Documentation Clues
- "Include your API key in the x-api-key header"
- "Add the API key to the Authorization header"
- "Use HTTP header authentication with your API key"
- "Your API key can be found in the dashboard"

#### Planning Notes
- Simple to implement
- No token refresh needed
- Single credential type
- Key may be prefixed (e.g., `sk_live_`, `pk_`)

#### Examples
**Stripe**:
```bash
curl https://api.stripe.com/v1/charges \
  -u sk_test_...:  # API key as basic auth username
```
**AWS (some services)**:
```bash
curl https://service.amazonaws.com \
  -H "x-api-key: YOUR_API_KEY"
```

---

### 2. CreateAccessToken
**Definition**: OAuth-style flow with separate token endpoint
**UCS Mapping**: `ConnectorAuthType::CreateAccessToken`
**Complexity**: High

#### Identification Signals
- Separate token endpoint (e.g., `/oauth/token`, `/auth/token`)
- Client ID and Client Secret required
- Returns `access_token` with expiry
- Refresh token provided
- Token used in Authorization header
- Documentation has "OAuth" section

#### Token Request Flow
```bash
# Step 1: Obtain token
POST /oauth/token
Headers:
  Content-Type: application/x-www-form-urlencoded
Body:
  grant_type=client_credentials
  client_id=your_client_id
  client_secret=your_client_secret

# Response
{
  "access_token": "eyJ...",
  "expires_in": 3600,
  "token_type": "Bearer",
  "refresh_token": "def502..."
}

# Step 2: Use token
GET /api/resource
Headers:
  Authorization: Bearer eyJ...
```

#### Documentation Clues
- "OAuth 2.0 client credentials flow"
- "Obtain an access token"
- "Token expires after X hours"
- "Client ID and Secret required"
- "Refresh your token"

#### Planning Notes
- Complex implementation required
- Token refresh logic needed
- Multiple credential types (client_id, client_secret)
- Token lifecycle management
- Add `CreateAccessToken` flow to implementation

#### Examples
**PayPal**:
```bash
# Get token
POST /v1/oauth2/token
Authorization: Basic base64(client_id:client_secret)
Body: grant_type=client_credentials

# Use token
POST /v2/checkout/orders
Authorization: Bearer access_token
```

**Adyen** (for some APIs):
```bash
# Get token
POST /hpp/authentication/v1/generateToken.json
Body:
  merchantAccount: your_account
  auth: {
    "userName": "username",
    "password": "password"
  }

# Use token
POST /payment-initiation/v3/payments
Authorization: Bearer token
```

---

### 3. Signature
**Definition**: Request signing with HMAC or similar algorithm
**UCS Mapping**: `ConnectorAuthType::Signature`
**Complexity**: Very High

#### Identification Signals
- Custom signing algorithm
- Secret key required
- Request body or headers signed
- Timestamp in signature
- Hash or signature in headers
- Documentation has "Sign requests" section

#### Signature Patterns
```bash
# Pattern 1: HMAC in header
POST /api/endpoint
Headers:
  X-Signature: sha256=base64(hmac_sha256(secret, request_body))
  X-Timestamp: 1704067200

# Pattern 2: Authorization header
POST /api/endpoint
Headers:
  Authorization: AWS4-HMAC-SHA256 Credential=..., SignedHeaders=..., Signature=...

# Pattern 3: Query parameter
GET /api/resource?signature=base64(hmac_sha256(secret, query_string))
```

#### Documentation Clues
- "Sign all requests with your secret key"
- "Include timestamp in signature"
- "Generate HMAC-SHA256 signature"
- "Calculate signature as..."
- "Verify request authenticity"

#### Planning Notes
- Very complex implementation
- Custom signing logic required
- Secret key management
- Timestamp handling
- May need to sign request body, headers, or query params

#### Examples
**PayPal (Classic API)**:
```bash
# Signature calculated from request
POST /v1/AdaptivePayments/Pay
Headers:
  X-PAYPAL-SECURITY-USERID: user
  X-PAYPAL-SECURITY-PASSWORD: pass
  X-PAYPAL-SECURITY-SIGNATURE: signature
  X-PAYPAL-REQUEST-DATA-FORMAT: JSON
  X-PAYPAL-RESPONSE-DATA-FORMAT: JSON
Body:
  {
    "actionType": "PAY",
    "signature": "calculated_signature"
  }
```

**Amazon Pay**:
```bash
POST /v1/payments
Headers:
  Authorization: AWS4-HMAC-SHA256 Credential=access_key/date/region/service/aws4_request, SignedHeaders=..., Signature=...
```

---

### 4. MultiHeaderKey
**Definition**: Multiple header fields required for authentication
**UCS Mapping**: `ConnectorAuthType::MultiHeaderKey`
**Complexity**: Medium

#### Identification Signals
- API Key + API Secret
- API Key + Merchant ID
- Multiple credential fields required
- Each field in separate header
- No OAuth flow

#### Header Patterns
```bash
# Pattern 1: Key + Secret
Headers:
  x-api-key: your_key
  x-api-secret: your_secret

# Pattern 2: Key + Merchant ID
Headers:
  x-api-key: your_key
  x-merchant-id: merchant_123

# Pattern 3: Key + Secret + Other
Headers:
  api-key: key
  api-secret: secret
  x-version: v1
```

#### Documentation Clues
- "Include both API key and API secret"
- "Provide your merchant ID"
- "All three headers are required"
- "Multiple headers must be present"

#### Planning Notes
- Multiple credential fields
- Complex header structure
- Validate all required headers
- May include version or other metadata

#### Examples
**First Data**:
```bash
POST /transactions/payments
Headers:
  Content-Type: application/json
  x-gge4-api-key: your_api_key
  x-gge4-date: timestamp
  x-gge4-hmac: signature
```

**CyberSource**:
```bash
POST /ec/v1/payments
Headers:
  Content-Type: application/json
  Authorization: Basic base64(merchant_id:transaction_key)
  x-merchant-id: merchant_123
```

---

## Authentication Flow Planning

### Determine Auth Type Checklist

**Step 1: Check Credentials Required**
- [ ] Single API key only? → HeaderKey
- [ ] Client ID + Client Secret? → Likely CreateAccessToken
- [ ] API Key + API Secret? → MultiHeaderKey or Signature
- [ ] Secret key for signing? → Signature

**Step 2: Check Documentation Structure**
- [ ] Separate "Authentication" or "OAuth" section? → CreateAccessToken
- [ ] "API Keys" section only? → HeaderKey
- [ ] "Signing Requests" section? → Signature
- [ ] Multiple credential fields? → MultiHeaderKey

**Step 3: Examine Request Examples**
```bash
# HeaderKey Example
curl https://api.example.com/payment \
  -H "x-api-key: sk_test_..."  # ← Single header with key

# CreateAccessToken Example
curl https://api.example.com/payment \
  -H "Authorization: Bearer eyJ..."  # ← Bearer token (obtained separately)

# Signature Example
curl https://api.example.com/payment \
  -H "X-Signature: sha256=abc..."  # ← Custom signature
  -H "X-Timestamp: 123456"  # ← Timestamp
```

**Step 4: Look for Token Endpoint**
- [ ] `/oauth/token` or `/auth/token`? → CreateAccessToken
- [ ] No token endpoint? → HeaderKey or Signature
- [ ] Token expires and refreshes? → CreateAccessToken

### OAuth vs Simple Token

**Simple Token** (HeaderKey):
```bash
# Key in dashboard = Static token
GET /api/resource
Authorization: Bearer static_key_from_dashboard
```

**OAuth Token** (CreateAccessToken):
```bash
# 1. Exchange credentials for token
POST /oauth/token
client_id=abc
client_secret=xyz

# 2. Get temporary token
{
  "access_token": "eyJ...",
  "expires_in": 3600
}

# 3. Use token (expires soon)
GET /api/resource
Authorization: Bearer eyJ...
```

### Edge Cases

#### PayPal Dual Auth
PayPal supports both:
1. **Simple token** (older API): Static token from dashboard
2. **OAuth** (newer API): Client credentials flow

**Planning**: Check which API version is documented.

#### Signature with Key
Some connectors use both API key and signature:
```bash
Headers:
  x-api-key: key       # Simple identification
  x-signature: sig     # Cryptographic signature
```
**Planning**: This is likely Signature type (signature is primary auth).

#### Basic Auth
Some use HTTP Basic Authentication:
```bash
Authorization: Basic base64(username:password)
```
**Planning**: This is typically HeaderKey (username/password treated as API credentials).

## In Implementation Plan

```markdown
## 1. Architecture Choices
- **Auth Type**: CreateAccessToken
  - Pattern: OAuth client credentials flow
  - Token Endpoint: POST /v1/oauth2/token
  - Token Format: Bearer {access_token}
  - Refresh: Yes (refresh_token provided)
  - Credentials Required:
    - client_id: From PayPal dashboard
    - client_secret: From PayPal dashboard
  - Token Expiry: 9 hours (expires_in field)

  Evidence:
  - Documentation has "OAuth 2.0" section
  - Separate token endpoint with grant_type
  - access_token expires in 3600 seconds
  - refresh_token provided for renewal
```

## Common Planning Questions

### Q: "API has token endpoint but also accepts static key"
A: Check documentation - may support both. Prefer OAuth if documented as primary method.

### Q: "API requires API key + secret but calls it 'signature'"
A: If just concatenation (not cryptographic signing) → MultiHeaderKey. If actual HMAC/signature → Signature.

### Q: "Documentation shows 'Authorization: Bearer' but no OAuth section"
A: Check if Bearer token is static (HeaderKey) or temporary (CreateAccessToken).

### Q: "Multiple auth methods shown (Basic, API Key, OAuth)"
A: Verify which is for Payments API vs other APIs. Payments may have specific method.

## Credential Management

### HeaderKey
- Single credential: API key
- Storage: Environment variable or config
- Rotation: Manual key regeneration

### CreateAccessToken
- Two credentials: Client ID, Client Secret
- Storage: Secure vault for secrets
- Rotation: Client secret rotation + token refresh
- Automation: Token refresh logic

### Signature
- Single credential: Secret key
- Storage: Secure vault (highest security)
- Rotation: Key regeneration
- Automation: Request signing logic

### MultiHeaderKey
- Multiple credentials: API key, secret, merchant ID
- Storage: Secure vault
- Rotation: Each credential independently
- Validation: All headers required