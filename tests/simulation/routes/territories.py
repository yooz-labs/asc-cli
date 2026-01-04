"""Route handlers for territories endpoints."""

from typing import TYPE_CHECKING

import httpx

from tests.simulation.responses import build_resource, build_response

if TYPE_CHECKING:
    from tests.simulation.state import StateManager


def handle_list_territories(
    request: httpx.Request,
    state: "StateManager",
) -> httpx.Response:
    """Handle GET /territories.

    Returns all territories from state.
    """
    territories = list(state.territories.values())

    data = [build_resource("territories", t["id"], t.get("attributes", {})) for t in territories]

    return httpx.Response(200, json=build_response(data))
