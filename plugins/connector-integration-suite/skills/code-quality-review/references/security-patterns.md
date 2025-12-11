# Security Patterns Reference

**Version**: 1.0.0
**Purpose**: Security validation rules and vulnerability detection patterns

---

## OWASP Top 10 Checks

### 1. Injection Attacks

#### SQL Injection

**Vulnerable** (❌):
```rust
// Direct string concatenation
let query = format!("SELECT * FROM users WHERE id = '{}'", user_id);
db.execute(&query);  // VULNERABLE
```

**Safe** (✅):
```rust
// Parameterized queries
let query = "SELECT * FROM users WHERE id = ?";
db.execute(query, &[user_id]);  // SAFE
```

**Detection**:
```bash
# Look for string formatting in SQL contexts
grep -n "format!.*SELECT\|INSERT\|UPDATE\|DELETE" src/**/*.rs
```

---

#### Command Injection

**Vulnerable** (❌):
```rust
use std::process::Command;

// User input in command
let output = Command::new("sh")
    .arg("-c")
    .arg(format!("curl {}", user_url))  // VULNERABLE
    .output();
```

**Safe** (✅):
```rust
// Validate and sanitize input
fn is_valid_url(url: &str) -> bool {
    url.starts_with("https://") && !url.contains(';')
}

if is_valid_url(&user_url) {
    Command::new("curl").arg(&user_url).output();  // SAFE
}
```

**Detection**:
```bash
# Look for Command with format! or user input
grep -n "Command::new.*format!" src/**/*.rs
```

---

### 2. Authentication & Session Management

#### Hardcoded Credentials

**Vulnerable** (❌):
```rust
const API_KEY: &str = "sk_live_abc123";  // VULNERABLE
const DATABASE_PASSWORD: &str = "password123";  // VULNERABLE

fn connect() {
    let client = Client::new("https://api.example.com", API_KEY);
}
```

**Safe** (✅):
```rust
// Load from environment or secure config
fn get_api_key() -> Result<String, Error> {
    std::env::var("API_KEY").map_err(|_| Error::MissingApiKey)
}

// Or from auth_type (for connectors)
let api_key = match &router_data.connector_auth_type {
    ConnectorAuthType::HeaderKey { api_key } => api_key,
    _ => return Err(Error::InvalidAuthType),
};
```

**Detection**:
```bash
# Look for hardcoded secrets
grep -niE "(password|secret|api_key|token).*=.*[\"']" src/**/*.rs | grep -v "env::var"
```

---

#### Weak Authentication

**Vulnerable** (❌):
```rust
// No password hashing
fn create_user(password: &str) {
    db.insert("users", &User {
        password: password.to_string(),  // VULNERABLE - plaintext
    });
}
```

**Safe** (✅):
```rust
use argon2::{Argon2, PasswordHasher};

fn create_user(password: &str) -> Result<(), Error> {
    let salt = generate_salt();
    let hash = Argon2::default()
        .hash_password(password.as_bytes(), &salt)?
        .to_string();

    db.insert("users", &User { password_hash: hash });
    Ok(())
}
```

---

### 3. Sensitive Data Exposure

#### Logging Sensitive Information

**Vulnerable** (❌):
```rust
// Logging PII or credentials
logger::info!("Processing payment for card: {}", card_number);  // VULNERABLE
logger::debug!("API Key: {}", api_key);  // VULNERABLE
```

**Safe** (✅):
```rust
// Redact sensitive data
logger::info!("Processing payment for card: {}****", &card_number[..4]);
logger::debug!("API Key: [REDACTED]");

// Or use structured logging with redaction
#[derive(Debug)]
struct SafePayment {
    #[log(skip)]  // Don't log this field
    card_number: String,
    amount: MinorUnit,
}
```

**Detection**:
```bash
# Look for logging with sensitive field names
grep -niE "log.*card|credit|cvv|password|secret|key" src/**/*.rs
```

---

#### Exposing Errors

**Vulnerable** (❌):
```rust
// Detailed error to client
Err(format!("Database connection failed: {}, host: {}, user: {}",
    error, db_host, db_user))  // VULNERABLE - leaks internal info
```

**Safe** (✅):
```rust
// Generic error to client, detailed log internally
logger::error!("DB connection failed: {} (host: {}, user: {})",
    error, db_host, db_user);

Err("Internal server error".to_string())  // SAFE - generic message
```

---

### 4. XML External Entities (XXE)

#### Unsafe XML Parsing

**Vulnerable** (❌):
```rust
// Default XML parser (may allow external entities)
let doc = Document::parse(xml_str);  // Potentially VULNERABLE
```

**Safe** (✅):
```rust
use roxmltree::ParsingOptions;

let options = ParsingOptions {
    allow_dtd: false,  // Disable DTD processing
    ..Default::default()
};
let doc = Document::parse_with_options(xml_str, options);
```

---

### 5. Broken Access Control

#### Missing Authorization Checks

**Vulnerable** (❌):
```rust
// No permission check
fn delete_user(user_id: &str) {
    db.delete("users", user_id);  // VULNERABLE - anyone can delete
}
```

