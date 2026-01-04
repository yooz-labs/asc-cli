# yooz-asc Development Plan

## Project Overview
**Goal:** CLI for Apple App Store Connect API management
**Stack:** Python 3.10+, Typer, httpx, Pydantic

## Development Tasks

### Phase 1: Foundation [CURRENT]
- [x] Project structure with uv/ruff/mypy
- [x] Typer CLI framework setup
- [x] Authentication module (JWT token generation)
- [x] Base API client with httpx
- [x] Credential storage (~/.config/yooz-asc/)
- [x] `asc auth login/status/logout/test`
- [x] `asc apps list/info`
- [x] `asc subscriptions list` (basic)
- [x] `asc testflight` (stubs)

### Phase 2: Subscriptions & Pricing
- [ ] `asc subscriptions create` - Create new subscription
- [ ] `asc subscriptions delete` - Delete subscription
- [ ] `asc subscriptions update` - Update subscription metadata
- [ ] `asc subscriptions groups list/create/delete`
- [ ] `asc subscriptions pricing list` - Show current prices
- [ ] `asc subscriptions pricing set` - Set price for subscription
- [ ] `asc subscriptions pricing equalizations` - Show equivalent prices
- [ ] Bulk pricing from YAML file

### Phase 3: Introductory & Promotional Offers
- [ ] `asc subscriptions offers list` - List current offers
- [ ] `asc subscriptions offers create` - Create offer
- [ ] `asc subscriptions offers delete` - Remove offer
- [ ] `asc subscriptions promos list/create/delete`
- [ ] Signature generation for promotional offers

### Phase 4: TestFlight
- [ ] `asc testflight builds list` - List builds with filters
- [ ] `asc testflight builds info` - Build details
- [ ] `asc testflight builds expire` - Expire a build
- [ ] `asc testflight builds submit` - Submit for beta review
- [ ] `asc testflight groups list/create/delete`
- [ ] `asc testflight groups add-build/remove-build`
- [ ] `asc testflight testers list/add/remove/invite`

### Phase 5: App Management
- [ ] `asc apps versions list/create/submit`
- [ ] `asc apps metadata get/set`
- [ ] `asc apps screenshots upload`
- [ ] `asc apps review status/cancel`

### Phase 6: Reports & Analytics
- [ ] `asc reports sales` - Download sales reports
- [ ] `asc reports subscriptions` - Subscription analytics
- [ ] `asc reports finance` - Financial reports
- [ ] `asc reviews list/respond`

### Phase 7: Bulk Operations
- [ ] `asc bulk apply` - Apply YAML configuration
- [ ] `asc bulk export` - Export current config to YAML

## Success Criteria
- [ ] All core commands implemented and tested
- [ ] Documentation complete and accurate
- [ ] CI/CD pipeline functional
- [ ] 95%+ test coverage
- [ ] Published to PyPI

## Milestones
1. **v0.1.0** - Auth + basic listing (Complete)
2. **v0.2.0** - Full subscription pricing + offers
3. **v0.3.0** - TestFlight management
4. **v0.4.0** - App submission workflow
5. **v0.5.0** - Reports and analytics
6. **v1.0.0** - Full feature parity + stable API

## Notes
- API rate limiting: 500 requests/hour for most endpoints
- Pagination: All list endpoints return max 200 items
- Retry logic: Exponential backoff for 429 responses
