# Error Handling Patterns Reference

Best practices and anti-patterns for error handling across different programming languages.

## Anti-Patterns (Things to Detect)

### 1. Empty Catch Blocks

**TypeScript/JavaScript**:
```typescript
// WARNING - Silent failure
try {
  await saveData();
} catch (e) {
  // Empty - errors silently swallowed
}

// WARNING - Just logging
try {
  await saveData();
} catch (e) {
  console.log(e);  // Logged but not handled
}

// GOOD - Proper handling
try {
  await saveData();
} catch (e) {
  logger.error('Failed to save data', { error: e });
  throw new DatabaseError('Save failed', { cause: e });
}
```

**Python**:
```python
# WARNING - Bare except
try:
    save_data()
except:
    pass

# WARNING - Exception with pass
try:
    save_data()
except Exception:
    pass

# GOOD - Proper handling
try:
    save_data()
except DatabaseError as e:
    logger.error('Failed to save', exc_info=True)
    raise ApplicationError('Save failed') from e
```

**Java**:
```java
// WARNING - Empty catch
try {
    saveData();
} catch (Exception e) {
    // Empty
}

// GOOD
try {
    saveData();
} catch (DatabaseException e) {
    logger.error("Failed to save", e);
    throw new ApplicationException("Save failed", e);
}
```

### 2. Swallowed Exceptions

**TypeScript/JavaScript**:
```typescript
// WARNING - Exception caught but not propagated
async function processOrder(order) {
  try {
    await validateOrder(order);
    await chargePayment(order);
    await fulfillOrder(order);
  } catch (e) {
    logger.error('Order failed', e);
    // Missing: throw or return error
  }
  return { success: true };  // Lies! Could have failed
}

// GOOD
async function processOrder(order) {
  try {
    await validateOrder(order);
    await chargePayment(order);
    await fulfillOrder(order);
    return { success: true };
  } catch (e) {
    logger.error('Order failed', e);
    return { success: false, error: e.message };
  }
}
```

### 3. Generic Error Messages

**TypeScript/JavaScript**:
```typescript
// WARNING - Unhelpful error
throw new Error('Something went wrong');
throw new Error('Error');

// GOOD - Specific and actionable
throw new ValidationError('Email format invalid', { field: 'email', value: email });
throw new DatabaseError('User not found', { userId, table: 'users' });
```

### 4. Missing Error Context

**TypeScript/JavaScript**:
```typescript
// WARNING - No context
catch (e) {
  throw e;  // Lost context of where/why
}

// GOOD - Preserving context
catch (e) {
  throw new ServiceError('Payment processing failed', {
    cause: e,
    orderId,
    amount
  });
}
```

**Python**:
```python
# WARNING - Re-raising without context
except Exception as e:
    raise e

# GOOD - Chaining exceptions
except DatabaseError as e:
    raise ApplicationError('Database operation failed') from e
```

### 5. Panic Without Context (Rust)

```rust
// WARNING - Unhelpful panic
let value = result.unwrap();
let value = result.expect("error");

// BETTER - Contextful expect
let value = result.expect("Failed to parse config file");

// GOOD - Proper error propagation
let value = result.context("Failed to parse config")?;

// BEST - Custom error types
let value = result.map_err(|e| ConfigError::ParseFailed {
    path: config_path,
    source: e
})?;
```

### 6. Ignoring Errors (Go)

```go
// WARNING - Ignored error
result, _ := doSomething()

// WARNING - Error not checked
result, err := doSomething()
useResult(result)  // err not checked!

// GOOD
result, err := doSomething()
if err != nil {
    return fmt.Errorf("doSomething failed: %w", err)
}
useResult(result)
```

## Best Practices

### 1. Error Propagation

**TypeScript/JavaScript**:
```typescript
// Use error cause for chaining
catch (e) {
  throw new CustomError('Operation failed', { cause: e });
}

// Or wrap errors
catch (e) {
  throw new WrappedError('Context message', e);
}
```

**Python**:
```python
# Use raise from for chaining
except LowLevelError as e:
    raise HighLevelError('Operation failed') from e
```

