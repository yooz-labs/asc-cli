"""Request validators for API simulation.

Validates incoming requests match Apple's documented format and constraints.
"""

from typing import Any


class ValidationError(Exception):
    """Request validation failed."""

    def __init__(self, status: int, code: str, detail: str) -> None:
        self.status = status
        self.code = code
        self.detail = detail
        super().__init__(detail)


def validate_json_api_request(data: dict[str, Any], expected_type: str) -> None:
    """Validate JSON:API request structure.

    Args:
        data: Request body
        expected_type: Expected resource type

    Raises:
        ValidationError: If request structure is invalid
    """
    if "data" not in data:
        raise ValidationError(400, "INVALID_REQUEST", "Missing 'data' field")

    if data["data"].get("type") != expected_type:
        raise ValidationError(
            400,
            "INVALID_TYPE",
            f"Expected type '{expected_type}', got '{data['data'].get('type')}'",
        )


def validate_subscription_price_request(data: dict[str, Any]) -> None:
    """Validate subscription price creation request.

    Args:
        data: Request body

    Raises:
        ValidationError: If request is invalid
    """
    validate_json_api_request(data, "subscriptionPrices")

    relationships = data.get("data", {}).get("relationships", {})

    if "subscription" not in relationships:
        raise ValidationError(
            400, "MISSING_RELATIONSHIP", "Missing required relationship: subscription"
        )
    if "subscriptionPricePoint" not in relationships:
        raise ValidationError(
            400,
            "MISSING_RELATIONSHIP",
            "Missing required relationship: subscriptionPricePoint",
        )


def validate_introductory_offer_request(
    data: dict[str, Any],
    subscription_period: str | None,
) -> None:
    """Validate introductory offer creation request.

    Args:
        data: Request body
        subscription_period: Current subscription period (None if not set)

    Raises:
        ValidationError: If request is invalid
    """
    validate_json_api_request(data, "subscriptionIntroductoryOffers")

    attrs = data.get("data", {}).get("attributes", {})

    # Validate required attributes
    required = ["duration", "offerMode", "numberOfPeriods"]
    for field in required:
        if field not in attrs:
            raise ValidationError(400, "MISSING_ATTRIBUTE", f"Missing required attribute: {field}")

    # Validate subscription has period set
    if subscription_period is None:
        raise ValidationError(
            409,
            "ENTITY_ERROR.RELATIONSHIP.INVALID",
            "Subscription duration must be set before creating offers",
        )

    # Validate relationships
    relationships = data.get("data", {}).get("relationships", {})
    if "subscription" not in relationships:
        raise ValidationError(
            400, "MISSING_RELATIONSHIP", "Missing required relationship: subscription"
        )
    if "territory" not in relationships:
        raise ValidationError(
            400, "MISSING_RELATIONSHIP", "Missing required relationship: territory"
        )

    # Validate offer mode
    valid_modes = ["FREE_TRIAL", "PAY_AS_YOU_GO", "PAY_UP_FRONT"]
    if attrs.get("offerMode") not in valid_modes:
        raise ValidationError(
            400,
            "INVALID_ATTRIBUTE",
            f"Invalid offerMode. Must be one of: {', '.join(valid_modes)}",
        )

    # Validate duration
    valid_durations = [
        "THREE_DAYS",
        "ONE_WEEK",
        "TWO_WEEKS",
        "ONE_MONTH",
        "TWO_MONTHS",
        "THREE_MONTHS",
        "SIX_MONTHS",
        "ONE_YEAR",
    ]
    if attrs.get("duration") not in valid_durations:
        raise ValidationError(
            400,
            "INVALID_ATTRIBUTE",
            f"Invalid duration. Must be one of: {', '.join(valid_durations)}",
        )

    # Validate price point required for paid offers
    if (
        attrs.get("offerMode") in ["PAY_AS_YOU_GO", "PAY_UP_FRONT"]
        and "subscriptionPricePoint" not in relationships
    ):
        raise ValidationError(
            400,
            "MISSING_RELATIONSHIP",
            "subscriptionPricePoint is required for paid offers",
        )


def validate_subscription_availability_request(data: dict[str, Any]) -> None:
    """Validate subscription availability request.

    Args:
        data: Request body

    Raises:
        ValidationError: If request is invalid
    """
    validate_json_api_request(data, "subscriptionAvailabilities")

    relationships = data.get("data", {}).get("relationships", {})

    if "subscription" not in relationships:
        raise ValidationError(
            400, "MISSING_RELATIONSHIP", "Missing required relationship: subscription"
        )
    if "availableTerritories" not in relationships:
        raise ValidationError(
            400,
            "MISSING_RELATIONSHIP",
            "Missing required relationship: availableTerritories",
        )


def validate_duration_for_period(
    duration: str,
    subscription_period: str,
) -> None:
    """Validate offer duration is valid for subscription period.

    Based on Apple's documented constraints in ref/app-store-connect-api.md.

    Args:
        duration: Offer duration
        subscription_period: Subscription billing period

    Raises:
        ValidationError: If duration is not valid for the period
    """
    # Duration constraints by subscription period
    # EXACT constraints from Apple API documentation (ref/app-store-connect-api.md lines 91-100)
    valid_durations: dict[str, list[str]] = {
        "ONE_WEEK": ["THREE_DAYS"],
        "ONE_MONTH": ["ONE_WEEK", "TWO_WEEKS", "ONE_MONTH", "TWO_MONTHS", "THREE_MONTHS"],
        "TWO_MONTHS": ["ONE_MONTH", "TWO_MONTHS", "THREE_MONTHS", "SIX_MONTHS"],
        "THREE_MONTHS": ["ONE_MONTH", "TWO_MONTHS", "THREE_MONTHS", "SIX_MONTHS"],
        "SIX_MONTHS": ["ONE_MONTH", "THREE_MONTHS", "SIX_MONTHS"],
        "ONE_YEAR": [
            "ONE_WEEK",
            "ONE_MONTH",
            "TWO_MONTHS",
            "THREE_MONTHS",
            "SIX_MONTHS",
            "ONE_YEAR",
        ],
    }

    allowed = valid_durations.get(subscription_period, [])
    if duration not in allowed:
        raise ValidationError(
            400,
            "INVALID_ATTRIBUTE",
            f"Duration '{duration}' is not valid for subscription period "
            f"'{subscription_period}'. Valid durations: {', '.join(allowed)}",
        )
