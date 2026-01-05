# asc-cli Development Plan

## Project Overview
**Goal:** CLI for Apple App Store Connect API management
**Stack:** Python 3.10+, Typer, httpx, Pydantic

## Development Tasks

### Phase 1: Foundation ✅ COMPLETE
- [x] Project structure with uv/ruff/mypy
- [x] Typer CLI framework setup
- [x] Authentication module (JWT token generation)
- [x] Base API client with httpx (with pagination support)
- [x] Credential storage (~/.config/asc-cli/)
- [x] `asc auth login/status/logout/test`
- [x] `asc apps list/info`
- [x] `asc subscriptions list` (full implementation)
- [x] `asc testflight builds/groups/testers` (complete)

### Phase 2: Subscriptions & Pricing ✅ COMPLETE
- [x] `asc subscriptions check` - Check subscription readiness status
- [x] `asc subscriptions pricing list` - Show current prices across territories
- [x] `asc subscriptions pricing set` - Set price with territory support
- [x] Price equalization via API integration
- [x] Bulk pricing from YAML file
- [ ] `asc subscriptions create` - Create new subscription *(deferred)*
- [ ] `asc subscriptions delete` - Delete subscription *(deferred)*
- [ ] `asc subscriptions update` - Update subscription metadata *(deferred)*
- [ ] `asc subscriptions groups list/create/delete` *(deferred)*

### Phase 3: Introductory & Promotional Offers ✅ COMPLETE
- [x] `asc subscriptions offers list` - List current offers
- [x] `asc subscriptions offers create` - Create offer with validation
- [x] `asc subscriptions offers delete` - Remove offer with confirmation
- [x] Duration and period validation
- [x] Territory-based offer management
- [ ] `asc subscriptions promos list/create/delete` *(future)*
- [ ] Signature generation for promotional offers *(future)*

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

### Phase 7: Bulk Operations ✅ COMPLETE
- [x] `asc bulk init` - Generate YAML configuration template
- [x] `asc bulk validate` - Validate YAML configuration
- [x] `asc bulk apply` - Apply YAML configuration with dry-run support
- [x] Bulk pricing across 175 territories
- [x] Error tracking and reporting
- [ ] `asc bulk export` - Export current config to YAML *(future)*

## Success Criteria
- [x] All core commands implemented and tested (subscription management complete)
- [x] 96% test coverage (exceeds 95% target) ✨
- [x] CI/CD pipeline functional (GitHub Actions with ruff, mypy, pytest)
- [x] NO MOCKS testing policy enforced
- [ ] Documentation complete and accurate *(in progress)*
- [ ] Published to PyPI *(future)*

## Milestones
1. **v0.1.0** - Auth + basic listing ✅ Complete
2. **v0.2.0** - Full subscription pricing + offers [CURRENT - 95% complete]
   - Pricing and offers fully implemented
   - Bulk operations working
   - Remaining: subscription CRUD operations (deferred)
3. **v0.3.0** - TestFlight management ✅ Complete (basic commands)
4. **v0.4.0** - App submission workflow *(future)*
5. **v0.5.0** - Reports and analytics *(future)*
6. **v1.0.0** - Full feature parity + stable API *(future)*

## Current Status (2026-01-04)

### What Works
- Full subscription pricing management across 175 territories
- Introductory offer creation and management
- Bulk pricing operations via YAML
- Comprehensive test suite (245 tests, 96% coverage)
- Real API validation against production Whisper app
- Pagination support for large datasets

### What's Next
- Documentation improvements
- Error message refinement
- Package publishing to PyPI
- Subscription CRUD operations (if needed)

## Notes
- API rate limiting: 350 requests/minute (implemented in simulator)
- Pagination: All list endpoints return max 200 items (handled automatically)
- Pagination tested with 200+ price points across 175 territories
- NO MOCKS policy: All tests use simulation or real API
