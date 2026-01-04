# asc-cli Implementation Plan

## Overview

A comprehensive CLI for Apple App Store Connect API, similar to GitHub's `gh` CLI.

## Phase 1: Foundation (Current)

### Core Infrastructure
- [x] Project structure with uv/ruff/mypy
- [x] Typer CLI framework setup
- [x] Authentication module (JWT token generation)
- [x] Base API client with httpx
- [x] Credential storage (~/.config/asc-cli/)

### Basic Commands
- [x] `asc auth login/status/logout/test`
- [x] `asc apps list/info`
- [x] `asc subscriptions list` (basic)
- [x] `asc testflight` (stubs)

## Phase 2: Subscriptions & Pricing

### Subscription Management
- [ ] `asc subscriptions create` - Create new subscription
- [ ] `asc subscriptions delete` - Delete subscription
- [ ] `asc subscriptions update` - Update subscription metadata
- [ ] `asc subscriptions groups list/create/delete`

### Pricing (175 territories)
- [ ] `asc subscriptions pricing list` - Show current prices
- [ ] `asc subscriptions pricing set` - Set price for subscription
  - Single territory or all territories
  - Price point lookup by USD amount
  - Bulk pricing from YAML file
- [ ] `asc subscriptions pricing equalizations` - Show equivalent prices

### Introductory Offers
- [ ] `asc subscriptions offers list` - List current offers
- [ ] `asc subscriptions offers create` - Create offer
  - Free trial (duration: 3d, 1w, 2w, 1m, 2m, 3m, 6m, 1y)
  - Pay as you go (discounted recurring)
  - Pay up front (one-time discounted)
- [ ] `asc subscriptions offers delete` - Remove offer

### Promotional Offers
- [ ] `asc subscriptions promos list`
- [ ] `asc subscriptions promos create`
- [ ] `asc subscriptions promos delete`
- [ ] Signature generation for promotional offers

## Phase 3: TestFlight

### Builds
- [ ] `asc testflight builds list` - List builds with filters
- [ ] `asc testflight builds info` - Build details
- [ ] `asc testflight builds expire` - Expire a build
- [ ] `asc testflight builds submit` - Submit for beta review

### Beta Groups
- [ ] `asc testflight groups list`
- [ ] `asc testflight groups create`
- [ ] `asc testflight groups delete`
- [ ] `asc testflight groups add-build`
- [ ] `asc testflight groups remove-build`

### Testers
- [ ] `asc testflight testers list`
- [ ] `asc testflight testers add`
- [ ] `asc testflight testers remove`
- [ ] `asc testflight testers invite` - Send/resend invite

## Phase 4: App Management

### Versions
- [ ] `asc apps versions list`
- [ ] `asc apps versions create`
- [ ] `asc apps versions submit` - Submit for review

### Metadata
- [ ] `asc apps metadata get`
- [ ] `asc apps metadata set`
- [ ] `asc apps screenshots upload`

### Review
- [ ] `asc apps review status`
- [ ] `asc apps review cancel`

## Phase 5: Reports & Analytics

### Sales Reports
- [ ] `asc reports sales` - Download sales reports
- [ ] `asc reports subscriptions` - Subscription analytics
- [ ] `asc reports finance` - Financial reports

### Performance
- [ ] `asc metrics list` - Performance metrics
- [ ] `asc metrics diagnostics` - Diagnostic logs

### Customer Reviews
- [ ] `asc reviews list`
- [ ] `asc reviews respond`

## Phase 6: Provisioning

### Certificates
- [ ] `asc certs list`
- [ ] `asc certs create`
- [ ] `asc certs revoke`

### Profiles
- [ ] `asc profiles list`
- [ ] `asc profiles create`
- [ ] `asc profiles delete`

### Devices
- [ ] `asc devices list`
- [ ] `asc devices register`
- [ ] `asc devices disable`

### Bundle IDs
- [ ] `asc bundles list`
- [ ] `asc bundles create`
- [ ] `asc bundles capabilities`

## Phase 7: Team Management

### Users
- [ ] `asc users list`
- [ ] `asc users invite`
- [ ] `asc users remove`
- [ ] `asc users roles`

## Phase 8: Advanced Features

### Bulk Operations
- [ ] `asc bulk apply` - Apply YAML configuration
- [ ] `asc bulk export` - Export current config to YAML

### Configuration Files
```yaml
# Example: subscriptions.yaml
subscriptions:
  - product_id: com.example.pro.monthly
    name: Pro Monthly
    price: 2.99
    introductory_offer:
      type: free-trial
      duration: 2w
```

### Xcode Cloud
- [ ] `asc xcode-cloud workflows list`
- [ ] `asc xcode-cloud builds list`
- [ ] `asc xcode-cloud builds start`

## Technical Considerations

### API Coverage
- App Store Connect API v1 and v2
- Handle pagination (all list endpoints)
- Rate limiting (respect API limits)
- Retry logic with exponential backoff

### Territory Handling
- 175 territories for pricing
- Bulk operations for efficiency
- Parallel requests where safe

### Output Formats
- Rich terminal output (default)
- JSON output (`--json`)
- YAML output (`--yaml`)
- CSV output for reports (`--csv`)

### Testing Strategy
- Unit tests with mocked API responses
- Integration tests with sandbox
- 95%+ code coverage requirement

### CI/CD
- GitHub Actions for testing
- Automated releases to PyPI
- Homebrew formula updates

## API Endpoints Reference

### Core Endpoints
- `/v1/apps` - App management
- `/v1/subscriptions` - Subscription CRUD
- `/v1/subscriptionGroups` - Subscription groups
- `/v1/subscriptionPrices` - Pricing
- `/v1/subscriptionPricePoints` - Price point lookup
- `/v1/subscriptionIntroductoryOffers` - Intro offers
- `/v1/subscriptionPromotionalOffers` - Promo offers
- `/v1/territories` - Territory list

### TestFlight Endpoints
- `/v1/builds` - Build management
- `/v1/betaGroups` - Beta groups
- `/v1/betaTesters` - Tester management
- `/v1/preReleaseVersions` - Pre-release versions

### Reports Endpoints
- `/v1/salesReports` - Sales data
- `/v1/financeReports` - Financial data
- `/v1/analyticsReportRequests` - Analytics

## Milestones

1. **v0.1.0** - Auth + basic listing (Current)
2. **v0.2.0** - Full subscription pricing + offers
3. **v0.3.0** - TestFlight management
4. **v0.4.0** - App submission workflow
5. **v0.5.0** - Reports and analytics
6. **v1.0.0** - Full feature parity + stable API
