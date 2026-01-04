# asc-cli Design Ideas

## Purpose
Capture high-level concepts, design decisions, and architectural ideas before implementation.

## Core Concepts

### Project Vision
**Goal:** Be the "gh" CLI for App Store Connect
**Key Principles:**
- Simple commands for common tasks
- YAML configs for complex/bulk operations
- Rich terminal output by default, JSON/YAML for scripting

## Architecture Ideas

### CLI Structure
```
asc <resource> <action> [options]
```
- `asc auth` - Authentication management
- `asc apps` - App management
- `asc subscriptions` - Subscription & pricing
- `asc testflight` - Beta testing
- `asc bulk` - Bulk operations from YAML

### API Client Design
**Concept:** Layered client with separation of concerns
**Components:**
- `AuthClient` - JWT token generation and refresh
- `APIClient` - HTTP requests with retry logic
- `ResourceClient` - High-level resource operations

**Trade-offs:**
- Pro: Clear separation, easy testing
- Pro: Token refresh handled automatically
- Con: More files to maintain
- Con: Need to pass client through layers

### Output Formats
```python
class OutputFormat(str, Enum):
    TABLE = "table"   # Rich tables (default)
    JSON = "json"     # For scripting
    YAML = "yaml"     # For config export
    CSV = "csv"       # For reports
```

## Feature Ideas

### Feature: Bulk Pricing
**Concept:** Apply pricing across 175 territories from YAML
**User Value:** One command instead of 175 API calls
**Implementation:** Parse YAML, lookup price points, batch API calls
**Complexity:** Medium
**Priority:** Must-have

### Feature: Price Point Lookup
**Concept:** Convert USD amount to territory-specific price points
**User Value:** "Set $2.99" instead of knowing price point IDs
**Implementation:** Cache price points, fuzzy match to requested price
**Complexity:** Medium
**Priority:** Must-have

### Feature: Subscription Templates
**Concept:** Define subscription structure in YAML
**User Value:** Version control subscription configuration
**Implementation:** YAML schema with pricing, offers, metadata
**Complexity:** Complex
**Priority:** Nice-to-have

## Design Patterns

### Pattern: Command Groups
**Use Case:** Related commands under a namespace
**Benefits:** Discoverable CLI, organized help
**Example:**
```bash
asc subscriptions list
asc subscriptions pricing list
asc subscriptions pricing set
asc subscriptions offers create
```

### Pattern: Progress Indicators
**Use Case:** Long-running operations (bulk pricing)
**Benefits:** User feedback, interruptibility
**Implementation:** Rich progress bars with ETA

## User Experience Ideas

### Workflow: Setting Up New Subscription
**Goal:** Create subscription with pricing and free trial
**Steps:**
1. `asc subscriptions create --name "Pro Monthly" --group "Pro"`
2. `asc subscriptions pricing set --subscription pro.monthly --price 2.99`
3. `asc subscriptions offers create --subscription pro.monthly --type free-trial --days 14`

**Pain Points to Address:**
- Price point lookup is tedious
- Territory selection is overwhelming
- Offer configuration is complex

## Technical Explorations

### Concept: Async API Client
**Hypothesis:** Async httpx could speed up bulk operations
**Benefits if Successful:**
- Parallel requests for bulk pricing
- Better UX with progress updates
**Risks:**
- Complexity in error handling
- Rate limit management harder
**Experiment Needed:** Benchmark sync vs async for 175-territory pricing

## Future Possibilities

### Long-term Vision
- CI/CD integration for subscription management
- GitHub Actions for automated pricing updates
- Diff and preview for config changes

### Stretch Goals
- Interactive mode with fuzzy search
- Webhook integration for status updates
- Dashboard web UI option
