# Amount Converter Reference

## Overview

Guide for selecting the correct amount converter based on connector API specifications.

## Available Converters

### 1. StringMinorUnitConverter
**Purpose**: Handle amounts as strings in minor currency units (cents, pence, etc.)
**Input**: String without decimal point
**Examples**:
- Input: `"1000"` → Output: `MinorUnit(1000)` → Represents: $10.00
- Input: `"5000"` → Output: `MinorUnit(5000)` → Represents: $50.00
- Input: `"100"` → Output: `MinorUnit(100)` → Represents: $1.00

**When to Use**:
- API shows amounts without decimal points
- Amounts represented as integers in strings
- Documentation says "amounts in cents"
- Field names like `amount_cents`
- Historical/legacy APIs

**Connector Examples**:
```json
{
  "amount": "1000",
  "currency": "USD"
}

{
  "amount_cents": 1000,
  "currency": "USD"
}
```

**Planning Decision Tree**:
1. Check API examples - are decimals shown? NO → MinorUnit
2. Is field named `amount_cents` or similar? YES → MinorUnit
3. Documentation says "pass amounts in cents"? YES → MinorUnit
4. Amount shown as `"100"` (string, no decimal)? YES → MinorUnit

### 2. StringMajorUnitConverter
**Purpose**: Handle amounts as strings with decimal point
**Input**: String with decimal point
**Examples**:
- Input: `"10.00"` → Output: `MajorUnit("10.00")` → Represents: $10.00
- Input: `"10.50"` → Output: `MajorUnit("10.50")` → Represents: $10.50
- Input: `"0.99"` → Output: `MajorUnit("0.99")` → Represents: $0.99

**When to Use**:
- API shows amounts with decimal points in strings
- Always includes decimal places (even .00)
- String type (not number)
- Modern APIs with decimal support
- Multi-currency support with varying decimals

**Connector Examples**:
```json
{
  "amount": "10.00",
  "currency": "USD"
}

{
  "amount": "10.5",
  "currency": "EUR"
}
```

**Planning Decision Tree**:
1. Check API examples - are decimals shown? YES → Continue
2. Is it a string type? YES → StringMajorUnit
3. Always has decimal places? YES → StringMajorUnit
4. Field type specified as "string"? YES → StringMajorUnit

### 3. FloatMajorUnitConverter
**Purpose**: Handle amounts as floating point numbers
**Input**: Number with or without decimal point
**Examples**:
- Input: `10.00` → Output: `MajorUnit("10.00")` → Represents: $10.00
- Input: `10.5` → Output: `MajorUnit("10.5")` → Represents: $10.50
- Input: `10` → Output: `MajorUnit("10")` → Represents: $10.00

**When to Use**:
- API shows amounts as numbers (not strings)
- JavaScript/TypeScript APIs
- Float/double type in spec
- Modern REST APIs
- Careful: May lose precision with very large amounts

**Connector Examples**:
```json
{
  "amount": 10.00,
  "currency": "USD"
}

{
  "amount": 10.5,
  "currency": "EUR"
}
```

**Planning Decision Tree**:
1. Check API examples - are decimals shown? YES → Continue
2. Is it a number type (not quoted)? YES → FloatMajorUnit
3. No quotes around value? YES → FloatMajorUnit
4. Field type is "number" or "float"? YES → FloatMajorUnit

## Decision Framework

### Step 1: Examine API Examples
Look at actual request/response examples in documentation:

```bash
# Example 1
"amount": "1000"  # String, no decimal

# Example 2
"amount": "10.00"  # String, with decimal

# Example 3
"amount": 10.00    # Number, with decimal
```

### Step 2: Check Field Types
Look for type specifications in documentation:

```yaml
amount:
  type: string
  description: Amount in cents

amount:
  type: string
  description: Amount in major units

amount:
  type: number
  description: Amount in USD
```

### Step 3: Consider Documentation Notes
Look for explanatory text:

- "Pass amounts in cents" → MinorUnit
- "Use major currency units" → StringMajorUnit
- "Amount is a float" → FloatMajorUnit
- "No decimals in amount field" → MinorUnit
- "Always include two decimal places" → StringMajorUnit

### Step 4: Validate Edge Cases
Test your decision with edge cases:

**For MinorUnit**:
- Zero: `"0"` ✓
- Large amounts: `"100000000"` ✓
- No decimals possible ✓

**For StringMajorUnit**:
- Zero: `"0.00"` ✓
- Precise decimals: `"10.50"` ✓
- Varying precision: `"10.5"` and `"10.55"` ✓

