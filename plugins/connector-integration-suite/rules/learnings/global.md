# Global Learnings

Dynamic cross-session learnings from connector integrations.
**This file is updated by agents after each successful integration.**

> [!NOTE]
> This is a **template** provided by the plugin. Actual learnings accumulate in your project's `.claude/rules/learnings/global.md` and should be committed to your project repository.

## Authentication Patterns

- OAuth2 connectors require `CreateAccessToken` flow
- API key connectors use `ApiHeaderKey` auth type
- Bearer token auth uses `SignatureKey` with header prefix

## Amount Handling

- Always use `MinorUnit` type for amounts
- Declare appropriate converters: `StringMinorUnit`, `StringMajorUnit`, etc.
- Never use `f64` or floats for monetary values

## Status Mapping

- Map all connector statuses to UCS status enums
- Handle unknown statuses gracefully with `Pending`
- Document unmapped statuses in comments

## Request/Response Patterns

- Use `Secret<>` wrapper for all PII fields
- Extract reference IDs from router_data, never hardcode
- Use `?` operator instead of `unwrap()`

<!-- Agents: Add new learnings below this line -->
