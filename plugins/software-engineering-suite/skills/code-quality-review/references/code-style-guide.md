# Code Style Guide Reference

Language-agnostic style guidelines for detecting code quality issues.

## Naming Conventions

### General Rules

| Element | Convention | Example |
|---------|------------|---------|
| Classes/Types | PascalCase | `UserService`, `HttpClient` |
| Functions/Methods | camelCase or snake_case | `getUserById`, `get_user_by_id` |
| Variables | camelCase or snake_case | `userName`, `user_name` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_RETRIES`, `API_BASE_URL` |
| Private members | underscore prefix (optional) | `_privateMethod`, `_internalState` |

### Anti-Patterns

```typescript
// SUGGESTION - Inconsistent naming
const user_name = 'John';
const userAge = 25;
const UserEmail = 'john@example.com';  // Mixed conventions

// GOOD - Consistent
const userName = 'John';
const userAge = 25;
const userEmail = 'john@example.com';
```

```python
# SUGGESTION - PascalCase for variables
UserName = 'John'  # Should be user_name

# SUGGESTION - camelCase in Python
userName = 'John'  # Should be user_name

# GOOD
user_name = 'John'
```

### Meaningful Names

```typescript
// SUGGESTION - Unclear names
const d = new Date();  // What date?
const arr = getUsers();  // What kind of array?
const temp = calculate();  // Temporary what?

// GOOD - Self-documenting
const createdAt = new Date();
const activeUsers = getUsers();
const discountedPrice = calculate();
```

## Dead Code

### Unreachable Code

```typescript
// SUGGESTION - Code after return
function process() {
  return result;
  console.log('This never runs');  // Dead code
}

// SUGGESTION - Always-false condition
if (false) {
  doSomething();  // Never executes
}

// SUGGESTION - Commented-out code
function handler() {
  // const oldImplementation = ...
  // if (oldCondition) { ... }
  return newImplementation();
}
```

### Unused Variables

```typescript
// SUGGESTION - Declared but never used
const unusedConfig = loadConfig();
// unusedConfig never referenced

// SUGGESTION - Unused function parameters
function process(data, options, callback) {
  // callback never used
  return transform(data, options);
}

// GOOD - Use underscore for intentionally unused
function process(data, options, _callback) {
  return transform(data, options);
}
```

### Unused Imports

```typescript
// SUGGESTION - Imported but never used
import { useState, useEffect, useCallback } from 'react';

function Component() {
  const [state, setState] = useState(0);
  // useEffect and useCallback never used
  return <div>{state}</div>;
}
```

## Code Complexity

### Long Functions

```typescript
// SUGGESTION - Function > 50 lines
function processOrder(order) {
  // Line 1
  // ...
  // Line 75
  // Too long, hard to understand and test
}

// GOOD - Break into smaller functions
function processOrder(order) {
  validateOrder(order);
  const payment = processPayment(order);
  const fulfillment = createFulfillment(order, payment);
  notifyCustomer(order, fulfillment);
  return { payment, fulfillment };
}
```

### Deep Nesting

```typescript
// SUGGESTION - > 3 levels of nesting
function process(data) {
  if (data) {
    if (data.items) {
      for (const item of data.items) {
        if (item.active) {
          if (item.price > 0) {
            // Hard to follow
          }
        }
      }
    }
  }
}

// GOOD - Early returns and extraction
function process(data) {
  if (!data?.items) return;

  const activeItems = data.items.filter(item => item.active && item.price > 0);
  activeItems.forEach(processItem);
}
```

### Cyclomatic Complexity

```typescript
// SUGGESTION - High cyclomatic complexity
function getDiscount(user, order, promo) {
  if (user.isPremium) {
    if (order.total > 100) {
      if (promo === 'SUMMER') {
        return 0.3;
      } else if (promo === 'WINTER') {
        return 0.25;
      }
      return 0.2;
    }
    return 0.1;
  } else if (order.total > 200) {
    if (promo) {
      return 0.15;
    }
    return 0.1;
  }
  return 0;
}

// GOOD - Table-driven or strategy pattern
const discountRules = [
  { condition: (u, o, p) => u.isPremium && o.total > 100 && p === 'SUMMER', discount: 0.3 },
  { condition: (u, o, p) => u.isPremium && o.total > 100 && p === 'WINTER', discount: 0.25 },
  { condition: (u, o) => u.isPremium && o.total > 100, discount: 0.2 },
  { condition: (u) => u.isPremium, discount: 0.1 },
  { condition: (u, o, p) => o.total > 200 && p, discount: 0.15 },
  { condition: (u, o) => o.total > 200, discount: 0.1 },
];

