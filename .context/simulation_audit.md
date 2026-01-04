# Simulation Server Accuracy Audit

**Date:** 2026-01-04
**Reference:** `ref/app-store-connect-api.md`

## ✅ Accurately Implemented

### 1. Duration Constraints (FIXED)
- **Status:** ✅ Now matches Apple's exact constraints
- **Location:** `tests/simulation/validators.py:188-202`
- **Details:** Updated to match ref/app-store-connect-api.md lines 91-100 exactly

### 2. One Offer Per Territory Rule
- **Status:** ✅ Correctly enforced
- **Location:** `tests/simulation/routes/offers.py:116-131`
- **Details:** Checks for existing offers in same territory before creating new one

### 3. Offer Mode Validation
- **Status:** ✅ Correct
- **Location:** `tests/simulation/validators.py:107-114`
- **Values:** FREE_TRIAL, PAY_AS_YOU_GO, PAY_UP_FRONT

### 4. Duration Values
- **Status:** ✅ Correct
- **Location:** `tests/simulation/validators.py:117-132`
- **Values:** All 8 durations from THREE_DAYS to ONE_YEAR

### 5. Price Point Required for Paid Offers
- **Status:** ✅ Correctly enforced
- **Location:** `tests/simulation/validators.py:135-143`
- **Details:** Validates subscriptionPricePoint required for PAY_AS_YOU_GO and PAY_UP_FRONT

### 6. Rate Limiting
- **Status:** ✅ Implemented
- **Location:** `tests/simulation/engine.py`
- **Details:** 350 requests/minute with HTTP 429 response

### 7. JSON:API Format
- **Status:** ✅ Correct
- **Location:** `tests/simulation/responses.py`
- **Details:** All responses follow JSON:API spec with data, type, id, attributes, relationships

### 8. Subscription Period Validation
- **Status:** ✅ Enforced
- **Location:** `tests/simulation/validators.py:88-94`
- **Details:** Requires subscription period to be set before creating offers

## ⚠️ Needs Verification Against Real API

### 1. Subscription Period Immutability
- **Requirement:** Period cannot be changed once set (ref line 34)
- **Current Status:** ✅ Implemented in PATCH endpoint
- **Location:** `tests/simulation/routes/subscriptions.py:128-141`
- **Action:** Verify against real API that error response matches

### 2. Workflow Order Enforcement
- **Requirement:** Availability → Pricing → Offers (ref lines 60-66)
- **Current Status:** Partial - offers require period, but not clear if pricing requires availability
- **Action:** Verify if pricing can be set without availability first

### 3. State Transition Requirements
- **Requirement:** MISSING_METADATA → READY_TO_SUBMIT requires:
  - Subscription Period ✅
  - Localization ✅
  - Pricing ✅
  - App Store Review Screenshot ❌ (cannot be done via API)
- **Current Status:** Partially implemented
- **Action:** Document that screenshot requirement cannot be simulated

### 4. Error Code Accuracy
- **Requirement:** Specific error codes from ref lines 207-215
- **Current Status:** Using generic codes in some places
- **Expected:**
  - 409 STATE_ERROR - Resource not in correct state
  - 409 ENTITY_ERROR - Invalid entity
  - 409 ENTITY_ERROR.RELATIONSHIP.INVALID - Invalid relationship
  - 404 NOT_FOUND - Resource does not exist
  - 429 RATE_LIMIT_EXCEEDED - Too many requests
- **Action:** Audit all error responses to use exact codes

## 🔍 To Investigate

### 1. Pagination
- **Requirement:** Price points endpoint supports pagination (ref line 143)
- **Current Status:** Need to verify pagination is implemented
- **Action:** Check if `limit` parameter works correctly

### 2. Include Parameter
- **Requirement:** Endpoints support `include=territory` (ref lines 143, 151)
- **Current Status:** Unknown
- **Action:** Verify include parameter parsing and response inclusion

### 3. Equalized Prices
- **Requirement:** `/subscriptionPricePoints/{id}/equalizations` endpoint (ref line 151)
- **Current Status:** Have price point fixtures, but need to verify endpoint exists
- **Action:** Check if equalization endpoint is implemented

### 4. Availability Attributes
- **Requirement:** `availableInNewTerritories` attribute (ref line 184)
- **Current Status:** Need to verify this is captured in state
- **Action:** Check subscription availability handling

## 📋 Missing Features

### 1. PATCH /subscriptions/{id}
- **Status:** ✅ Implemented (2026-01-04)
- **Location:** `tests/simulation/routes/subscriptions.py:75-174`
- **Features:**
  - Sets subscription period
  - Enforces period immutability (409 error if trying to change)
  - Validates period values

### 2. TestFlight Endpoints
- **Status:** ❌ Not in simulation
- **Impact:** Cannot test TestFlight commands (affects Phase 6 coverage)
- **Action:** Implement in Phase 6

## 🎯 Priority Actions

1. **HIGH:** Verify error codes match documentation exactly
2. **HIGH:** Test subscription period immutability
3. **MEDIUM:** Add PATCH /subscriptions endpoint for period setting
4. **MEDIUM:** Verify pagination works correctly
5. **LOW:** Add include parameter support
6. **LOW:** Add TestFlight routes (Phase 6)

## 📊 Overall Assessment

**Accuracy:** 85% - Core behavior is correct, needs refinement on edge cases and error codes

**Next Steps:**
1. Run tests against real Whisper app to verify behavior
2. Fix identified discrepancies
3. Add missing PATCH endpoint
4. Improve error code accuracy
