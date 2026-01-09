# Performance Patterns Reference

Anti-patterns and best practices for performance-conscious code review.

## N+1 Query Problem

### The Problem

```typescript
// WARNING - N+1 queries
async function getUsersWithOrders() {
  const users = await db.query('SELECT * FROM users');  // 1 query

  for (const user of users) {
    // N queries (one per user)
    user.orders = await db.query('SELECT * FROM orders WHERE user_id = ?', [user.id]);
  }

  return users;
}
```

### The Solution

```typescript
// GOOD - Single query with JOIN
async function getUsersWithOrders() {
  const results = await db.query(`
    SELECT u.*, o.*
    FROM users u
    LEFT JOIN orders o ON o.user_id = u.id
  `);
  return groupByUser(results);
}

// GOOD - Two queries with IN clause
async function getUsersWithOrders() {
  const users = await db.query('SELECT * FROM users');
  const userIds = users.map(u => u.id);

  const orders = await db.query(
    'SELECT * FROM orders WHERE user_id IN (?)',
    [userIds]
  );

  return users.map(user => ({
    ...user,
    orders: orders.filter(o => o.user_id === user.id)
  }));
}
```

### Detection Pattern

```bash
# Look for queries inside loops
grep -rn "for.*{" -A 10 --include="*.ts" | grep -E "(query|find|select|fetch)"
```

## Unnecessary Allocations

### Rust

```rust
// WARNING - Unnecessary clone
fn process(data: &String) {
    let owned = data.clone();  // Clone when borrow would work
    println!("{}", owned);
}

// GOOD - Use reference
fn process(data: &str) {
    println!("{}", data);
}

// WARNING - Clone in loop
for item in items {
    let copy = item.clone();  // Cloning every iteration
    process(copy);
}

// GOOD - Move or borrow
for item in items {
    process(&item);  // Borrow
}
// Or
for item in items.into_iter() {
    process(item);  // Move ownership
}
```

### JavaScript/TypeScript

```typescript
// WARNING - Creating arrays in loops
function process(items: Item[]) {
  for (const item of items) {
    const temp = [];  // New array every iteration
    temp.push(item);
    doSomething(temp);
  }
}

// WARNING - Spread in accumulator
const result = items.reduce((acc, item) => [...acc, item.value], []);
// Creates new array for each item

// GOOD - Push to existing array
const result = items.reduce((acc, item) => {
  acc.push(item.value);
  return acc;
}, []);

// Or just map
const result = items.map(item => item.value);
```

### Python

```python
# WARNING - String concatenation in loop
result = ""
for item in items:
    result += str(item)  # Creates new string each time

# GOOD - Use join
result = "".join(str(item) for item in items)

# WARNING - List append with +
result = []
for item in items:
    result = result + [item]  # Creates new list

# GOOD - Use append
result = []
for item in items:
    result.append(item)

# Or comprehension
result = [item for item in items]
```

## Blocking in Async Context

### TypeScript/JavaScript

```typescript
// WARNING - Sync file read in async context
async function processFiles(paths: string[]) {
  for (const path of paths) {
    const content = fs.readFileSync(path);  // Blocks event loop
    await process(content);
  }
}

// GOOD - Use async APIs
async function processFiles(paths: string[]) {
  for (const path of paths) {
    const content = await fs.promises.readFile(path);
    await process(content);
  }
}

// BETTER - Parallel processing
async function processFiles(paths: string[]) {
  const contents = await Promise.all(
    paths.map(path => fs.promises.readFile(path))
  );
  await Promise.all(contents.map(process));
}
```

### Python

```python
# WARNING - Sync call in async function
async def fetch_all(urls):
    results = []
    for url in urls:
        response = requests.get(url)  # Blocks!
        results.append(response)
    return results

# GOOD - Use async HTTP client
async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [session.get(url) for url in urls]
        return await asyncio.gather(*tasks)
```

### Rust

```rust
// WARNING - Blocking in async
async fn process() {
    let data = std::fs::read_to_string("file.txt")?;  // Blocks!
}

// GOOD - Use async file I/O
async fn process() {
    let data = tokio::fs::read_to_string("file.txt").await?;
}

// WARNING - std::thread::sleep in async
async fn delayed() {
    std::thread::sleep(Duration::from_secs(1));  // Blocks executor
}

// GOOD - Use async sleep
async fn delayed() {
    tokio::time::sleep(Duration::from_secs(1)).await;
}
```

## Memory Leaks

### JavaScript/TypeScript

```typescript
// WARNING - Event listener not removed
class Component {
  constructor() {
    window.addEventListener('resize', this.handleResize);
  }

  // Missing cleanup - listener persists after component destroyed
}

// GOOD - Cleanup on destroy
class Component {
  constructor() {
    window.addEventListener('resize', this.handleResize);
  }

  destroy() {
    window.removeEventListener('resize', this.handleResize);
  }
}

// WARNING - Closure capturing large objects
function createHandler(largeData) {
  return () => {
    console.log(largeData.length);  // Captures entire largeData
  };
}

// GOOD - Capture only what's needed
function createHandler(largeData) {
  const length = largeData.length;
  return () => {
    console.log(length);  // Only captures the number
  };
}
```

