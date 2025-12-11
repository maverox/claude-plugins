# Web Scraping Patterns for API Documentation

## Overview

Best practices for extracting information from payment connector API documentation using a **WebSearch-first approach** with Firecrawl as fallback.

## Primary Strategy: WebSearch + WebFetch

### Understanding the Two-Step Process

**WebSearch**: SEARCHES the web for documentation links
**WebFetch**: Provides CONTROLLED SCRAPING of documentation pages

This two-step approach ensures reliability:
1. Find documentation URLs efficiently with web search
2. Scrape content reliably with controlled extraction

### Step 1: SEARCH the Web for Documentation

**Primary: Use WebSearch() to search**
```bash
# WebSearch SEARCHES the web for relevant links
WebSearch(query: "[connector_name] payment API documentation", limit: 5)
```

**Fallback (if WebSearch fails):**
```bash
# Fallback: Use Firecrawl search (also searches)
mcp__firecrawl__firecrawl_search(query: "[connector_name] API documentation", limit: 5)
```

### Step 2: Extract Documentation URLs from Search Results
From search results, identify and extract:
- Official API documentation links
- Developer documentation portals
- API reference pages
- Payment-related endpoints

Prioritize:
1. Official connector domain (e.g., stripe.com, adyen.com)
2. Developer/API sections
3. Most recent documentation versions

### Step 3: SCRAPE Documentation with WebFetch (Controlled Extraction)

**Primary: Use WebFetch() for controlled scraping**
```bash
# WebFetch provides CONTROLLED SCRAPING
# - Returns structured markdown
# - Better handling of page structure
# - More reliable for extracting specific content
WebFetch(url: "[documentation_url]", prompt: "Extract API endpoints, authentication, and schemas")
```

**Fallback (if WebFetch fails):**
```bash
# Use Firecrawl scrape for more aggressive extraction
# - More powerful scraping capabilities
# - Better for complex/dynamic documentation
mcp__firecrawl__firecrawl_scrape(url: "[documentation_url]", formats: ["markdown"])
```

### Step 4: Handle Complex/Multi-Page Documentation

For multi-page or complex documentation:
```bash
# Use Firecrawl crawl for multi-page extraction
mcp__firecrawl__firecrawl_crawl(
  url: "[documentation_base_url]/*",
  includePaths: ["*/api/*", "*/payments/*", "*/reference/*"],
  maxDiscoveryDepth: 3
)
```

Use when:
- Documentation spans multiple pages
- Need to discover all available endpoints
- Single page fetch isn't sufficient

## Common Documentation Structures

### Stripe-Style Docs
**Structure**: Separate pages for each endpoint
**Navigation**:
- Main API reference page lists all endpoints
- Each endpoint has dedicated page with examples
- Try-it sections with cURL examples

**Scraping Strategy**:
```bash
1. Navigate to main API reference
2. Extract all endpoint links
3. For each endpoint:
   - Navigate to endpoint page
   - Scrape HTTP method and path
   - Extract request example
   - Extract response example
   - Note auth requirements
```

### Adyen-Style Docs
**Structure**: Single page with expandable sections
**Navigation**:
- Long single page with sections for each flow
- Expandable sections with details
- Multiple examples per endpoint

**Scraping Strategy**:
```bash
1. Navigate to API documentation page
2. Scroll through entire page to load all sections
3. Use evaluate to find all endpoint patterns
4. Extract data from visible sections
5. Look for: "Method", "Endpoint", "Request", "Response"
```

### PayPal-Style Docs
**Structure**: API Explorer with live examples
**Navigation**:
- Interactive API explorer
- Tabbed interface for different endpoints
- Code samples in multiple languages

**Scraping Strategy**:
```bash
1. Navigate to API reference
2. Take screenshot to see page structure
3. Click through tabs to see all endpoints
4. Extract from visible examples
5. Note sandbox vs production differences
```

## Navigation Patterns

### Finding API Endpoints
Search for these patterns in documentation:
- HTTP method + URL pattern (e.g., "POST /v1/payments")
- Endpoint headers
- Code examples with request/response
- "API Reference" sections

**Grep Patterns**:
- `POST|GET|PUT|DELETE`
- `/v[0-9]+/`
- `curl`
- `Request Body`
- `Response`

### Identifying Auth Methods
Look for:
- "Authentication" sections
- Headers in examples
- "API Key" references
- "Bearer token" mentions
- OAuth flow descriptions

**Key Phrases**:
- "x-api-key"
- "Authorization: Bearer"
- "api_key"
- "client_id"
- "client_secret"

### Finding Amount Formats
Look for:
- Request body examples
- JSON samples
- "amount" fields
- Currency handling

**Key Patterns**:
- `"amount": "1000"` (string, no decimal)
- `"amount": "10.00"` (string with decimal)
- `"amount": 10.00` (number)
- `amount_cents`

## Puppeteer Tool Usage

### Navigate
```bash
mcp__puppeteer__puppeteer_navigate(url)
```

**Best Practices**:
- Navigate to main API reference first
- Look for "API Reference" or "Documentation" links
- Some sites require cookie consent - handle this

### Extract Links
```bash
mcp__puppeteer__puppeteer_evaluate(
  "Array.from(document.querySelectorAll('a'))
   .map(a => a.href)
   .filter(h => h.includes('api') || h.includes('docs') || h.includes('reference'))
   .filter(h => !h.includes('#'))"
)
```

