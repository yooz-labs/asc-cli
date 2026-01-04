"""Route handlers for API simulation.

Each module handles a group of related endpoints.
"""

from tests.simulation.routes.apps import handle_get_app, handle_list_apps
from tests.simulation.routes.offers import (
    handle_create_introductory_offer,
    handle_delete_introductory_offer,
    handle_list_introductory_offers,
)
from tests.simulation.routes.pricing import (
    handle_create_subscription_price,
    handle_list_price_points,
    handle_list_subscription_prices,
)
from tests.simulation.routes.subscriptions import (
    handle_create_subscription_availability,
    handle_get_subscription,
    handle_get_subscription_availability,
    handle_list_subscription_groups,
    handle_list_subscription_localizations,
    handle_list_subscriptions,
)
from tests.simulation.routes.territories import handle_list_territories

__all__ = [
    # Apps
    "handle_list_apps",
    "handle_get_app",
    # Subscriptions
    "handle_list_subscription_groups",
    "handle_list_subscriptions",
    "handle_get_subscription",
    "handle_list_subscription_localizations",
    "handle_get_subscription_availability",
    "handle_create_subscription_availability",
    # Territories
    "handle_list_territories",
    # Pricing
    "handle_list_price_points",
    "handle_list_subscription_prices",
    "handle_create_subscription_price",
    # Offers
    "handle_list_introductory_offers",
    "handle_create_introductory_offer",
    "handle_delete_introductory_offer",
]