**Safe** (✅):
```rust
fn delete_user(user_id: &str, requester: &User) -> Result<(), Error> {
    // Check authorization
    if !requester.is_admin() && requester.id != user_id {
        return Err(Error::Unauthorized);
    }

    db.delete("users", user_id)
}
```

---

### 6. Security Misconfiguration

#### Insecure Defaults

**Vulnerable** (❌):
```rust
// Accepting all certificates (for HTTPS)
let client = reqwest::Client::builder()
    .danger_accept_invalid_certs(true)  // VULNERABLE
    .build()?;
```

**Safe** (✅):
```rust
// Proper certificate validation
let client = reqwest::Client::builder()
    .build()?;  // SAFE - validates certs by default
```

---

### 7. Cross-Site Scripting (XSS)

#### Unescaped Output

**Vulnerable** (❌):
```rust
// Rendering user input without escaping
fn render_comment(comment: &str) -> String {
    format!("<div>{}</div>", comment)  // VULNERABLE if comment contains <script>
}
```

**Safe** (✅):
```rust
use htmlescape::encode_minimal;

fn render_comment(comment: &str) -> String {
    format!("<div>{}</div>", encode_minimal(comment))  // SAFE
}
```

---

### 8. Insecure Deserialization

**Vulnerable** (❌):
```rust
use bincode;

// Deserializing untrusted data
fn load_config(data: &[u8]) -> Config {
    bincode::deserialize(data).unwrap()  // VULNERABLE - could execute code
}
```

**Safe** (✅):
```rust
use serde_json;

// Use safe formats (JSON) with validation
fn load_config(data: &[u8]) -> Result<Config, Error> {
    let config: Config = serde_json::from_slice(data)?;

    // Validate
    if !config.is_valid() {
        return Err(Error::InvalidConfig);
    }

    Ok(config)
}
```

---

### 9. Using Components with Known Vulnerabilities

#### Outdated Dependencies

**Check with**:
```bash
cargo audit
```

**Detection**:
- Run `cargo audit` in CI/CD
- Review `Cargo.lock` for old versions
- Check for security advisories

---

### 10. Insufficient Logging & Monitoring

**Vulnerable** (❌):
```rust
// No logging for security events
fn login(username: &str, password: &str) -> Result<Session, Error> {
    authenticate(username, password)?;
    Ok(create_session(username))
}
```

**Safe** (✅):
```rust
fn login(username: &str, password: &str) -> Result<Session, Error> {
    match authenticate(username, password) {
        Ok(_) => {
            logger::info!("Successful login for user: {}", username);
            Ok(create_session(username))
        }
        Err(e) => {
            logger::warn!("Failed login attempt for user: {}", username);
            Err(e)
        }
    }
}
```

**Log Security Events**:
- Failed authentication attempts
- Access to sensitive resources
- Permission changes
- Data modifications
- API rate limit violations

---

## Rust-Specific Security Issues

### 1. Integer Overflow

**Vulnerable** (❌):
```rust
fn calculate_total(price: u32, quantity: u32) -> u32 {
    price * quantity  // VULNERABLE - can overflow
}
```

**Safe** (✅):
```rust
fn calculate_total(price: u32, quantity: u32) -> Result<u32, Error> {
    price.checked_mul(quantity)
        .ok_or(Error::IntegerOverflow)
}
```

---

### 2. Unsafe Code

**Vulnerable** (❌):
```rust
unsafe {
    let ptr = data.as_ptr();
    *ptr = value;  // VULNERABLE - undefined behavior possible
}
```

**Safe** (✅):
```rust
// Use safe abstractions
data[index] = value;  // SAFE - bounds checked
```

**Rule**: NEVER use `unsafe` in this codebase

---

### 3. Thread Safety

**Vulnerable** (❌):
```rust
use std::rc::Rc;
use std::cell::RefCell;

static mut COUNTER: i32 = 0;  // VULNERABLE - not thread-safe

fn increment() {
    unsafe { COUNTER += 1; }
}
```

**Safe** (✅):
```rust
use std::sync::atomic::{AtomicI32, Ordering};

static COUNTER: AtomicI32 = AtomicI32::new(0);

fn increment() {
    COUNTER.fetch_add(1, Ordering::SeqCst);
}
```

---

## Payment-Specific Security

### 1. PCI DSS Compliance

#### Card Data Handling

**Rules**:
- ❌ NEVER store full card numbers
- ❌ NEVER store CVV/CVC
- ❌ NEVER log card data
- ✅ Use tokenization
- ✅ Encrypt sensitive data at rest
- ✅ Use HTTPS for transmission

**Example**:
```rust
// WRONG
struct Payment {
    card_number: String,  // NEVER store full number
    cvv: String,          // NEVER store CVV
}

// CORRECT
struct Payment {
    card_token: String,   // Tokenized reference
    last_4_digits: String, // Only last 4 for display
}
```

---

### 2. Amount Validation

**Vulnerable** (❌):
```rust
// No validation
fn process_payment(amount: MinorUnit) {
    charge(amount);  // VULNERABLE - negative amounts?
}
```