**Rust**:
```rust
// Use ? operator with context
use anyhow::Context;
let data = read_file(path)
    .context("Failed to read configuration")?;
```

### 2. Specific Exception Types

```typescript
// Define custom errors
class ValidationError extends Error {
  constructor(message: string, public field: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

class DatabaseError extends Error {
  constructor(message: string, public query: string) {
    super(message);
    this.name = 'DatabaseError';
  }
}

// Use specific catches
try {
  await processUser(data);
} catch (e) {
  if (e instanceof ValidationError) {
    return res.status(400).json({ error: e.message, field: e.field });
  }
  if (e instanceof DatabaseError) {
    logger.error('DB error', { query: e.query });
    return res.status(500).json({ error: 'Database error' });
  }
  throw e;  // Re-throw unknown errors
}
```

### 3. Graceful Degradation

```typescript
// GOOD - Fallback behavior
async function getUserAvatar(userId: string): Promise<string> {
  try {
    return await fetchAvatar(userId);
  } catch (e) {
    logger.warn('Failed to fetch avatar, using default', { userId, error: e });
    return DEFAULT_AVATAR_URL;
  }
}

// GOOD - Retry with backoff
async function fetchWithRetry<T>(fn: () => Promise<T>, retries = 3): Promise<T> {
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (e) {
      if (i === retries - 1) throw e;
      await delay(Math.pow(2, i) * 1000);
    }
  }
  throw new Error('Unreachable');
}
```

### 4. Meaningful Error Messages

```typescript
// Template for good error messages
throw new Error([
  'Failed to process payment',           // What failed
  `Order: ${orderId}`,                   // Context
  `Amount: ${amount}`,                   // Relevant data
  `Reason: ${e.message}`,                // Why it failed
].join(' | '));

// Or structured errors
throw new PaymentError({
  message: 'Payment processing failed',
  code: 'PAYMENT_DECLINED',
  orderId,
  amount,
  reason: e.message,
  retryable: true,
});
```

## Detection Patterns

### Grep Commands

```bash
# Empty catch blocks
grep -rn "catch.*{[\s]*}" --include="*.ts" --include="*.js"
grep -rn "except.*:[\s]*pass" --include="*.py"

# Bare except (Python)
grep -rn "except:" --include="*.py"

# Ignored errors (Go)
grep -rn ", _ :=" --include="*.go"

# Unwrap without context (Rust)
grep -rn "\.unwrap()" --include="*.rs"
grep -rn "\.expect(\"" --include="*.rs"

# Generic error messages
grep -rn "throw new Error\(['\"]Error" --include="*.ts"
grep -rn "raise Exception\(" --include="*.py"
```

### ESLint Rules

```json
{
  "rules": {
    "no-empty": ["error", { "allowEmptyCatch": false }],
    "no-unused-vars": ["error", { "caughtErrors": "all" }]
  }
}
```

### Clippy (Rust)

```bash
cargo clippy -- -W clippy::unwrap_used -W clippy::expect_used
```

## Severity Classification

| Issue | Severity | Description |
|-------|----------|-------------|
| Empty catch block | WARNING | Errors silently swallowed |
| Bare except (Python) | WARNING | Catches system exceptions |
| Ignored error (Go `_`) | WARNING | Error not handled |
| `unwrap()` without context | WARNING | Panic without helpful message |
| Generic error message | SUGGESTION | Not actionable |
| Missing error logging | SUGGESTION | Hard to debug |
| Not re-throwing after log | WARNING | Caller unaware of failure |

## Language-Specific Notes

### TypeScript/JavaScript
- Use `Error.cause` (ES2022+) for error chaining
- Consider using `neverthrow` for Result types
- Always use `async/await` with try/catch

### Python
- Always use `raise ... from e` for chaining
- Define custom exception hierarchy
- Use `logging.exception()` to include stack trace

### Rust
- Prefer `?` operator over `unwrap()`
- Use `anyhow` for application code
- Use `thiserror` for library code
- Add context with `.context()` or `.with_context()`

### Go
- Always check returned errors
- Use `fmt.Errorf("context: %w", err)` for wrapping
- Consider using `pkg/errors` for stack traces
