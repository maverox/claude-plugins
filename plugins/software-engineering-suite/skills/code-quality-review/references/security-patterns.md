# Security Patterns Reference

Comprehensive guide to detecting security vulnerabilities based on OWASP Top 10 and language-specific patterns.

## OWASP Top 10 Checks

### 1. Injection (A03:2021)

#### SQL Injection

**TypeScript/JavaScript**:
```typescript
// CRITICAL - String concatenation
const query = `SELECT * FROM users WHERE id = ${userId}`;
const query = "SELECT * FROM users WHERE id = " + userId;

// SAFE - Parameterized queries
const query = 'SELECT * FROM users WHERE id = ?';
await db.query(query, [userId]);

// SAFE - ORM
const user = await User.findById(userId);
```

**Python**:
```python
# CRITICAL - String formatting
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
cursor.execute("SELECT * FROM users WHERE id = %s" % user_id)

# SAFE - Parameterized
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
cursor.execute("SELECT * FROM users WHERE id = %(id)s", {"id": user_id})
```

**Detection Patterns**:
```regex
# SQL with string interpolation
(execute|query|raw)\s*\(\s*[`"'].*\$\{
(execute|query|raw)\s*\(\s*f["']
SELECT.*\+\s*\w+
```

#### Command Injection

**TypeScript/JavaScript**:
```typescript
// CRITICAL
exec(`ls ${userInput}`);
spawn('sh', ['-c', userInput]);

// SAFE
execFile('ls', ['-la', sanitizedPath]);
```

**Python**:
```python
# CRITICAL
os.system(f"ls {user_input}")
subprocess.call(user_input, shell=True)

# SAFE
subprocess.run(['ls', '-la', sanitized_path], shell=False)
```

**Detection Patterns**:
```regex
exec\s*\(.*\$\{
system\s*\(.*\+
subprocess\.(call|run|Popen).*shell\s*=\s*True
```

#### Code Injection

**TypeScript/JavaScript**:
```typescript
// CRITICAL
eval(userInput);
new Function(userInput)();
setTimeout(userInput, 1000);

// SAFE
JSON.parse(userInput);  // For JSON data
```

**Python**:
```python
# CRITICAL
eval(user_input)
exec(user_input)

# SAFE
ast.literal_eval(user_input)  # For simple literals only
```

### 2. Broken Authentication (A07:2021)

**Patterns to Detect**:
```typescript
// CRITICAL - Hardcoded credentials
const password = "admin123";
const apiKey = "sk_live_xxxxx";

// CRITICAL - Weak password hashing
const hash = md5(password);
const hash = sha1(password);

// SAFE - Strong hashing
const hash = await bcrypt.hash(password, 12);
const hash = await argon2.hash(password);
```

**Detection Patterns**:
```regex
# Hardcoded secrets
(password|secret|api_?key|token)\s*[=:]\s*["'][^"']+["']
# Weak hashing
(md5|sha1)\s*\(
```

### 3. Sensitive Data Exposure (A02:2021)

**Patterns to Detect**:
```typescript
// CRITICAL - Logging sensitive data
console.log('Password:', password);
logger.info({ user, password });

// CRITICAL - Exposing in errors
throw new Error(`Login failed for ${email}: ${password}`);

// SAFE - Masked logging
logger.info({ user: user.email, passwordProvided: !!password });
```

**Detection Patterns**:
```regex
(console\.(log|info|debug)|logger\.).*password
(console\.(log|info|debug)|logger\.).*secret
(console\.(log|info|debug)|logger\.).*token
```

### 4. XML External Entities (A05:2021)

**Patterns to Detect**:
```typescript
// CRITICAL - XXE vulnerable
const parser = new DOMParser();
parser.parseFromString(userXml, 'text/xml');

// Python
from xml.etree import ElementTree
ElementTree.fromstring(user_xml)  # Vulnerable to XXE

// SAFE
import defusedxml.ElementTree as ET
ET.fromstring(user_xml)
```

### 5. Broken Access Control (A01:2021)

**Patterns to Detect**:
```typescript
// CRITICAL - Missing authorization
app.get('/admin/users', (req, res) => {
  // No auth check
  return getAllUsers();
});

// CRITICAL - IDOR
app.get('/user/:id', (req, res) => {
  // Using user-provided ID directly
  return getUser(req.params.id);
});

// SAFE
app.get('/user/:id', authMiddleware, (req, res) => {
  if (req.user.id !== req.params.id && !req.user.isAdmin) {
    return res.status(403).json({ error: 'Forbidden' });
  }
  return getUser(req.params.id);
});
```

### 6. Security Misconfiguration (A05:2021)

**Patterns to Detect**:
```typescript
// CRITICAL - Debug in production
app.use(errorHandler({ debug: true }));

// CRITICAL - CORS wildcard
app.use(cors({ origin: '*' }));

// CRITICAL - Disabled security headers
app.disable('x-powered-by');  // Actually good
helmet();  // Should use this

// SAFE
app.use(cors({ origin: 'https://myapp.com' }));
app.use(helmet());
```

### 7. Insecure Deserialization (A08:2021)

**Patterns to Detect**:
```python
# CRITICAL - Pickle with untrusted data
import pickle
data = pickle.loads(user_data)

# CRITICAL - YAML unsafe load
import yaml
data = yaml.load(user_data)  # Unsafe by default

# SAFE
data = yaml.safe_load(user_data)
data = json.loads(user_data)
```

```typescript
// CRITICAL - Unsafe JSON with reviver
JSON.parse(userInput, unsafeReviver);
```

### 8. Insufficient Logging (A09:2021)

**Patterns to Detect**:
```typescript
// WARNING - No logging on auth failure
if (!isValidPassword(password)) {
  return res.status(401).json({ error: 'Invalid' });
}

// SAFE - Logging security events
if (!isValidPassword(password)) {
  logger.warn('Login failed', { email, ip: req.ip });
  return res.status(401).json({ error: 'Invalid' });
}
```

### 9. SSRF (Server-Side Request Forgery)

**Patterns to Detect**:
```typescript
// CRITICAL - User-controlled URL
const response = await fetch(req.body.url);
axios.get(userProvidedUrl);

// SAFE - Allowlist validation
const allowedHosts = ['api.example.com', 'cdn.example.com'];
const url = new URL(userUrl);
if (!allowedHosts.includes(url.host)) {
  throw new Error('Invalid URL');
}
```

### 10. Path Traversal

**Patterns to Detect**:
```typescript
// CRITICAL - User input in file path
const file = fs.readFileSync(`./uploads/${req.params.filename}`);

// SAFE - Validation
const filename = path.basename(req.params.filename);
const filepath = path.join('./uploads', filename);
if (!filepath.startsWith('./uploads/')) {
  throw new Error('Invalid path');
}
```

## Language-Specific Patterns

### TypeScript/JavaScript

```typescript
// Dangerous functions
eval()
Function()
setTimeout(string)
setInterval(string)
document.write()
innerHTML = userInput
outerHTML = userInput
```

### Python

```python
# Dangerous functions
eval()
exec()
compile()
__import__()
pickle.loads()
yaml.load()  # without Loader
subprocess.*(shell=True)
os.system()
```

### Rust

```rust
// Unsafe blocks without justification
unsafe { }

// Potential memory issues
std::mem::transmute()
std::ptr::read()
std::ptr::write()
```

### Go

```go
// Template injection
template.HTML(userInput)

// SQL injection
db.Query("SELECT * FROM users WHERE id = " + id)
```

## Detection Commands

### Grep Patterns

```bash
# SQL Injection
grep -rn "execute.*\$\{" --include="*.ts" --include="*.js"
grep -rn "query.*\+" --include="*.py"

# Command Injection
grep -rn "exec\s*\(" --include="*.ts" --include="*.js"
grep -rn "os\.system" --include="*.py"

# Hardcoded Secrets
grep -rn "password\s*=\s*[\"']" --include="*.ts" --include="*.js" --include="*.py"
grep -rn "api_key\s*=\s*[\"']" --include="*.ts" --include="*.js" --include="*.py"

# Eval usage
grep -rn "\beval\s*\(" --include="*.ts" --include="*.js" --include="*.py"
```

### Automated Tools

```bash
# JavaScript/TypeScript
npx eslint --plugin security .

# Python
bandit -r .
safety check

# Rust
cargo audit

# General
semgrep --config=p/security-audit .
```

## Severity Classification

| Issue Type | Severity | Blocks Merge |
|------------|----------|--------------|
| SQL Injection | CRITICAL | Yes |
| Command Injection | CRITICAL | Yes |
| Code Injection (eval) | CRITICAL | Yes |
| Hardcoded Secrets | CRITICAL | Yes |
| Insecure Deserialization | CRITICAL | Yes |
| Path Traversal | CRITICAL | Yes |
| SSRF | CRITICAL | Yes |
| XSS | CRITICAL | Yes |
| Weak Cryptography | WARNING | No |
| Missing Auth Check | WARNING | No |
| Debug Mode | WARNING | No |
| Missing Security Headers | WARNING | No |
| Insufficient Logging | SUGGESTION | No |
