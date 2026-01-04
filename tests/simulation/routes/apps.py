"""Route handlers for apps endpoints."""

from typing import TYPE_CHECKING

import httpx

from tests.simulation.responses import (
    build_not_found_error,
    build_resource,
    build_response,
)

if TYPE_CHECKING:
    from tests.simulation.state import StateManager


def handle_list_apps(request: httpx.Request, state: "StateManager") -> httpx.Response:
    """Handle GET /apps with optional filters.

    Supports:
        - filter[bundleId]: Filter by bundle ID
    """
    params = dict(request.url.params)

    apps = list(state.apps.values())

    # Apply filter[bundleId] if present
    bundle_id_filter = params.get("filter[bundleId]")
    if bundle_id_filter:
        apps = [a for a in apps if a["attributes"].get("bundleId") == bundle_id_filter]

    data = []
    for app in apps:
        # Note: Real API includes relationships with links only (no data)
        # We omit them for now since we don't have link URLs
        data.append(build_resource("apps", app["id"], app["attributes"]))

    return httpx.Response(200, json=build_response(data))


def handle_get_app(
    request: httpx.Request,
    state: "StateManager",
    app_id: str,
) -> httpx.Response:
    """Handle GET /apps/{id}."""
    if app_id not in state.apps:
        return httpx.Response(404, json=build_not_found_error("App", app_id))

    app = state.apps[app_id]

    # Note: Real API includes relationships with links only (no data)
    # We omit them for now since we don't have link URLs
    return httpx.Response(
        200,
        json=build_response(build_resource("apps", app_id, app["attributes"])),
    )
