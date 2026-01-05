# API Validation Findings

**Date:** 2026-01-04
**Validated Against:** Real Whisper App (live.yooz.whisper)
**Test Results:** `tests/validation/comparison_results.json`

## Summary

- **Total Endpoints Tested:** 3
- **Passed:** 0
- **Failed:** 3
- **Overall Status:** ⚠️ Significant discrepancies found

## Critical Findings

### 1. Missing `relationships` Field in ALL Resources

**Severity:** HIGH
**Impact:** JSON:API spec violation

All resource types are missing the `relationships` field:
- Apps
- Subscription Groups
- Subscriptions

**Real API Response:**
```json
{
  "type": "apps",
  "id": "6757027131",
  "attributes": { ... },
  "relationships": {
    "subscriptionGroups": {
      "links": {
        "self": "...",
        "related": "..."
      }
    }
  }
}
```

**Simulation Response:**
```json
{
  "type": "apps",
  "id": "app_whisper",
  "attributes": { ... }
  // Missing relationships!
}
```

**Fix Required:** Add `relationships` field to `build_resource()` in `tests/simulation/responses.py`

---

### 2. Missing App Attributes (11 fields)

**Severity:** MEDIUM
**Impact:** Incomplete app data

Missing attributes in app responses:
1. `subscriptionStatusUrl` - Webhook URL for subscription events
2. `subscriptionStatusUrlForSandbox` - Sandbox webhook URL
3. `subscriptionStatusUrlVersion` - Webhook version
4. `subscriptionStatusUrlVersionForSandbox` - Sandbox webhook version
5. `isOrEverWasMadeForKids` - COPPA compliance flag
6. `streamlinedPurchasingEnabled` - Streamlined purchasing setting
7. `sku` - App SKU identifier
8. `accessibilityUrl` - Accessibility description URL
9. `contentRightsDeclaration` - Content rights declaration
10. `primaryLocale` - App's primary locale
11. `relationships` - Related resources

**Fix Required:** Update `StateManager.add_app()` to include these attributes

---

### 3. Missing Subscription Group Attributes

**Severity:** LOW
**Impact:** Missing metadata

Missing in subscription groups:
- `relationships` - Links to subscriptions

**Also Found:**
- Reference name mismatch (test data vs real data)
  - Real: "Yooz Whisper Plans"
  - Simulation: "Whisper Pro"

**Fix Required:** Add relationships support

---

### 4. Missing Subscription Attributes (4 fields)

**Severity:** MEDIUM
**Impact:** Missing important subscription metadata

Missing attributes in subscription responses:
1. `reviewNote` - Internal review notes
2. `familySharable` - Family Sharing enabled flag
3. `groupLevel` - Subscription level within group (1-10)
4. `relationships` - Links to related resources

**Fix Required:** Update `StateManager.add_subscription()` to include these fields

---

## Test Data Discrepancies

These are **NOT bugs** - just test data that doesn't match real Whisper app:

### Subscription Names & Product IDs

| Real Whisper App | Simulation Fixture |
|---|---|
| Pro Monthly | Whisper Pro Monthly |
| Pro Yearly | Whisper Pro Yearly |
| Pro Family Monthly | Whisper Pro Family Monthly |
| Pro Family Yearly | Whisper Pro Family Yearly |

**Product IDs:**
- Real: `live.yooz.whisper.pro.monthly`
- Simulation: `live.yooz.whisper.pro.family_monthly` (underscore vs dot)

**Action:** Update `tests/simulation/fixtures/apps.py:load_whisper_app()` to match real data

---

## Required Fixes

### Priority 1: Add `relationships` Field (Critical)

**File:** `tests/simulation/responses.py`

Update `build_resource()` to support relationships:

```python
def build_resource(
    resource_type: str,
    resource_id: str,
    attributes: dict[str, Any],
    relationships: dict[str, Any] | None = None,  # ADD THIS
) -> dict[str, Any]:
    resource = {
        "type": resource_type,
        "id": resource_id,
        "attributes": attributes,
    }

    if relationships:  # ADD THIS
        resource["relationships"] = relationships

    return resource
```

Then update all route handlers to pass relationships.

### Priority 2: Add Missing App Attributes

**File:** `tests/simulation/state.py`

Update `add_app()` method:

```python
def add_app(
    self,
    app_id: str,
    bundle_id: str,
    name: str,
    sku: str | None = None,
    primary_locale: str = "en-US",
    # ... add other parameters
) -> None:
    self.apps[app_id] = {
        "id": app_id,
        "attributes": {
            "bundleId": bundle_id,
            "name": name,
            "sku": sku or app_id,
            "primaryLocale": primary_locale,
            "isOrEverWasMadeForKids": False,
            "streamlinedPurchasingEnabled": False,
            "contentRightsDeclaration": "USES_THIRD_PARTY_CONTENT",
            "subscriptionStatusUrl": None,
            "subscriptionStatusUrlForSandbox": None,
            "subscriptionStatusUrlVersion": None,
            "subscriptionStatusUrlVersionForSandbox": None,
            "accessibilityUrl": None,
        }
    }
```

### Priority 3: Add Missing Subscription Attributes

**File:** `tests/simulation/state.py`

Update `add_subscription()`:

```python
def add_subscription(
    self,
    subscription_id: str,
    group_id: str,
    product_id: str,
    name: str,
    state: str = "MISSING_METADATA",
    subscription_period: str | None = None,
    family_sharable: bool = True,  # ADD
    group_level: int = 1,  # ADD
    review_note: str | None = None,  # ADD
) -> None:
    self.subscriptions[subscription_id] = {
        "id": subscription_id,
        "attributes": {
            "name": name,
            "productId": product_id,
            "state": state,
            "subscriptionPeriod": subscription_period,
            "familySharable": family_sharable,  # ADD
            "groupLevel": group_level,  # ADD
            "reviewNote": review_note,  # ADD
        }
    }
```

### Priority 4: Fix Test Data

**File:** `tests/simulation/fixtures/apps.py`

Update `load_whisper_app()` to use correct names and product IDs:

```python
subscription_configs = [
    ("monthly", "ONE_MONTH", "2.99", "Pro Monthly"),  # Changed from "Whisper Pro Monthly"
    ("yearly", "ONE_YEAR", "29.99", "Pro Yearly"),  # Changed
    ("family_monthly", "ONE_MONTH", "6.99", "Pro Family Monthly"),  # Changed
    ("family_yearly", "ONE_YEAR", "69.99", "Pro Family Yearly"),  # Changed
]

# And fix product IDs:
product_id = f"{bundle_id}.pro.{suffix.replace('_', '.')}"  # Use dots instead of underscores
```

---

## Validation Checklist

- [ ] Add `relationships` to all resources
- [ ] Add missing app attributes
- [ ] Add missing subscription attributes
- [ ] Update Whisper fixture data to match real app
- [ ] Re-run validation to verify fixes
- [ ] Test that simulation still works with updated structure
- [ ] Update tests to expect new fields

---

## Next Validation Run

After fixes, expected results:
- **Structure discrepancies:** 0 (all fields present)
- **Value discrepancies:** 0 (test data matches real data)
- **Test status:** 3/3 PASS

---

## Notes

- Relationships are a core part of JSON:API spec
- Missing them makes responses technically invalid
- Some attributes (like `sku`) are required by Apple
- Test data accuracy helps validate CLI commands work correctly
