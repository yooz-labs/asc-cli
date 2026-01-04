# asc-cli Scratch History

## Purpose
Document failed attempts, dead ends, and lessons learned during development.

## Failed Attempts Log

### Attempt: Using authlib for JWT
**Date:** January 2, 2026
**Goal:** Generate JWT tokens for App Store Connect API

#### Implementation:
```python
from authlib.jose import jwt
token = jwt.encode(header, payload, key)
```

#### Issue Encountered:
- Primary problem: ES256 key format incompatibility
- Error messages: "Could not deserialize key data"

#### Root Cause:
authlib expected different key format than Apple's .p8 files

#### Time Spent:
~30 minutes

#### Lesson Learned:
PyJWT handles Apple's .p8 format directly, no conversion needed

#### Alternative Solution:
Used PyJWT with cryptography backend - worked immediately

---

## Common Pitfalls

### Pitfall: Token Expiry
**Symptoms:** 401 errors after ~20 minutes
**Cause:** JWT tokens expire, not refreshed
**Solution:** Check expiry before requests, regenerate if needed

### Pitfall: Price Point Mismatch
**Symptoms:** API rejects price point ID
**Cause:** Price points vary by territory
**Solution:** Look up price points per territory, not globally

## Abandoned Approaches

### Approach: Storing tokens in keychain
**Why Considered:** More secure than file
**Why Abandoned:** Adds complexity, tokens are short-lived anyway
**Better Alternative:** Store credentials (not tokens) securely, generate tokens on demand

## Library/Tool Issues

### Tool: pre-commit with mypy
**Version:** mypy 1.10.0
**Issue:** Slow type checking on every commit
**Workaround:** Run mypy only on staged files
**Alternative:** Consider separate CI check for full type coverage

## Lessons Summary

### Key Learnings
1. Apple's API documentation is good but verbose
2. Price points are territory-specific, always look up
3. JWT tokens should be regenerated, not cached long

### Things to Check First Next Time
- [ ] API rate limits before bulk operations
- [ ] Token expiry before long-running commands
- [ ] Price point availability for new territories

### Patterns to Avoid
- Pattern: Caching JWT tokens - They expire quickly, regenerate instead
- Pattern: Hardcoding price points - They change, always look up