**Safe** (✅):
```rust
fn process_payment(amount: MinorUnit) -> Result<(), Error> {
    if amount.is_zero() || amount.is_negative() {
        return Err(Error::InvalidAmount);
    }

    charge(amount)
}
```

---

### 3. Idempotency

**Vulnerable** (❌):
```rust
// No idempotency check
fn create_payment() -> Payment {
    let payment = Payment::new();
    db.insert(payment);  // VULNERABLE - duplicate payments
    payment
}
```

**Safe** (✅):
```rust
fn create_payment(idempotency_key: &str) -> Result<Payment, Error> {
    // Check if already processed
    if let Some(existing) = db.find_by_key(idempotency_key) {
        return Ok(existing);  // Return existing payment
    }

    let payment = Payment::new(idempotency_key);
    db.insert(payment.clone());
    Ok(payment)
}
```

---

## Input Validation

### 1. Validate All Inputs

**Validation Checklist**:
- ✅ Type validation (enforce types)
- ✅ Range validation (min/max)
- ✅ Format validation (regex, patterns)
- ✅ Whitelist validation (enum, allowed values)
- ✅ Length validation (strings, arrays)

**Example**:
```rust
fn validate_email(email: &str) -> Result<(), Error> {
    // Length check
    if email.len() > 254 {
        return Err(Error::EmailTooLong);
    }

    // Format check
    let email_regex = regex::Regex::new(r"^[^@]+@[^@]+\.[^@]+$").unwrap();
    if !email_regex.is_match(email) {
        return Err(Error::InvalidEmailFormat);
    }

    Ok(())
}
```

---

### 2. Sanitization

**HTML/XML**:
```rust
use htmlescape::encode_minimal;

fn sanitize_html(input: &str) -> String {
    encode_minimal(input)
}
```

**SQL**:
```rust
// Use parameterized queries (no manual sanitization needed)
```

**Shell Commands**:
```rust
// Avoid shell execution with user input
// If necessary, use strict whitelisting
fn is_safe_filename(name: &str) -> bool {
    name.chars().all(|c| c.is_alphanumeric() || c == '-' || c == '_')
}
```

---

## Rate Limiting

**Example**:
```rust
use std::collections::HashMap;
use std::time::{Duration, Instant};

struct RateLimiter {
    requests: HashMap<String, Vec<Instant>>,
    max_requests: usize,
    window: Duration,
}

impl RateLimiter {
    fn check(&mut self, client_id: &str) -> Result<(), Error> {
        let now = Instant::now();
        let requests = self.requests.entry(client_id.to_string()).or_default();

        // Remove old requests
        requests.retain(|&time| now.duration_since(time) < self.window);

        // Check limit
        if requests.len() >= self.max_requests {
            return Err(Error::RateLimitExceeded);
        }

        requests.push(now);
        Ok(())
    }
}
```

---

## Security Checklist

### For Every PR:

- [ ] No hardcoded credentials
- [ ] No SQL injection vulnerabilities
- [ ] No command injection vulnerabilities
- [ ] Proper input validation
- [ ] Sensitive data not logged
- [ ] Error messages don't leak info
- [ ] Authentication/authorization checks in place
- [ ] HTTPS enforced for external calls
- [ ] No unsafe code blocks
- [ ] Dependencies up to date (cargo audit)
- [ ] Rate limiting where applicable
- [ ] Proper error handling (no unwrap/expect)

### For Connector Integration:

- [ ] Credentials from auth_type only
- [ ] Card data never stored/logged
- [ ] Amount validation implemented
- [ ] Idempotency handled
- [ ] Reference IDs not hardcoded
- [ ] Status mapping secure (no info leakage)

---

## Automated Security Checks

### Cargo Audit
```bash
cargo audit
# Checks for known vulnerabilities
```

### Clippy Security Lints
```bash
cargo clippy -- -W clippy::unwrap_used -W clippy::expect_used
```

### Custom Security Scan
```bash
#!/bin/bash

echo "Scanning for security issues..."

# Hardcoded secrets
echo "Checking for hardcoded secrets..."
grep -rniE "(password|secret|api_key|token).*=.*[\"'][a-zA-Z0-9]{10,}" src/ && echo "⚠️  Found potential secrets"

# SQL injection
echo "Checking for potential SQL injection..."
grep -rn "format!.*SELECT\|INSERT\|UPDATE\|DELETE" src/ && echo "⚠️  Found potential SQL injection"

# Command injection
echo "Checking for potential command injection..."
grep -rn "Command::new.*format!" src/ && echo "⚠️  Found potential command injection"

# Unsafe blocks
echo "Checking for unsafe code..."
grep -rn "unsafe {" src/ && echo "⚠️  Found unsafe blocks"

echo "Security scan complete!"
```

---

## Version History

- **1.0.0** (2025-12-09): Initial security patterns
  - OWASP Top 10 checks
  - Rust-specific security issues
  - Payment security rules
  - Input validation patterns
  - Rate limiting examples
