"""State management for API simulation.

Maintains in-memory state that persists across requests within a test
but resets between tests.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StateManager:
    """In-memory state for simulated API."""

    # Core entities keyed by ID
    apps: dict[str, dict[str, Any]] = field(default_factory=dict)
    subscription_groups: dict[str, dict[str, Any]] = field(default_factory=dict)
    subscriptions: dict[str, dict[str, Any]] = field(default_factory=dict)
    subscription_prices: dict[str, dict[str, Any]] = field(default_factory=dict)
    subscription_price_points: dict[str, dict[str, Any]] = field(default_factory=dict)
    introductory_offers: dict[str, dict[str, Any]] = field(default_factory=dict)
    subscription_availabilities: dict[str, dict[str, Any]] = field(default_factory=dict)
    subscription_localizations: dict[str, dict[str, Any]] = field(default_factory=dict)
    territories: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Relationships (parent_id -> child_ids)
    app_subscription_groups: dict[str, list[str]] = field(default_factory=dict)
    group_subscriptions: dict[str, list[str]] = field(default_factory=dict)
    subscription_prices_map: dict[str, list[str]] = field(default_factory=dict)
    subscription_offers_map: dict[str, list[str]] = field(default_factory=dict)
    subscription_localizations_map: dict[str, list[str]] = field(default_factory=dict)
    subscription_availability_territories: dict[str, list[str]] = field(default_factory=dict)

    # Counters for ID generation
    _id_counter: int = 1000

    def next_id(self, prefix: str = "") -> str:
        """Generate next unique ID."""
        self._id_counter += 1
        return f"{prefix}{self._id_counter}"

    def reset(self) -> None:
        """Reset all state to empty."""
        self.apps.clear()
        self.subscription_groups.clear()
        self.subscriptions.clear()
        self.subscription_prices.clear()
        self.subscription_price_points.clear()
        self.introductory_offers.clear()
        self.subscription_availabilities.clear()
        self.subscription_localizations.clear()
        self.territories.clear()

        self.app_subscription_groups.clear()
        self.group_subscriptions.clear()
        self.subscription_prices_map.clear()
        self.subscription_offers_map.clear()
        self.subscription_localizations_map.clear()
        self.subscription_availability_territories.clear()

        self._id_counter = 1000

    def add_app(
        self,
        app_id: str,
        bundle_id: str,
        name: str,
        sku: str | None = None,
        primary_locale: str = "en-US",
        content_rights_declaration: str = "USES_THIRD_PARTY_CONTENT",
        **extra_attrs: Any,
    ) -> dict[str, Any]:
        """Add an app to state with all required attributes."""
        app = {
            "id": app_id,
            "type": "apps",
            "attributes": {
                "bundleId": bundle_id,
                "name": name,
                "sku": sku or app_id,
                "primaryLocale": primary_locale,
                "contentRightsDeclaration": content_rights_declaration,
                # Subscription webhook URLs
                "subscriptionStatusUrl": None,
                "subscriptionStatusUrlForSandbox": None,
                "subscriptionStatusUrlVersion": None,
                "subscriptionStatusUrlVersionForSandbox": None,
                # Additional app settings
                "isOrEverWasMadeForKids": False,
                "streamlinedPurchasingEnabled": False,
                "accessibilityUrl": None,
                **extra_attrs,
            },
        }
        self.apps[app_id] = app
        return app

    def add_subscription_group(
        self,
        group_id: str,
        app_id: str,
        reference_name: str,
        **extra_attrs: Any,
    ) -> dict[str, Any]:
        """Add a subscription group to state."""
        group = {
            "id": group_id,
            "type": "subscriptionGroups",
            "attributes": {
                "referenceName": reference_name,
                **extra_attrs,
            },
        }
        self.subscription_groups[group_id] = group
        self.app_subscription_groups.setdefault(app_id, []).append(group_id)
        return group

    def add_subscription(
        self,
        subscription_id: str,
        group_id: str,
        product_id: str,
        name: str,
        state: str = "MISSING_METADATA",
        subscription_period: str | None = None,
        family_sharable: bool = True,
        group_level: int = 1,
        review_note: str | None = None,
        **extra_attrs: Any,
    ) -> dict[str, Any]:
        """Add a subscription to state with all required attributes."""
        subscription = {
            "id": subscription_id,
            "type": "subscriptions",
            "attributes": {
                "productId": product_id,
                "name": name,
                "state": state,
                "subscriptionPeriod": subscription_period,
                "familySharable": family_sharable,
                "groupLevel": group_level,
                "reviewNote": review_note,
                **extra_attrs,
            },
        }
        self.subscriptions[subscription_id] = subscription
        self.group_subscriptions.setdefault(group_id, []).append(subscription_id)
        return subscription

    def add_subscription_localization(
        self,
        localization_id: str,
        subscription_id: str,
        locale: str,
        name: str,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Add a subscription localization to state."""
        localization = {
            "id": localization_id,
            "type": "subscriptionLocalizations",
            "attributes": {
                "locale": locale,
                "name": name,
                "description": description,
            },
        }
        self.subscription_localizations[localization_id] = localization
        self.subscription_localizations_map.setdefault(subscription_id, []).append(localization_id)
        return localization

    def add_price_point(
        self,
        price_point_id: str,
        subscription_id: str,
        territory_id: str,
        customer_price: str,
        proceeds: str,
    ) -> dict[str, Any]:
        """Add a subscription price point to state."""
        price_point = {
            "id": price_point_id,
            "type": "subscriptionPricePoints",
            "attributes": {
                "customerPrice": customer_price,
                "proceeds": proceeds,
            },
            "relationships": {
                "territory": {
                    "data": {"type": "territories", "id": territory_id},
                },
            },
        }
        self.subscription_price_points[price_point_id] = price_point
        return price_point

    def add_subscription_price(
        self,
        price_id: str,
        subscription_id: str,
        price_point_id: str,
        start_date: str | None = None,
        preserved: bool = False,
    ) -> dict[str, Any]:
        """Add a subscription price to state."""
        price = {
            "id": price_id,
            "type": "subscriptionPrices",
            "attributes": {
                "startDate": start_date,
                "preserved": preserved,
            },
            "relationships": {
                "subscription": {
                    "data": {"type": "subscriptions", "id": subscription_id},
                },
                "subscriptionPricePoint": {
                    "data": {"type": "subscriptionPricePoints", "id": price_point_id},
                },
            },
        }
        self.subscription_prices[price_id] = price
        self.subscription_prices_map.setdefault(subscription_id, []).append(price_id)
        return price

    def add_introductory_offer(
        self,
        offer_id: str,
        subscription_id: str,
        territory_id: str,
        offer_mode: str,
        duration: str,
        number_of_periods: int = 1,
        price_point_id: str | None = None,
    ) -> dict[str, Any]:
        """Add an introductory offer to state."""
        offer = {
            "id": offer_id,
            "type": "subscriptionIntroductoryOffers",
            "attributes": {
                "offerMode": offer_mode,
                "duration": duration,
                "numberOfPeriods": number_of_periods,
            },
            "relationships": {
                "subscription": {
                    "data": {"type": "subscriptions", "id": subscription_id},
                },
                "territory": {
                    "data": {"type": "territories", "id": territory_id},
                },
            },
        }
        if price_point_id:
            offer["relationships"]["subscriptionPricePoint"] = {
                "data": {"type": "subscriptionPricePoints", "id": price_point_id},
            }
        self.introductory_offers[offer_id] = offer
        self.subscription_offers_map.setdefault(subscription_id, []).append(offer_id)
        return offer

    def set_subscription_availability(
        self,
        subscription_id: str,
        territory_ids: list[str],
        available_in_new_territories: bool = True,
    ) -> dict[str, Any]:
        """Set subscription availability for territories."""
        availability_id = f"avail_{subscription_id}"
        availability = {
            "id": availability_id,
            "type": "subscriptionAvailabilities",
            "attributes": {
                "availableInNewTerritories": available_in_new_territories,
            },
            "relationships": {
                "subscription": {
                    "data": {"type": "subscriptions", "id": subscription_id},
                },
                "availableTerritories": {
                    "data": [{"type": "territories", "id": tid} for tid in territory_ids],
                },
            },
        }
        self.subscription_availabilities[availability_id] = availability
        self.subscription_availability_territories[subscription_id] = territory_ids
        return availability

    def get_subscription_availability_territories(self, subscription_id: str) -> list[str]:
        """Get territories where subscription is available."""
        return self.subscription_availability_territories.get(subscription_id, [])

    def delete_introductory_offer(self, offer_id: str) -> bool:
        """Delete an introductory offer."""
        if offer_id not in self.introductory_offers:
            return False

        offer = self.introductory_offers.pop(offer_id)
        subscription_id = offer["relationships"]["subscription"]["data"]["id"]

        if subscription_id in self.subscription_offers_map:
            offers = self.subscription_offers_map[subscription_id]
            if offer_id in offers:
                offers.remove(offer_id)

        return True