### React Specific

```typescript
// WARNING - Missing cleanup in useEffect
useEffect(() => {
  const subscription = api.subscribe(handleUpdate);
  // Missing return cleanup function!
}, []);

// GOOD - Proper cleanup
useEffect(() => {
  const subscription = api.subscribe(handleUpdate);
  return () => subscription.unsubscribe();
}, []);

// WARNING - Interval not cleared
useEffect(() => {
  setInterval(doSomething, 1000);  // Runs forever
}, []);

// GOOD - Clear interval
useEffect(() => {
  const id = setInterval(doSomething, 1000);
  return () => clearInterval(id);
}, []);
```

## Inefficient Loops

### Repeated Lookups

```typescript
// WARNING - Repeated object access
for (let i = 0; i < items.length; i++) {
  if (config.settings.advanced.featureFlags.enableNewAlgorithm) {
    // Deep access every iteration
  }
}

// GOOD - Cache outside loop
const useNewAlgorithm = config.settings.advanced.featureFlags.enableNewAlgorithm;
for (let i = 0; i < items.length; i++) {
  if (useNewAlgorithm) {
    // Use cached value
  }
}
```

### Unnecessary Work in Loops

```typescript
// WARNING - Regex creation in loop
for (const str of strings) {
  if (new RegExp(pattern).test(str)) {  // Compiles regex every iteration
    // ...
  }
}

// GOOD - Compile once
const regex = new RegExp(pattern);
for (const str of strings) {
  if (regex.test(str)) {
    // ...
  }
}

// WARNING - DOM queries in loop
for (const item of items) {
  const container = document.getElementById('container');  // Query every time
  container.appendChild(createNode(item));
}

// GOOD - Query once
const container = document.getElementById('container');
for (const item of items) {
  container.appendChild(createNode(item));
}
```

## Inefficient Data Structures

```typescript
// WARNING - Array for lookups
const users = [{ id: 1, name: 'Alice' }, { id: 2, name: 'Bob' }];
function findUser(id) {
  return users.find(u => u.id === id);  // O(n) lookup
}

// GOOD - Map for frequent lookups
const usersById = new Map(users.map(u => [u.id, u]));
function findUser(id) {
  return usersById.get(id);  // O(1) lookup
}

// WARNING - Set operations on array
const arr = [1, 2, 3, 4, 5];
if (arr.includes(target)) { ... }  // O(n)

// GOOD - Use Set for membership tests
const set = new Set([1, 2, 3, 4, 5]);
if (set.has(target)) { ... }  // O(1)
```

## Missing Indexes (Database)

```sql
-- WARNING - Query on non-indexed column
SELECT * FROM orders WHERE status = 'pending';
-- If status is not indexed, full table scan

-- GOOD - Ensure index exists
CREATE INDEX idx_orders_status ON orders(status);

-- WARNING - Query on multiple columns without compound index
SELECT * FROM orders WHERE user_id = ? AND status = 'pending';

-- GOOD - Compound index for common queries
CREATE INDEX idx_orders_user_status ON orders(user_id, status);
```

## Detection Patterns

### Grep Commands

```bash
# N+1 pattern (queries in loops)
grep -rn "for\|while\|forEach" -A 5 --include="*.ts" | grep -E "query|find|select|await db\."

# Sync file operations in async
grep -rn "async" -A 20 --include="*.ts" | grep "readFileSync\|writeFileSync"

# Clone in Rust
grep -rn "\.clone()" --include="*.rs"

# Event listeners without cleanup
grep -rn "addEventListener" --include="*.ts" --include="*.tsx"
# Then check for corresponding removeEventListener

# setInterval without clearInterval
grep -rn "setInterval" --include="*.ts" --include="*.tsx"
```

### ESLint Rules

```json
{
  "rules": {
    "no-await-in-loop": "warn",
    "require-atomic-updates": "warn"
  }
}
```

### Clippy (Rust)

```bash
cargo clippy -- -W clippy::clone_on_ref_ptr -W clippy::redundant_clone
```

## Severity Classification

| Issue | Severity | Description |
|-------|----------|-------------|
| N+1 queries | WARNING | Major performance issue |
| Blocking in async | WARNING | Blocks event loop/executor |
| Memory leak (event listeners) | WARNING | Growing memory usage |
| Unnecessary clone | SUGGESTION | Extra allocations |
| Inefficient loop | SUGGESTION | Repeated work |
| Missing database index | WARNING | Slow queries |
| String concatenation in loop | SUGGESTION | Extra allocations |
| Regex in loop | SUGGESTION | Repeated compilation |
