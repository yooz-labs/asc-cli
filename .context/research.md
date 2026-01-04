# asc-cli Research Notes

## Purpose
Track technical solutions, approaches, and references discovered during development.

## Research Log

### Problem: JWT Token Generation for App Store Connect
**Date:** January 2, 2026
**Context:** Need to authenticate with App Store Connect API

#### Explored Solutions:
1. **PyJWT with ES256:**
   - Description: Use pyjwt library with cryptography for ES256
   - Pros: Well-maintained, widely used
   - Cons: Requires cryptography dependency
   - References: https://developer.apple.com/documentation/appstoreconnectapi/creating-api-keys-for-app-store-connect-api

#### Decision:
**Selected:** PyJWT with ES256
**Rationale:** Industry standard, good documentation, handles key parsing

#### Implementation Notes:
- Token expires in 20 minutes (max allowed)
- Must include `aud: appstoreconnect-v1` claim
- Private key is .p8 format (PEM-encoded EC key)

---

### Problem: API Response Pagination
**Date:** January 2, 2026
**Context:** List endpoints return max 200 items

#### Explored Solutions:
1. **Manual pagination:**
   - Description: Parse `links.next` and make subsequent requests
   - Pros: Simple, explicit
   - Cons: More code, easy to get wrong

2. **Generator pattern:**
   - Description: Yield items, fetch next page transparently
   - Pros: Clean API, lazy loading
   - Cons: Can't easily parallelize

#### Decision:
**Selected:** Generator pattern
**Rationale:** Clean API for callers, handles pagination transparently

---

## References & Resources

### Documentation
- [App Store Connect API](https://developer.apple.com/documentation/appstoreconnectapi) - Official docs
- [JWT for ASC](https://developer.apple.com/documentation/appstoreconnectapi/creating-api-keys-for-app-store-connect-api) - Auth details
- [Subscription Pricing](https://developer.apple.com/documentation/appstoreconnectapi/subscription_prices) - Price management

### Code Examples
- [apple-app-store-connect](https://github.com/Ponytech/appstoreconnectapi) - Python reference
- [fastlane spaceship](https://github.com/fastlane/fastlane/tree/master/spaceship) - Ruby implementation

## Technical Decisions Log

### Decision: HTTP Client
**Date:** January 2, 2026
**Options Considered:**
- requests: Synchronous, well-known, no async
- httpx: Sync + async, modern, good typing
- aiohttp: Async only, complex
**Choice:** httpx
**Reasoning:** Modern API, supports both sync and async, good type hints

### Decision: CLI Framework
**Date:** January 2, 2026
**Options Considered:**
- Click: Mature, widely used
- Typer: Modern, type hints, builds on Click
- argparse: Standard library, verbose
**Choice:** Typer
**Reasoning:** Type hints for validation, Rich integration, less boilerplate
