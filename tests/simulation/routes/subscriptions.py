"""Route handlers for subscription endpoints."""

from typing import TYPE_CHECKING

import httpx

from tests.simulation.responses import (
    build_not_found_error,
    build_relationship,
    build_relationship_list,
    build_resource,
    build_response,
)
from tests.simulation.validators import (
    ValidationError,
    validate_subscription_availability_request,
)

if TYPE_CHECKING:
    from tests.simulation.state import StateManager


def handle_list_subscription_groups(
    request: httpx.Request,
    state: "StateManager",
    app_id: str,
) -> httpx.Response:
    """Handle GET /apps/{app_id}/subscriptionGroups."""
    if app_id not in state.apps:
        return httpx.Response(404, json=build_not_found_error("App", app_id))

    group_ids = state.app_subscription_groups.get(app_id, [])
    groups = [
        state.subscription_groups[gid] for gid in group_ids if gid in state.subscription_groups
    ]

    data = []
    for group in groups:
        group_id = group["id"]
        # Build relationships - link to app and subscriptions
        subscription_ids = state.group_subscriptions.get(group_id, [])
        relationships = {
            "app": build_relationship("apps", app_id),
            "subscriptions": build_relationship_list("subscriptions", subscription_ids),
        }
        data.append(
            build_resource("subscriptionGroups", group_id, group["attributes"], relationships)
        )

    return httpx.Response(200, json=build_response(data))


def handle_list_subscriptions(
    request: httpx.Request,
    state: "StateManager",
    group_id: str,
) -> httpx.Response:
    """Handle GET /subscriptionGroups/{group_id}/subscriptions."""
    if group_id not in state.subscription_groups:
        return httpx.Response(404, json=build_not_found_error("SubscriptionGroup", group_id))

    subscription_ids = state.group_subscriptions.get(group_id, [])
    subscriptions = [
        state.subscriptions[sid] for sid in subscription_ids if sid in state.subscriptions
    ]

    data = []
    for subscription in subscriptions:
        sub_id = subscription["id"]
        # Build relationships - link to group, localizations, prices, etc
        localization_ids = state.subscription_localizations_map.get(sub_id, [])
        relationships = {
            "subscriptionGroup": build_relationship("subscriptionGroups", group_id),
            "subscriptionLocalizations": build_relationship_list(
                "subscriptionLocalizations", localization_ids
            ),
        }
        data.append(
            build_resource("subscriptions", sub_id, subscription["attributes"], relationships)
        )

    return httpx.Response(200, json=build_response(data))


def handle_get_subscription(
    request: httpx.Request,
    state: "StateManager",
    subscription_id: str,
) -> httpx.Response:
    """Handle GET /subscriptions/{subscription_id}."""
    if subscription_id not in state.subscriptions:
        return httpx.Response(404, json=build_not_found_error("Subscription", subscription_id))

    subscription = state.subscriptions[subscription_id]

    # Find the group this subscription belongs to
    group_id = None
    for gid, sub_ids in state.group_subscriptions.items():
        if subscription_id in sub_ids:
            group_id = gid
            break

    # Build relationships
    localization_ids = state.subscription_localizations_map.get(subscription_id, [])
    relationships = {
        "subscriptionLocalizations": build_relationship_list(
            "subscriptionLocalizations", localization_ids
        ),
    }
    if group_id:
        relationships["subscriptionGroup"] = build_relationship("subscriptionGroups", group_id)

    return httpx.Response(
        200,
        json=build_response(
            build_resource(
                "subscriptions", subscription_id, subscription["attributes"], relationships
            )
        ),
    )