**Tips**:
- Filter for relevant links only
- Remove anchors (# links)
- Check for pagination or "Load More" buttons

### Click Elements
```bash
mcp__puppeteer__puppeteer_click(selector)
```

**Selectors to try**:
- `"a[href*='api']"`
- `".nav-link"`
- `.accordion-toggle`
- `.expand-button`
- `button:contains('Show more')`

### Screenshot for Debugging
```bash
mcp__puppeteer__puppeteer_screenshot(name: "page-structure")
```

**When to use**:
- After initial navigation
- When clicking doesn't work
- To see what content is actually loaded
- To understand page structure

### Evaluate for Content
```bash
mcp__puppeteer__puppeteer_evaluate("document.body.innerText")
```

**For extracting specific content**:
```javascript
// Extract all endpoint definitions
Array.from(document.querySelectorAll('pre, code'))
  .map(el => el.innerText)
  .filter(text => text.includes('curl') || text.includes('POST'))

// Extract request/response examples
Array.from(document.querySelectorAll('.code-example, .example'))
  .map(el => ({
    request: el.querySelector('.request')?.innerText,
    response: el.querySelector('.response')?.innerText
  }))

// Extract tables
Array.from(document.querySelectorAll('table'))
  .map(table => {
    const rows = Array.from(table.querySelectorAll('tr'))
    return rows.map(row => ({
      method: row.querySelector('td:nth-child(1)')?.innerText,
      endpoint: row.querySelector('td:nth-child(2)')?.innerText
    }))
  })
```

## Handling Common Issues

### Issue: Single Page Application
**Problem**: Content loads via JavaScript
**Solution**: Add wait before scraping

```bash
# Wait for page to load
mcp__puppeteer__puppeteer_evaluate("""
  new Promise(resolve => {
    if (document.readyState === 'complete') {
      resolve();
    } else {
      window.addEventListener('load', resolve);
    }
  });
""")

# Then extract content
```

### Issue: Expandable Sections
**Problem**: Details hidden until clicked
**Solution**: Click to expand before scraping

```bash
# Click all expand buttons
mcp__puppeteer__puppeteer_evaluate("""
  Array.from(document.querySelectorAll('button, .toggle, .expand'))
    .forEach(btn => btn.click());
""")

# Wait for animations
sleep 2

# Then extract content
```

### Issue: Pagination
**Problem**: Multiple pages of endpoints
**Solution**: Navigate through pages

```bash
# Check for pagination
mcp__puppeteer__puppeteer_evaluate("""
  const nextButtons = document.querySelectorAll('a[href*="next"], .pagination-next');
  return nextButtons.length > 0;
""")

# If pagination exists, click through pages
# Repeat extraction for each page
```

### Issue: Cookie Consent
**Problem**: Cookie banner blocks content
**Solution**: Accept cookies

```bash
# Try to click cookie accept buttons
mcp__puppeteer__puppeteer_evaluate("""
  const acceptButtons = document.querySelectorAll('[id*="accept"], [class*="accept"], button:contains("Accept")');
  if (acceptButtons.length > 0) {
    acceptButtons[0].click();
    return true;
  }
  return false;
""")

# Wait for banner to disappear
sleep 2
```

## Extraction Templates

### Endpoint Extraction Template
```
## [Flow Name]
**HTTP Method**: [POST/GET/PUT/DELETE]
**Path**: [URL path]
**Description**: [What it does]

**Request**:
[JSON request example]

**Response**:
[JSON response example]

**Auth Required**: [yes/no]
**Notes**: [Any special handling]
```

### Authentication Template
```
**Auth Type**: [HeaderKey/CreateAccessToken/Basic/Custom]

**Header Details**:
- Header Name: [x-api-key/Authorization/Basic]
- Format: [Bearer token/api key/username:password]
- Where to get: [dashboard/api key section]

**Example**:
[curl example with auth]
```

### Status Code Template
```
**Common Status Codes**:
- 200: Success
- 400: Bad Request (validation error)
- 401: Unauthorized (invalid auth)
- 403: Forbidden (insufficient permissions)
- 404: Not Found (resource doesn't exist)
- 429: Too Many Requests (rate limited)
- 500: Server Error

**Connector-Specific**:
[List from documentation]
```

## Tips for Better Extraction

1. **Start Broad, Then Narrow**
   - First, get overview of all endpoints
   - Then deep-dive into specific flow pages

2. **Use Multiple Extraction Methods**
   - InnerText for structured data
   - OuterHTML for preserving formatting
   - Screenshots for visual debugging

3. **Validate as You Go**
   - Check that examples are syntactically valid JSON
   - Verify amount formats match expectations
   - Confirm all required fields are documented

4. **Save Progress**
   - Take screenshots at key points
   - Extract to file incrementally
   - Don't rely on memory

5. **Handle Rate Limiting**
   - Don't click too rapidly
   - Add delays between requests
   - If blocked, wait and retry

## Common Pitfalls

❌ **Don't**: Assume single page has all endpoints
✅ **Do**: Check navigation menu for section links

❌ **Don't**: Skip expandable sections
✅ **Do**: Click to expand before extracting

❌ **Don't**: Trust that examples match actual API
✅ **Do**: Cross-reference multiple examples

❌ **Don't**: Ignore test vs production differences
✅ **Do**: Note base URLs and credential requirements

❌ **Don't**: Miss rate limiting information
✅ **Do**: Document rate limits for planning agent