**For FloatMajorUnit**:
- Zero: `0` ✓
- Floating point: `10.5` ✓
- May lose precision: Very large numbers

## Common Connector Patterns

### Stripe
**Format**: StringMinorUnit
**Evidence**:
```bash
curl https://api.stripe.com/v1/payment_intents \
  -u sk_test_EXAMPLE: \
  -d amount=2000  # Amount in cents
```
**Decision**: StringMinorUnit (amount in cents)

### PayPal
**Format**: StringMajorUnit
**Evidence**:
```json
{
  "purchase_units": [{
    "amount": {
      "currency_code": "USD",
      "value": "10.00"  # String with decimal
    }
  }]
}
```
**Decision**: StringMajorUnit (value is string with decimal)

### Adyen
**Format**: IntegerMinorUnit
**Evidence**:
```json
{
  "amount": {
    "currency": "EUR",
    "value": 1000  # Integer, no decimal
  }
}
```
**Decision**: StringMinorUnit (integer = minor units, convert to string)

### Braintree
**Format**: StringMajorUnit
**Evidence**:
```json
{
  "amount": "10.00"  # String with decimal
}
```
**Decision**: StringMajorUnit

### Square
**Format**: IntegerMinorUnit
**Evidence**:
```json
{
  "amount_money": {
    "amount": 1000,  # Integer in cents
    "currency": "USD"
  }
}
```
**Decision**: StringMinorUnit (amount in cents)

## Amount Converter Configuration

### In Implementation Plan
```markdown
## Architecture Choices
- **Amount Converter**: StringMinorUnit
  - Decision: API shows amounts as "1000" (string without decimals)
  - Evidence: Documentation states "amounts in cents"
  - Examples:
    - $10.00 → "1000"
    - $0.99 → "99"
  - UCS Type: StringMinorUnitConverter
```

### In Code Generation
The implementation agent will use this in `create_all_prerequisites!`:

```rust
macros::create_all_prerequisites!(
    connector_name: ConnectorName,
    api: [
        (flow: Authorize, ...),
    ],
    amount_converters: [
        amount_converter: StringMinorUnit  // ← From implementation plan
    ],
);
```

## Testing Your Decision

### Validate with Multiple Examples
Request examples should all follow the same pattern:

**StringMinorUnit**:
```json
// Small amount
"amount": "100"   // = $1.00

// Large amount
"amount": "100000"  // = $1000.00

// Zero
"amount": "0"
```

**StringMajorUnit**:
```json
// Small amount
"amount": "1.00"

// Large amount
"amount": "1000.00"

// Zero
"amount": "0.00"
```

**FloatMajorUnit**:
```json
// Small amount
"amount": 1.00

// Large amount
"amount": 1000.00

// Zero
"amount": 0
```

### Check Consistency
- Are ALL examples consistent with your decision?
- Do any examples contradict the pattern?
- Is the documentation clear about the format?

## Common Mistakes to Avoid

❌ **Assuming decimals mean MinorUnit**
- Decimals in API can be StringMajorUnit or FloatMajorUnit
- Check if string or number

❌ **Ignoring documentation type specs**
- Type specification is authoritative
- Don't guess based on examples alone

❌ **Mixing converter types**
- Choose ONE converter for entire connector
- Don't use different converters for different flows

❌ **Not validating edge cases**
- Test zero, negative (if allowed), and large amounts
- Ensure converter handles all valid values

❌ **Confusing integer and string**
- `"100"` (string) vs `100` (number) → different converters
- StringMinorUnit vs StringMajorUnit based on decimal presence

## Planning Checklist

- [ ] Examined multiple API examples
- [ ] Checked type specifications in docs
- [ ] Read documentation notes about amount format
- [ ] Validated decision with edge cases
- [ ] Confirmed consistency across all flows
- [ ] Documented decision in implementation plan
- [ ] Specified exact converter type (not just "minor" or "major")
- [ ] Provided evidence/examples supporting decision

## When to Ask for User Confirmation

Ask the user if:
- API examples are contradictory
- Documentation is unclear
- Multiple converter types seem valid
- Edge cases don't work with your decision
- Connector has unusual amount handling

**Example Question**:
"The API shows 'amount': '1000' in some places and 'amount': '10.00' in others. Both are strings but different formats. Should I use StringMinorUnit (interpreting '1000' as $10.00) or StringMajorUnit (interpreting '10.00' as $10.00)?"