def handle_update_subscription(
    request: httpx.Request,
    state: "StateManager",
    subscription_id: str,
) -> httpx.Response:
    """Handle PATCH /subscriptions/{subscription_id}.

    Primarily used to set subscriptionPeriod. Once set, period cannot be changed.
    """
    if subscription_id not in state.subscriptions:
        return httpx.Response(404, json=build_not_found_error("Subscription", subscription_id))

    try:
        data = request.json() if hasattr(request, "json") else {}
        if callable(data):
            data = data()
    except Exception:
        from tests.simulation.responses import build_error_response

        return httpx.Response(
            400,
            json=build_error_response(400, "INVALID_REQUEST", "Bad Request", "Invalid JSON"),
        )

    # Validate JSON:API structure
    if "data" not in data or data["data"].get("type") != "subscriptions":
        from tests.simulation.responses import build_error_response

        return httpx.Response(
            400,
            json=build_error_response(
                400, "INVALID_REQUEST", "Bad Request", "Invalid request structure"
            ),
        )

    if data["data"].get("id") != subscription_id:
        from tests.simulation.responses import build_error_response

        return httpx.Response(
            400,
            json=build_error_response(
                400, "INVALID_REQUEST", "Bad Request", "ID mismatch in request"
            ),
        )

    subscription = state.subscriptions[subscription_id]
    attrs = data["data"].get("attributes", {})

    # Handle subscriptionPeriod update
    if "subscriptionPeriod" in attrs:
        new_period = attrs["subscriptionPeriod"]
        current_period = subscription["attributes"].get("subscriptionPeriod")

        # Check if period is already set and trying to change it
        if current_period and current_period != new_period:
            from tests.simulation.responses import build_error_response

            return httpx.Response(
                409,
                json=build_error_response(
                    409,
                    "ENTITY_ERROR.ATTRIBUTE.INVALID",
                    "Entity Error",
                    f"Subscription period cannot be changed once set. "
                    f"Current: {current_period}, Requested: {new_period}",
                ),
            )

        # Validate period value
        valid_periods = [
            "ONE_WEEK",
            "ONE_MONTH",
            "TWO_MONTHS",
            "THREE_MONTHS",
            "SIX_MONTHS",
            "ONE_YEAR",
        ]
        if new_period not in valid_periods:
            from tests.simulation.responses import build_error_response

            return httpx.Response(
                400,
                json=build_error_response(
                    400,
                    "INVALID_ATTRIBUTE",
                    "Invalid Attribute",
                    f"Invalid subscriptionPeriod: {new_period}. "
                    f"Valid values: {', '.join(valid_periods)}",
                ),
            )

        # Set the period
        subscription["attributes"]["subscriptionPeriod"] = new_period

    # Build relationships for response
    group_id = None
    for gid, sub_ids in state.group_subscriptions.items():
        if subscription_id in sub_ids:
            group_id = gid
            break

    localization_ids = state.subscription_localizations_map.get(subscription_id, [])
    relationships = {
        "subscriptionLocalizations": build_relationship_list(
            "subscriptionLocalizations", localization_ids
        ),
    }
    if group_id:
        relationships["subscriptionGroup"] = build_relationship("subscriptionGroups", group_id)

    return httpx.Response(
        200,
        json=build_response(
            build_resource(
                "subscriptions", subscription_id, subscription["attributes"], relationships
            )
        ),
    )


def handle_list_subscription_localizations(
    request: httpx.Request,
    state: "StateManager",
    subscription_id: str,
) -> httpx.Response:
    """Handle GET /subscriptions/{subscription_id}/subscriptionLocalizations."""
    if subscription_id not in state.subscriptions:
        return httpx.Response(404, json=build_not_found_error("Subscription", subscription_id))

    localization_ids = state.subscription_localizations_map.get(subscription_id, [])
    localizations = [
        state.subscription_localizations[lid]
        for lid in localization_ids
        if lid in state.subscription_localizations
    ]

    data = [
        build_resource("subscriptionLocalizations", loc["id"], loc["attributes"])
        for loc in localizations
    ]
    return httpx.Response(200, json=build_response(data))


def handle_get_subscription_availability(
    request: httpx.Request,
    state: "StateManager",
    subscription_id: str,
) -> httpx.Response:
    """Handle GET /subscriptions/{subscription_id}/subscriptionAvailability."""
    if subscription_id not in state.subscriptions:
        return httpx.Response(404, json=build_not_found_error("Subscription", subscription_id))

    availability_id = f"avail_{subscription_id}"

    if availability_id not in state.subscription_availabilities:
        # No availability set yet - return empty
        return httpx.Response(200, json=build_response(None))

    availability = state.subscription_availabilities[availability_id]

    # Check if include=availableTerritories is requested
    params = dict(request.url.params)
    include = params.get("include", "")

    included = None
    if "availableTerritories" in include:
        territory_ids = state.subscription_availability_territories.get(subscription_id, [])
        included = [
            build_resource(
                "territories",
                tid,
                state.territories.get(tid, {}).get("attributes", {}),
            )
            for tid in territory_ids
            if tid in state.territories
        ]

    return httpx.Response(
        200,
        json=build_response(
            build_resource(
                "subscriptionAvailabilities",
                availability_id,
                availability["attributes"],
                relationships=availability.get("relationships"),
            ),
            included=included,
        ),
    )


def handle_create_subscription_availability(
    request: httpx.Request,
    state: "StateManager",
) -> httpx.Response:
    """Handle POST /subscriptionAvailabilities."""
    try:
        data = request.json() if hasattr(request, "json") else {}
        if callable(data):
            data = data()
    except Exception:
        data = {}

    try:
        validate_subscription_availability_request(data)
    except ValidationError as e:
        from tests.simulation.responses import build_error_response

        return httpx.Response(
            e.status,
            json=build_error_response(e.status, e.code, e.code, e.detail),
        )

    relationships = data["data"]["relationships"]
    subscription_id = relationships["subscription"]["data"]["id"]

    # Verify subscription exists
    if subscription_id not in state.subscriptions:
        return httpx.Response(404, json=build_not_found_error("Subscription", subscription_id))

    # Extract territory IDs
    territory_data = relationships["availableTerritories"]["data"]
    territory_ids = [t["id"] for t in territory_data]

    # Get attributes
    attrs = data["data"].get("attributes", {})
    available_in_new = attrs.get("availableInNewTerritories", True)

    # Set availability
    availability = state.set_subscription_availability(
        subscription_id=subscription_id,
        territory_ids=territory_ids,
        available_in_new_territories=available_in_new,
    )

    return httpx.Response(
        201,
        json=build_response(
            build_resource(
                "subscriptionAvailabilities",
                availability["id"],
                availability["attributes"],
                relationships=availability.get("relationships"),
            )
        ),
    )