function getDiscount(user, order, promo) {
  const rule = discountRules.find(r => r.condition(user, order, promo));
  return rule?.discount ?? 0;
}
```

## Magic Numbers/Strings

```typescript
// SUGGESTION - Magic numbers
if (response.status === 200) { ... }
if (retries > 3) { ... }
const timeout = 5000;

// GOOD - Named constants
const HTTP_OK = 200;
const MAX_RETRIES = 3;
const DEFAULT_TIMEOUT_MS = 5000;

if (response.status === HTTP_OK) { ... }
if (retries > MAX_RETRIES) { ... }
const timeout = DEFAULT_TIMEOUT_MS;
```

```typescript
// SUGGESTION - Magic strings
if (user.role === 'admin') { ... }
if (status === 'pending') { ... }

// GOOD - Enums or constants
enum UserRole {
  Admin = 'admin',
  User = 'user',
}

enum OrderStatus {
  Pending = 'pending',
  Completed = 'completed',
}

if (user.role === UserRole.Admin) { ... }
if (status === OrderStatus.Pending) { ... }
```

## Documentation

### Missing Documentation

```typescript
// SUGGESTION - Public API without docs
export function calculateTax(amount, rate, jurisdiction) {
  // Complex calculation without explanation
}

// GOOD - Documented public API
/**
 * Calculates tax amount based on jurisdiction rules.
 *
 * @param amount - Base amount in cents
 * @param rate - Tax rate as decimal (e.g., 0.08 for 8%)
 * @param jurisdiction - Two-letter state code
 * @returns Tax amount in cents
 * @throws {InvalidJurisdictionError} If jurisdiction is not supported
 *
 * @example
 * calculateTax(10000, 0.08, 'CA') // Returns 800
 */
export function calculateTax(
  amount: number,
  rate: number,
  jurisdiction: string
): number {
  // Implementation
}
```

### Outdated Comments

```typescript
// SUGGESTION - Comment doesn't match code
// Increment counter by 1
counter += 2;  // Actually adds 2

// SUGGESTION - TODO without context
// TODO: fix this
const result = hackyWorkaround();

// GOOD - Actionable TODO
// TODO(ticket-123): Replace with proper implementation after API v2 launch
const result = temporaryWorkaround();
```

## Code Duplication

```typescript
// SUGGESTION - Duplicated logic
function processUserOrder(user, order) {
  if (!user.email || !user.email.includes('@')) {
    throw new Error('Invalid email');
  }
  // Process order...
}

function sendNotification(user, message) {
  if (!user.email || !user.email.includes('@')) {
    throw new Error('Invalid email');
  }
  // Send notification...
}

// GOOD - Extracted validation
function validateEmail(email: string): void {
  if (!email || !email.includes('@')) {
    throw new ValidationError('Invalid email format');
  }
}

function processUserOrder(user, order) {
  validateEmail(user.email);
  // Process order...
}

function sendNotification(user, message) {
  validateEmail(user.email);
  // Send notification...
}
```

## Detection Patterns

### Grep Commands

```bash
# Unused imports (rough detection)
grep -rn "^import" --include="*.ts" | while read line; do
  # Check if imported names are used in file
done

# TODO/FIXME comments
grep -rn "TODO\|FIXME\|HACK\|XXX" --include="*.ts" --include="*.py"

# Magic numbers
grep -rn "=== [0-9]\{3,\}" --include="*.ts"  # 3+ digit numbers

# Commented code (rough)
grep -rn "^[\s]*//.*function\|^[\s]*//.*const\|^[\s]*//.*if" --include="*.ts"
```

### ESLint Rules

```json
{
  "rules": {
    "no-unused-vars": "error",
    "no-unreachable": "error",
    "no-magic-numbers": ["warn", { "ignore": [0, 1, -1] }],
    "complexity": ["warn", 10],
    "max-depth": ["warn", 3],
    "max-lines-per-function": ["warn", 50]
  }
}
```

### Pylint

```bash
pylint --disable=all --enable=W0611,W0612,W0613 .
# W0611: unused-import
# W0612: unused-variable
# W0613: unused-argument
```

## Severity Classification

| Issue | Severity | Description |
|-------|----------|-------------|
| Unused imports | SUGGESTION | Clutter, slight perf impact |
| Unused variables | SUGGESTION | Confusion, potential bug |
| Dead code | SUGGESTION | Maintenance burden |
| Long functions (>50 lines) | SUGGESTION | Hard to test/understand |
| Deep nesting (>3 levels) | SUGGESTION | Hard to follow |
| Magic numbers | SUGGESTION | Unclear meaning |
| Missing docs (public API) | SUGGESTION | Poor discoverability |
| Inconsistent naming | SUGGESTION | Readability |
| Code duplication | SUGGESTION | Maintenance burden |
| Outdated comments | WARNING | Misleading |
| High complexity | WARNING | Bug-prone |
