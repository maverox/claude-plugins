---
name: research-api-docs
description: |
  Scrape and parse payment connector API documentation to extract endpoints,
  schemas, auth patterns, and status codes. Creates structured specifications
  for connector implementation. Use when researching API docs, analyzing
  documentation, extracting endpoints, or creating technical specs.
  Auto-activates for requests like: "research [connector] API", "scrape documentation for",
  "extract API endpoints from", "analyze API docs", "create spec for [connector]".
allowed-tools: WebSearch, WebFetch, mcp__firecrawl__firecrawl_scrape,
  mcp__firecrawl__firecrawl_search, mcp__firecrawl__firecrawl_crawl, Write, Read, Grep, Glob
version: 1.0.0
---

# Research API Documentation Skill

## Overview

Extract technical specifications from payment connector API documentation by scraping, parsing, and structuring API information. This skill creates comprehensive specifications that serve as the foundation for connector implementation.

## When to Use This Skill

Auto-activates for these request patterns:
- "Research the [connector] API and create a spec"
- "Scrape documentation for [connector]"
- "Extract API endpoints from [connector] docs"
- "Analyze [connector] API documentation"
- "Create specification for [connector]"

Also useful for:
- Understanding payment flows supported by a connector
- Identifying authentication methods
- Documenting request/response schemas
- Mapping status codes and error formats

## Input Context

The skill receives these parameters:
- `connector_name` (required): Name of the connector (e.g., "stripe", "adyen")
- `api_docs_url` (optional): Direct documentation URL. If not provided, auto-discovers via web search.

## Process

### Phase 0: Consult References

Read the flow definitions and capability mapping reference to understand what to look for:

```bash
Read(".claude/skills/research-api-docs/references/flow-definitions.md")
Read(".claude/skills/research-api-docs/references/capability-mapping.md")
Read(".claude/knowledge/connector_integration_guide.md")
```

Focus on these sections:
1. **Standard Flow Definitions** - Understand the flows you need to identify
2. **Capability Mapping requirements** - Know what information to extract for each flow

### Phase 1: Find Documentation

**Web Search First Approach**:

**Step 1: Search the Web with WebSearch()**
1. Use `WebSearch()` to SEARCH the web for official API documentation
2. Query: "[connector_name] payment API documentation" or "[connector_name] API reference"
3. Extract relevant documentation URLs from search results
4. Prioritize official connector domains and developer documentation

**Step 2: Fallback Search (if WebSearch fails)**
If WebSearch returns errors or no useful results:
1. Use `mcp__firecrawl__firecrawl_search()` to search for documentation
2. Query: "[connector_name] API documentation"
3. Extract and prioritize official documentation links

**Step 3: Scrape Documentation with WebFetch (Controlled Scraping)**
After finding documentation URLs, use controlled scraping:
1. Use `WebFetch()` for controlled scraping of documentation pages
   - Provides structured markdown output
   - More reliable for extracting specific content
   - Better handling of page structure
2. If WebFetch fails, use `mcp__firecrawl__firecrawl_scrape()` as fallback
   - Use when WebFetch can't handle complex layouts
   - More aggressive scraping capabilities
3. For complex multi-page documentation, use `mcp__firecrawl__firecrawl_crawl()`
   - Crawls entire documentation sections
   - Useful for discovering all available endpoints
   - Use with appropriate depth and path filters
4. Extract links to find API documentation pages
5. Scrape content from relevant sections

### Phase 2: Extract Endpoints

Search for payment-related endpoints. Look for:
- Payment creation/authorization endpoints
- Payment capture endpoints
- Payment cancellation/void endpoints
- Refund endpoints
- Status check/retrieval endpoints
- Recurring payment/mandate setup endpoints

For each endpoint, document:
- HTTP method (POST, GET, etc.)
- URL path
- Request headers required
- Request body schema
- Response schema
- Authentication requirements
- Status codes

### Phase 3: Extract Authentication

Identify the authentication method:
- API keys (HeaderKey)
- Bearer tokens / OAuth (CreateAccessToken)
- Basic auth
- Custom signatures

Document:
- Where to obtain credentials
- Header names and formats
- Token refresh requirements

### Phase 4: Extract Amount Handling

Analyze amount formats in the API:
- String with no decimals (e.g., "1000") → StringMinorUnit
- String with decimals (e.g., "10.00") → StringMajorUnit
- Number (e.g., 10.00) → FloatMajorUnit

Document actual examples from the API.

### Phase 5: Extract Status Codes

Map connector status codes to UCS statuses:
- Payment succeeded → Charged
- Payment pending → Pending
- Payment failed → Failed
- Refund succeeded → Refunded
- Unknown statuses → Pending

### Phase 6: Create Specification

Create `.claude/context/connectors/<connector_name>/spec.md` with:
1. Connector overview
2. Supported payment flows
3. API endpoints (organized by flow)
4. Authentication details
5. Amount handling
6. Status mapping
7. Base URLs
8. Rate limits
9. Error formats
10. Pattern recognition notes for planning agent

## Output

Creates these artifacts:
- **Primary Output**: `.claude/context/connectors/<connector_name>/spec.md`
- **Context**: Pattern recognition notes about auth signals and amount formats

The specification is structured and comprehensive, enabling the planning agent to create implementation strategies.

## Examples

### Standalone Usage

**User**: "Research the Stripe API and create a spec"

**Skill Action**:
1. Searches for Stripe API documentation
2. Scrapes documentation pages
3. Extracts all payment-related endpoints
4. Identifies authentication (Bearer tokens)
5. Maps status codes
6. Creates comprehensive spec file

**Output**: Specification ready for implementation planning

### Orchestrated Usage

Called by `/connector-integrate stripe https://stripe.com/docs/api`:
1. Receives connector_name and api_docs_url
2. Creates specification
3. Planning agent consumes the spec

## Integration

**Prerequisites**: None - can be used standalone

**Dependents**:
- `plan-connector-implementation` skill consumes the spec
- `/connector-integrate` command orchestrates this skill as Phase 1

**Command Integration**: The `/connector-integrate` command invokes this skill automatically during the research phase, passing connector_name and api_docs_url.

## References

- Flow Definitions: `.claude/skills/research-api-docs/references/flow-definitions.md`
- Capability Mapping: `.claude/skills/research-api-docs/references/capability-mapping.md`
- Pattern Recognition: `.claude/skills/research-api-docs/references/scraping-patterns.md`
- UCS Integration Guide: `.claude/knowledge/connector_integration_guide.md`