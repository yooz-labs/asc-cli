"""Route handlers for pricing endpoints."""

from typing import TYPE_CHECKING

import httpx

from tests.simulation.responses import (
    build_not_found_error,
    build_resource,
    build_response,
)
from tests.simulation.validators import (
    ValidationError,
    validate_subscription_price_request,
)

if TYPE_CHECKING:
    from tests.simulation.state import StateManager


def handle_list_price_points(
    request: httpx.Request,
    state: "StateManager",
    subscription_id: str,
) -> httpx.Response:
    """Handle GET /subscriptions/{subscription_id}/pricePoints.

    Supports:
        - filter[territory]: Filter by territory ID
        - include=territory: Include territory data
        - limit: Maximum items to return
    """
    if subscription_id not in state.subscriptions:
        return httpx.Response(404, json=build_not_found_error("Subscription", subscription_id))

    params = dict(request.url.params)

    # Get all price points for this subscription
    price_points = list(state.subscription_price_points.values())

    # Apply territory filter
    territory_filter = params.get("filter[territory]")
    if territory_filter:
        price_points = [
            pp
            for pp in price_points
            if pp.get("relationships", {}).get("territory", {}).get("data", {}).get("id")
            == territory_filter
        ]

    # Build response data
    data = []
    included = []
    include_territory = "territory" in params.get("include", "")

    for pp in price_points:
        resource = build_resource(
            "subscriptionPricePoints",
            pp["id"],
            pp["attributes"],
            relationships=pp.get("relationships"),
        )
        data.append(resource)

        # Include territory if requested
        if include_territory:
            territory_id = (
                pp.get("relationships", {}).get("territory", {}).get("data", {}).get("id")
            )
            if territory_id and territory_id in state.territories:
                territory = state.territories[territory_id]
                included.append(
                    build_resource(
                        "territories",
                        territory_id,
                        territory.get("attributes", {}),
                    )
                )

    # Deduplicate included territories
    seen_ids = set()
    unique_included = []
    for item in included:
        if item["id"] not in seen_ids:
            seen_ids.add(item["id"])
            unique_included.append(item)

    return httpx.Response(
        200,
        json=build_response(data, included=unique_included if unique_included else None),
    )


def handle_list_subscription_prices(
    request: httpx.Request,
    state: "StateManager",
    subscription_id: str,
) -> httpx.Response:
    """Handle GET /subscriptions/{subscription_id}/prices."""
    if subscription_id not in state.subscriptions:
        return httpx.Response(404, json=build_not_found_error("Subscription", subscription_id))

    price_ids = state.subscription_prices_map.get(subscription_id, [])
    prices = [
        state.subscription_prices[pid] for pid in price_ids if pid in state.subscription_prices
    ]

    data = [
        build_resource(
            "subscriptionPrices",
            p["id"],
            p["attributes"],
            relationships=p.get("relationships"),
        )
        for p in prices
    ]

    return httpx.Response(200, json=build_response(data))


def handle_create_subscription_price(
    request: httpx.Request,
    state: "StateManager",
) -> httpx.Response:
    """Handle POST /subscriptionPrices."""
    try:
        data = request.json() if hasattr(request, "json") else {}
        if callable(data):
            data = data()
    except Exception:
        data = {}

    try:
        validate_subscription_price_request(data)
    except ValidationError as e:
        from tests.simulation.responses import build_error_response

        return httpx.Response(
            e.status,
            json=build_error_response(e.status, e.code, e.code, e.detail),
        )

    # Extract relationship IDs
    relationships = data["data"]["relationships"]
    subscription_id = relationships["subscription"]["data"]["id"]
    price_point_id = relationships["subscriptionPricePoint"]["data"]["id"]

    # Verify subscription exists
    if subscription_id not in state.subscriptions:
        return httpx.Response(404, json=build_not_found_error("Subscription", subscription_id))

    # Verify price point exists
    if price_point_id not in state.subscription_price_points:
        return httpx.Response(
            404, json=build_not_found_error("SubscriptionPricePoint", price_point_id)
        )

    # Get optional attributes
    attrs = data["data"].get("attributes", {})
    start_date = attrs.get("startDate")
    preserved = attrs.get("preserveCurrentPrice", False)

    # Create price
    price_id = state.next_id("price_")
    price = state.add_subscription_price(
        price_id=price_id,
        subscription_id=subscription_id,
        price_point_id=price_point_id,
        start_date=start_date,
        preserved=preserved,
    )

    return httpx.Response(
        201,
        json=build_response(
            build_resource(
                "subscriptionPrices",
                price_id,
                price["attributes"],
                relationships=price.get("relationships"),
            )
        ),
    )


def handle_list_price_point_equalizations(
    request: httpx.Request,
    state: "StateManager",
    price_point_id: str,
) -> httpx.Response:
    """Handle GET /subscriptionPricePoints/{price_point_id}/equalizations.

    Returns equalized prices for other territories based on the given price point.
    """
    if price_point_id not in state.subscription_price_points:
        return httpx.Response(
            404, json=build_not_found_error("SubscriptionPricePoint", price_point_id)
        )

    # In a real simulation, we'd calculate equalized prices
    # For now, return all other price points as "equalizations"
    base_pp = state.subscription_price_points[price_point_id]
    base_territory = base_pp.get("relationships", {}).get("territory", {}).get("data", {}).get("id")

    equalizations = [
        pp
        for pp in state.subscription_price_points.values()
        if pp["id"] != price_point_id
        and pp.get("relationships", {}).get("territory", {}).get("data", {}).get("id")
        != base_territory
    ]

    data = [
        build_resource(
            "subscriptionPricePoints",
            pp["id"],
            pp["attributes"],
            relationships=pp.get("relationships"),
        )
        for pp in equalizations
    ]

    return httpx.Response(200, json=build_response(data))
