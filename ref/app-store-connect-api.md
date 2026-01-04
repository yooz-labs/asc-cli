# App Store Connect API Reference

This document serves as a grounding reference for asc-cli CLI implementation.

## API Base URL

```
https://api.appstoreconnect.apple.com/v1
```

## Authentication

JWT Bearer token with ES256 algorithm. Token expires after 20 minutes.

## Subscriptions API

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/apps/{id}/subscriptionGroups` | GET | List subscription groups for an app |
| `/subscriptionGroups/{id}/subscriptions` | GET | List subscriptions in a group |
| `/subscriptions/{id}` | GET/PATCH | Get or update subscription |
| `/subscriptions/{id}/pricePoints` | GET | List price points for subscription |
| `/subscriptionPricePoints/{id}/equalizations` | GET | Get equalized prices for other territories |
| `/subscriptionPrices` | POST | Create/update subscription price |
| `/subscriptionAvailabilities` | POST | Set subscription availability |
| `/subscriptionIntroductoryOffers` | POST | Create introductory offer |
| `/territories` | GET | List all territories |

### Subscription Duration (subscriptionPeriod)

The subscription billing period can be set via PATCH request if not already set.
Once set to a value, it **cannot be changed** to a different value.

**Setting the period via API:**
```json
PATCH /subscriptions/{id}
{
  "data": {
    "type": "subscriptions",
    "id": "SUBSCRIPTION_ID",
    "attributes": {
      "subscriptionPeriod": "ONE_MONTH"
    }
  }
}
```

Available durations:
- `ONE_WEEK`
- `ONE_MONTH`
- `TWO_MONTHS`
- `THREE_MONTHS`
- `SIX_MONTHS`
- `ONE_YEAR`

If a subscription shows "MISSING_METADATA" status and needs its duration set, this **must be done in App Store Connect UI**.

### Workflow Order

The correct order for configuring subscriptions via API:

1. **Set Availability** - Which territories the subscription is available in
2. **Set Pricing** - Price points for each territory
3. **Create Offers** - Introductory offers (requires availability + pricing first)

## Introductory Offers API

### Offer Modes (offerMode)

```
FREE_TRIAL     - Free trial period
PAY_AS_YOU_GO  - Discounted recurring payments
PAY_UP_FRONT   - Single discounted payment upfront
```

### Duration Values (duration)

```
THREE_DAYS
ONE_WEEK
TWO_WEEKS
ONE_MONTH
TWO_MONTHS
THREE_MONTHS
SIX_MONTHS
ONE_YEAR
```

### Duration Constraints by Subscription Period

| Subscription Period | Valid Offer Durations |
|--------------------|----------------------|
| ONE_WEEK | 3 days |
| ONE_MONTH | 1 week, 2 weeks, 1 month, 2 months, 3 months |
| TWO_MONTHS | 1 month, 2 months, 3 months, 6 months |
| THREE_MONTHS | 1 month, 2 months, 3 months, 6 months |
| SIX_MONTHS | 1 month, 3 months, 6 months |
| ONE_YEAR | 1 week, 1 month, 2 months, 3 months, 6 months, 1 year |

### Create Introductory Offer Request

```json
{
  "data": {
    "type": "subscriptionIntroductoryOffers",
    "attributes": {
      "duration": "TWO_WEEKS",
      "offerMode": "FREE_TRIAL",
      "numberOfPeriods": 1
    },
    "relationships": {
      "subscription": {
        "data": { "type": "subscriptions", "id": "SUBSCRIPTION_ID" }
      },
      "territory": {
        "data": { "type": "territories", "id": "USA" }
      },
      "subscriptionPricePoint": {
        "data": { "type": "subscriptionPricePoints", "id": "PRICE_POINT_ID" }
      }
    }
  }
}
```

**Note**: `subscriptionPricePoint` is only required for `PAY_AS_YOU_GO` and `PAY_UP_FRONT` offers.

### Error: "Subscription missing duration"

This error occurs when:
1. The subscription's `subscriptionPeriod` has not been set
2. The subscription is in `MISSING_METADATA` state

**Solution**: Set the subscription duration in App Store Connect UI before creating offers via API.

## Price Points API

### List Price Points

```
GET /subscriptions/{id}/pricePoints?include=territory&limit=200
```

Returns all available price tiers for a subscription, with pagination.

### Get Equalized Prices

```
GET /subscriptionPricePoints/{id}/equalizations?include=territory&limit=200
```

Given a base price point (usually USA), returns equivalent prices for all other territories based on Apple's price equalization.

### Create Subscription Price

```json
{
  "data": {
    "type": "subscriptionPrices",
    "attributes": {},
    "relationships": {
      "subscription": {
        "data": { "type": "subscriptions", "id": "SUBSCRIPTION_ID" }
      },
      "subscriptionPricePoint": {
        "data": { "type": "subscriptionPricePoints", "id": "PRICE_POINT_ID" }
      }
    }
  }
}
```

## Availability API

### Set Subscription Availability

```json
{
  "data": {
    "type": "subscriptionAvailabilities",
    "attributes": {
      "availableInNewTerritories": true
    },
    "relationships": {
      "subscription": {
        "data": { "type": "subscriptions", "id": "SUBSCRIPTION_ID" }
      },
      "availableTerritories": {
        "data": [
          { "type": "territories", "id": "USA" },
          { "type": "territories", "id": "GBR" }
        ]
      }
    }
  }
}
```

## Rate Limiting

- Approximately 300-350 requests per minute
- Returns HTTP 429 when limit exceeded
- Limit resets at the next minute boundary

## Common Error Codes

| Status | Code | Description |
|--------|------|-------------|
| 409 | STATE_ERROR | Resource not in correct state (e.g., availability not set, overlapping offers) |
| 409 | ENTITY_ERROR | Invalid entity (e.g., missing required fields) |
| 409 | ENTITY_ERROR.RELATIONSHIP.INVALID | Invalid relationship (e.g., subscription missing duration) |
| 404 | NOT_FOUND | Resource does not exist |
| 429 | RATE_LIMIT_EXCEEDED | Too many requests |

## Subscription State Requirements

A subscription must meet these requirements to move from `MISSING_METADATA` to `READY_TO_SUBMIT`:

1. **Subscription Period** - Must be set (ONE_WEEK, ONE_MONTH, etc.)
2. **Localization** - At least one locale with name and description
3. **Pricing** - At least one price point configured
4. **App Store Review Screenshot** - Must be uploaded (cannot be done via API easily)

## Introductory Offers Limitations

**Only ONE introductory offer per subscription per territory at any given time.**

If you try to create multiple offers (e.g., both a free trial and pay-as-you-go), you'll get:
```
STATE_ERROR: Provided DateRange overlaps with existing offer's DateRange
```

To have multiple offer types, schedule them for different date ranges.

## Sources

- [App Store Connect API Documentation](https://developer.apple.com/documentation/appstoreconnectapi)
- [Managing Auto-Renewable Subscriptions](https://developer.apple.com/documentation/appstoreconnectapi/managing-auto-renewable-subscriptions)
- [Offer Auto-Renewable Subscriptions](https://developer.apple.com/help/app-store-connect/manage-subscriptions/offer-auto-renewable-subscriptions)
- [Set Up Introductory Offers](https://developer.apple.com/help/app-store-connect/manage-subscriptions/set-up-introductory-offers-for-auto-renewable-subscriptions/)
