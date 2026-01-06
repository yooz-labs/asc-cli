"""Core API simulation engine using respx.

The ASCSimulator intercepts httpx calls and returns realistic responses
based on Apple's documented API behavior.
"""

import re
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

import httpx
import respx

from tests.simulation.responses import build_rate_limit_error
from tests.simulation.routes.apps import handle_get_app, handle_list_apps
from tests.simulation.routes.offers import (
    handle_create_introductory_offer,
    handle_delete_introductory_offer,
    handle_list_introductory_offers,
)
from tests.simulation.routes.pricing import (
    handle_create_subscription_price,
    handle_list_price_point_equalizations,
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
    handle_update_subscription,
)
from tests.simulation.routes.territories import handle_list_territories
from tests.simulation.routes.testflight import (
    handle_add_beta_tester_to_groups,
    handle_add_builds_to_beta_group,
    handle_create_app_encryption_declaration,
    handle_create_beta_app_review_submission,
    handle_create_beta_build_localization,
    handle_create_beta_group,
    handle_create_beta_tester,
    handle_delete_beta_group,
    handle_delete_beta_tester,
    handle_get_beta_group,
    handle_get_beta_tester,
    handle_get_build_beta_details,
    handle_get_build_encryption_declaration,
    handle_list_beta_build_localizations,
    handle_list_beta_groups,
    handle_list_beta_testers,
    handle_list_builds,
    handle_remove_beta_tester_from_groups,
    handle_update_beta_build_localization,
    handle_update_beta_group,
    handle_update_build_beta_details,
)
from tests.simulation.state import StateManager


