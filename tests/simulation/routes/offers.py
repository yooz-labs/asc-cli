"""Route handlers for introductory offer endpoints."""

from typing import TYPE_CHECKING

import httpx

from tests.simulation.responses import (
    build_error_response,
    build_not_found_error,
    build_resource,
    build_response,
    build_state_error,
)
from tests.simulation.validators import (
    ValidationError,
    validate_duration_for_period,
    validate_introductory_offer_request,
)

if TYPE_CHECKING:
    from tests.simulation.state import StateManager


def handle_list_introductory_offers(
    request: httpx.Request,
    state: "StateManager",
    subscription_id: str,
) -> httpx.Response:
    """Handle GET /subscriptions/{subscription_id}/introductoryOffers."""
    if subscription_id not in state.subscriptions:
        return httpx.Response(404, json=build_not_found_error("Subscription", subscription_id))

    offer_ids = state.subscription_offers_map.get(subscription_id, [])
    offers = [
        state.introductory_offers[oid] for oid in offer_ids if oid in state.introductory_offers
    ]

    data = [
        build_resource(
            "subscriptionIntroductoryOffers",
            o["id"],
            o["attributes"],
            relationships=o.get("relationships"),
        )
        for o in offers
    ]

    return httpx.Response(200, json=build_response(data))


def handle_create_introductory_offer(
    request: httpx.Request,
    state: "StateManager",
) -> httpx.Response:
    """Handle POST /subscriptionIntroductoryOffers."""
    try:
        data = request.json() if hasattr(request, "json") else {}
        if callable(data):
            data = data()
    except Exception as e:
        return httpx.Response(
            400,
            json=build_error_response(
                400,
                "INVALID_REQUEST_BODY",
                "INVALID_REQUEST_BODY",
                f"Invalid JSON in request body: {e}",
            ),
        )

    # Get subscription ID first to check period
    relationships = data.get("data", {}).get("relationships", {})
    subscription_ref = relationships.get("subscription", {}).get("data", {})
    subscription_id = subscription_ref.get("id")

    # Get subscription period
    subscription_period = None
    if subscription_id and subscription_id in state.subscriptions:
        subscription = state.subscriptions[subscription_id]
        subscription_period = subscription["attributes"].get("subscriptionPeriod")

    try:
        validate_introductory_offer_request(data, subscription_period)
    except ValidationError as e:
        return httpx.Response(
            e.status,
            json=build_error_response(e.status, e.code, e.code, e.detail),
        )

    # Verify subscription exists
    if subscription_id not in state.subscriptions:
        return httpx.Response(404, json=build_not_found_error("Subscription", subscription_id))

    # Get offer attributes
    attrs = data["data"]["attributes"]
    duration = attrs["duration"]
    offer_mode = attrs["offerMode"]
    number_of_periods = attrs.get("numberOfPeriods", 1)

    # Validate duration is valid for subscription period
    try:
        validate_duration_for_period(duration, subscription_period)
    except ValidationError as e:
        return httpx.Response(
            e.status,
            json=build_error_response(e.status, e.code, e.code, e.detail),
        )

    # Get territory
    territory_ref = relationships.get("territory", {}).get("data", {})
    territory_id = territory_ref.get("id")

    if not territory_id:
        return httpx.Response(
            400,
            json=build_error_response(
                400,
                "MISSING_RELATIONSHIP",
                "Missing Relationship",
                "Territory is required",
            ),
        )

    # Check for existing offer in same territory
    existing_offers = state.subscription_offers_map.get(subscription_id, [])
    for offer_id in existing_offers:
        if offer_id in state.introductory_offers:
            offer = state.introductory_offers[offer_id]
            offer_territory = (
                offer.get("relationships", {}).get("territory", {}).get("data", {}).get("id")
            )
            if offer_territory == territory_id:
                return httpx.Response(
                    409,
                    json=build_state_error(
                        f"An introductory offer already exists for territory {territory_id}. "
                        "Only one offer per territory is allowed at a time."
                    ),
                )

    # Get optional price point for paid offers
    price_point_id = None
    if offer_mode in ["PAY_AS_YOU_GO", "PAY_UP_FRONT"]:
        price_point_ref = relationships.get("subscriptionPricePoint", {}).get("data", {})
        price_point_id = price_point_ref.get("id")

    # Create offer
    offer_id = state.next_id("offer_")
    offer = state.add_introductory_offer(
        offer_id=offer_id,
        subscription_id=subscription_id,
        territory_id=territory_id,
        offer_mode=offer_mode,
        duration=duration,
        number_of_periods=number_of_periods,
        price_point_id=price_point_id,
    )

    return httpx.Response(
        201,
        json=build_response(
            build_resource(
                "subscriptionIntroductoryOffers",
                offer_id,
                offer["attributes"],
                relationships=offer.get("relationships"),
            )
        ),
    )


def handle_delete_introductory_offer(
    request: httpx.Request,
    state: "StateManager",
    offer_id: str,
) -> httpx.Response:
    """Handle DELETE /subscriptionIntroductoryOffers/{offer_id}."""
    if offer_id not in state.introductory_offers:
        return httpx.Response(
            404, json=build_not_found_error("SubscriptionIntroductoryOffer", offer_id)
        )

    deleted = state.delete_introductory_offer(offer_id)

    if deleted:
        return httpx.Response(204)
    else:
        return httpx.Response(
            404, json=build_not_found_error("SubscriptionIntroductoryOffer", offer_id)
        )
