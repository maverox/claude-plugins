# Common Issues

Frequently encountered issues during connector integrations.
**This file is updated by agents to track recurring patterns.**

> [!NOTE]
> This is a **template** provided by the plugin. Actual issues accumulate in your project's `.claude/rules/learnings/common-issues.md` and should be committed to your project repository.

## Critical Issues

### Using RouterData instead of RouterDataV2
- **Frequency**: High
- **Severity**: Critical
- **Fix**: Always import and use `domain_types::router_data_v2::RouterDataV2`
- **Detection**: grep for `RouterData,` or `RouterData<`

### Missing Amount Converters
- **Frequency**: High
- **Severity**: Critical
- **Fix**: Declare converters in `create_all_prerequisites!` macro
- **Detection**: Empty `amount_converters:` block

### Reference ID Mutation
- **Frequency**: Medium
- **Severity**: High
- **Fix**: Extract reference IDs from router_data, never modify them
- **Detection**: grep for `session_id.clone()` patterns

### Using unwrap() Instead of Error Propagation
- **Frequency**: High
- **Severity**: Medium
- **Fix**: Use `?` operator or proper error handling
- **Detection**: grep for `.unwrap()`

## Medium Issues

### Missing Status Mapping
- **Frequency**: Medium
- **Severity**: Medium
- **Fix**: Map all connector statuses to UCS status enums
- **Detection**: Review match arms for completeness

### Incorrect Amount Format
- **Frequency**: Medium
- **Severity**: High
- **Fix**: Check connector docs for minor vs major unit, use correct converter
- **Detection**: Compare with connector API documentation

<!-- Agents: Add new issues below with frequency tracking -->