class ASCSimulator:
    """App Store Connect API simulator using respx.

    Usage:
        simulator = ASCSimulator()
        simulator.state.add_app("app_1", "com.example.app", "My App")

        with simulator.mock_context():
            client = AppStoreConnectClient()
            apps = await client.list_apps()
    """

    BASE_URL = "https://api.appstoreconnect.apple.com/v1"

    def __init__(self) -> None:
        self.state = StateManager()
        self._rate_limit_remaining = 350
        self._force_rate_limit = False
        self._error_overrides: dict[str, tuple[int, str, str]] = {}
        self._mock: respx.MockRouter | None = None

    def reset(self) -> None:
        """Reset simulator to initial state."""
        self.state.reset()
        self._rate_limit_remaining = 350
        self._force_rate_limit = False
        self._error_overrides.clear()

    def simulate_rate_limit(self) -> None:
        """Force next request to return 429 rate limit error."""
        self._force_rate_limit = True

    def simulate_error(
        self,
        endpoint_pattern: str,
        status: int,
        code: str,
        message: str,
    ) -> None:
        """Force specific endpoint to return an error.

        Args:
            endpoint_pattern: Regex pattern to match endpoint
            status: HTTP status code
            code: Error code
            message: Error message
        """
        self._error_overrides[endpoint_pattern] = (status, code, message)

    def clear_error_overrides(self) -> None:
        """Clear all error overrides."""
        self._error_overrides.clear()

    def _check_rate_limit(self) -> httpx.Response | None:
        """Check if rate limit should be enforced."""
        if self._force_rate_limit:
            self._force_rate_limit = False
            return httpx.Response(
                429,
                json=build_rate_limit_error(),
                headers={"Retry-After": "60"},
            )
        return None

    def _check_error_override(self, path: str) -> httpx.Response | None:
        """Check if an error override matches this path."""
        for pattern, (status, code, message) in self._error_overrides.items():
            if re.match(pattern, path):
                from tests.simulation.responses import build_error_response

                return httpx.Response(
                    status,
                    json=build_error_response(status, code, code, message),
                )
        return None

    def _wrap_handler(
        self,
        handler: Callable[..., httpx.Response],
        **kwargs: Any,
    ) -> Callable[[httpx.Request], httpx.Response]:
        """Wrap a route handler with rate limit and error checks."""

        def wrapped(request: httpx.Request) -> httpx.Response:
            # Check rate limit
            rate_limit_response = self._check_rate_limit()
            if rate_limit_response:
                return rate_limit_response

            # Check error overrides
            error_response = self._check_error_override(request.url.path)
            if error_response:
                return error_response

            # Call actual handler
            return handler(request, self.state, **kwargs)

        return wrapped

    def _wrap_handler_with_id(
        self,
        handler: Callable[..., httpx.Response],
        id_param: str,
    ) -> Callable[[httpx.Request, str], httpx.Response]:
        """Wrap a route handler that takes an ID parameter."""

        def wrapped(request: httpx.Request, **route_kwargs: str) -> httpx.Response:
            # Check rate limit
            rate_limit_response = self._check_rate_limit()
            if rate_limit_response:
                return rate_limit_response

            # Check error overrides
            error_response = self._check_error_override(request.url.path)
            if error_response:
                return error_response

            # Get ID from route kwargs
            resource_id = route_kwargs.get(id_param, "")

            # Call actual handler
            return handler(request, self.state, resource_id)

        return wrapped

    def _wrap_post_handler(
        self,
        handler: Callable[..., httpx.Response],
    ) -> Callable[[httpx.Request], httpx.Response]:
        """Wrap a POST handler."""

        def wrapped(request: httpx.Request) -> httpx.Response:
            # Check rate limit
            rate_limit_response = self._check_rate_limit()
            if rate_limit_response:
                return rate_limit_response

            # Check error overrides
            error_response = self._check_error_override(request.url.path)
            if error_response:
                return error_response

            # Call actual handler
            return handler(request, self.state)

        return wrapped

    @contextmanager
    def mock_context(self):
        """Context manager that mocks the ASC API.

        Usage:
            with simulator.mock_context():
                # All httpx requests to ASC API are intercepted
                client = AppStoreConnectClient()
                apps = await client.list_apps()
        """
        with respx.mock(assert_all_called=False) as mock:
            self._mock = mock

            # Register all routes
            self._register_routes(mock)

            yield self

        self._mock = None

    def _register_routes(self, mock: respx.MockRouter) -> None:
        """Register all API routes with the mock router."""

        # Apps
        mock.get(f"{self.BASE_URL}/apps").mock(side_effect=self._wrap_handler(handle_list_apps))
        mock.get(url__regex=rf"{re.escape(self.BASE_URL)}/apps/(?P<app_id>[^/]+)$").mock(
            side_effect=self._wrap_handler_with_id(handle_get_app, "app_id")
        )

        # Subscription Groups
        mock.get(
            url__regex=rf"{re.escape(self.BASE_URL)}/apps/(?P<app_id>[^/]+)/subscriptionGroups$"
        ).mock(side_effect=self._wrap_handler_with_id(handle_list_subscription_groups, "app_id"))

        # Subscriptions
        mock.get(
            url__regex=rf"{re.escape(self.BASE_URL)}/subscriptionGroups/(?P<group_id>[^/]+)/subscriptions$"
        ).mock(side_effect=self._wrap_handler_with_id(handle_list_subscriptions, "group_id"))
        mock.get(
            url__regex=rf"{re.escape(self.BASE_URL)}/subscriptions/(?P<subscription_id>[^/]+)$"
        ).mock(side_effect=self._wrap_handler_with_id(handle_get_subscription, "subscription_id"))
        mock.patch(
            url__regex=rf"{re.escape(self.BASE_URL)}/subscriptions/(?P<subscription_id>[^/]+)$"
        ).mock(
            side_effect=self._wrap_handler_with_id(handle_update_subscription, "subscription_id")
        )

        # Subscription Localizations
        mock.get(
            url__regex=rf"{re.escape(self.BASE_URL)}/subscriptions/(?P<subscription_id>[^/]+)/subscriptionLocalizations$"
        ).mock(
            side_effect=self._wrap_handler_with_id(
                handle_list_subscription_localizations, "subscription_id"
            )
        )

        # Subscription Availability
        mock.get(
            url__regex=rf"{re.escape(self.BASE_URL)}/subscriptions/(?P<subscription_id>[^/]+)/subscriptionAvailability"
        ).mock(
            side_effect=self._wrap_handler_with_id(
                handle_get_subscription_availability, "subscription_id"
            )
        )
        mock.post(f"{self.BASE_URL}/subscriptionAvailabilities").mock(
            side_effect=self._wrap_post_handler(handle_create_subscription_availability)
        )

        # Price Points
        mock.get(
            url__regex=rf"{re.escape(self.BASE_URL)}/subscriptions/(?P<subscription_id>[^/]+)/pricePoints"
        ).mock(side_effect=self._wrap_handler_with_id(handle_list_price_points, "subscription_id"))
        mock.get(
            url__regex=rf"{re.escape(self.BASE_URL)}/subscriptionPricePoints/(?P<price_point_id>[^/]+)/equalizations"
        ).mock(
            side_effect=self._wrap_handler_with_id(
                handle_list_price_point_equalizations, "price_point_id"
            )
        )

        # Subscription Prices
        mock.get(
            url__regex=rf"{re.escape(self.BASE_URL)}/subscriptions/(?P<subscription_id>[^/]+)/prices"
        ).mock(
            side_effect=self._wrap_handler_with_id(
                handle_list_subscription_prices, "subscription_id"
            )
        )
        mock.post(f"{self.BASE_URL}/subscriptionPrices").mock(
            side_effect=self._wrap_post_handler(handle_create_subscription_price)
        )

        # Introductory Offers
        mock.get(
            url__regex=rf"{re.escape(self.BASE_URL)}/subscriptions/(?P<subscription_id>[^/]+)/introductoryOffers"
        ).mock(
            side_effect=self._wrap_handler_with_id(
                handle_list_introductory_offers, "subscription_id"
            )
        )
        mock.post(f"{self.BASE_URL}/subscriptionIntroductoryOffers").mock(
            side_effect=self._wrap_post_handler(handle_create_introductory_offer)
        )
        mock.delete(
            url__regex=rf"{re.escape(self.BASE_URL)}/subscriptionIntroductoryOffers/(?P<offer_id>[^/]+)$"
        ).mock(side_effect=self._wrap_handler_with_id(handle_delete_introductory_offer, "offer_id"))

        # Territories
        mock.get(f"{self.BASE_URL}/territories").mock(
            side_effect=self._wrap_handler(handle_list_territories)
        )

        # =====================================================================
        # TestFlight Routes
        # =====================================================================

        # Builds - uses /builds with filter[app] query param
        mock.get(url__regex=rf"{re.escape(self.BASE_URL)}/builds(\?.*)?$").mock(
            side_effect=self._wrap_handler(handle_list_builds)
        )

        # Beta Build Localizations
        mock.get(
            url__regex=rf"{re.escape(self.BASE_URL)}/builds/(?P<build_id>[^/]+)/betaBuildLocalizations$"
        ).mock(
            side_effect=self._wrap_handler_with_id(handle_list_beta_build_localizations, "build_id")
        )
        mock.post(f"{self.BASE_URL}/betaBuildLocalizations").mock(
            side_effect=self._wrap_post_handler(handle_create_beta_build_localization)
        )
        mock.patch(
            url__regex=rf"{re.escape(self.BASE_URL)}/betaBuildLocalizations/(?P<localization_id>[^/]+)$"
        ).mock(
            side_effect=self._wrap_handler_with_id(
                handle_update_beta_build_localization, "localization_id"
            )
        )

        # App Encryption Declarations
        mock.get(
            url__regex=rf"{re.escape(self.BASE_URL)}/builds/(?P<build_id>[^/]+)/appEncryptionDeclaration$"
        ).mock(
            side_effect=self._wrap_handler_with_id(
                handle_get_build_encryption_declaration, "build_id"
            )
        )
        mock.post(f"{self.BASE_URL}/appEncryptionDeclarations").mock(
            side_effect=self._wrap_post_handler(handle_create_app_encryption_declaration)
        )

        # Beta App Review Submissions
        mock.post(f"{self.BASE_URL}/betaAppReviewSubmissions").mock(
            side_effect=self._wrap_post_handler(handle_create_beta_app_review_submission)
        )

        # Beta Groups - allow query params with (\?.*)?
        mock.get(
            url__regex=rf"{re.escape(self.BASE_URL)}/apps/(?P<app_id>[^/]+)/betaGroups(\?.*)?$"
        ).mock(side_effect=self._wrap_handler_with_id(handle_list_beta_groups, "app_id"))
        mock.get(url__regex=rf"{re.escape(self.BASE_URL)}/betaGroups/(?P<group_id>[^/]+)$").mock(
            side_effect=self._wrap_handler_with_id(handle_get_beta_group, "group_id")
        )
        mock.post(f"{self.BASE_URL}/betaGroups").mock(
            side_effect=self._wrap_post_handler(handle_create_beta_group)
        )
        mock.patch(url__regex=rf"{re.escape(self.BASE_URL)}/betaGroups/(?P<group_id>[^/]+)$").mock(
            side_effect=self._wrap_handler_with_id(handle_update_beta_group, "group_id")
        )
        mock.delete(url__regex=rf"{re.escape(self.BASE_URL)}/betaGroups/(?P<group_id>[^/]+)$").mock(
            side_effect=self._wrap_handler_with_id(handle_delete_beta_group, "group_id")
        )
        mock.post(
            url__regex=rf"{re.escape(self.BASE_URL)}/betaGroups/(?P<group_id>[^/]+)/relationships/builds$"
        ).mock(side_effect=self._wrap_handler_with_id(handle_add_builds_to_beta_group, "group_id"))

        # Beta Testers
        mock.get(f"{self.BASE_URL}/betaTesters").mock(
            side_effect=self._wrap_handler(handle_list_beta_testers)
        )
        mock.get(url__regex=rf"{re.escape(self.BASE_URL)}/betaTesters/(?P<tester_id>[^/]+)$").mock(
            side_effect=self._wrap_handler_with_id(handle_get_beta_tester, "tester_id")
        )
        mock.post(f"{self.BASE_URL}/betaTesters").mock(
            side_effect=self._wrap_post_handler(handle_create_beta_tester)
        )
        mock.delete(
            url__regex=rf"{re.escape(self.BASE_URL)}/betaTesters/(?P<tester_id>[^/]+)$"
        ).mock(side_effect=self._wrap_handler_with_id(handle_delete_beta_tester, "tester_id"))
        mock.post(
            url__regex=rf"{re.escape(self.BASE_URL)}/betaTesters/(?P<tester_id>[^/]+)/relationships/betaGroups$"
        ).mock(
            side_effect=self._wrap_handler_with_id(handle_add_beta_tester_to_groups, "tester_id")
        )
        mock.delete(
            url__regex=rf"{re.escape(self.BASE_URL)}/betaTesters/(?P<tester_id>[^/]+)/relationships/betaGroups$"
        ).mock(
            side_effect=self._wrap_handler_with_id(
                handle_remove_beta_tester_from_groups, "tester_id"
            )
        )

        # Build Beta Details
        mock.get(
            url__regex=rf"{re.escape(self.BASE_URL)}/builds/(?P<build_id>[^/]+)/buildBetaDetail$"
        ).mock(side_effect=self._wrap_handler_with_id(handle_get_build_beta_details, "build_id"))
        mock.patch(
            url__regex=rf"{re.escape(self.BASE_URL)}/buildBetaDetails/(?P<details_id>[^/]+)$"
        ).mock(
            side_effect=self._wrap_handler_with_id(handle_update_build_beta_details, "details_id")
        )
