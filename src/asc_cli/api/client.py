"""App Store Connect API client."""

from typing import Any

import httpx

from asc_cli.api.auth import AuthManager


class AppStoreConnectClient:
    """HTTP client for App Store Connect API."""

    BASE_URL = "https://api.appstoreconnect.apple.com/v1"

    def __init__(self, auth: AuthManager | None = None) -> None:
        """Initialize client with optional auth manager."""
        self._auth = auth or AuthManager.auto()
        self._client: httpx.AsyncClient | None = None

    @property
    def auth(self) -> AuthManager:
        """Get the auth manager."""
        return self._auth

    def _headers(self) -> dict[str, str]:
        """Get request headers with auth token."""
        return {
            "Authorization": f"Bearer {self._auth.token}",
            "Content-Type": "application/json",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a GET request."""
        client = await self._get_client()
        response = await client.get(
            endpoint,
            headers=self._headers(),
            params=params,
        )
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    async def post(
        self,
        endpoint: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Make a POST request."""
        client = await self._get_client()
        response = await client.post(
            endpoint,
            headers=self._headers(),
            json=data,
        )
        if not response.is_success:
            raise APIError(response.status_code, response.text)
        return response.json()  # type: ignore[no-any-return]

    async def patch(
        self,
        endpoint: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Make a PATCH request."""
        client = await self._get_client()
        response = await client.patch(
            endpoint,
            headers=self._headers(),
            json=data,
        )
        if not response.is_success:
            raise APIError(response.status_code, response.text)
        return response.json()  # type: ignore[no-any-return]

    async def delete(self, endpoint: str) -> bool:
        """Make a DELETE request."""
        client = await self._get_client()
        response = await client.delete(
            endpoint,
            headers=self._headers(),
        )
        return response.is_success

    # High-level methods

    async def list_apps(self) -> list[dict[str, Any]]:
        """List all apps."""
        result = await self.get("apps")
        return result.get("data", [])  # type: ignore[no-any-return]

    async def get_app(self, bundle_id: str) -> dict[str, Any] | None:
        """Get app by bundle ID."""
        result = await self.get("apps", {"filter[bundleId]": bundle_id})
        apps = result.get("data", [])
        return apps[0] if apps else None

    async def get_app_by_id(self, app_id: str) -> dict[str, Any]:
        """Get app by App Store Connect ID."""
        result = await self.get(f"apps/{app_id}")
        return result.get("data", {})  # type: ignore[no-any-return]

    async def list_subscription_groups(self, app_id: str) -> list[dict[str, Any]]:
        """List subscription groups for an app."""
        result = await self.get(f"apps/{app_id}/subscriptionGroups")
        return result.get("data", [])  # type: ignore[no-any-return]

    async def list_subscriptions(self, group_id: str) -> list[dict[str, Any]]:
        """List subscriptions in a group."""
        result = await self.get(f"subscriptionGroups/{group_id}/subscriptions")
        return result.get("data", [])  # type: ignore[no-any-return]

    async def get_subscription(self, subscription_id: str) -> dict[str, Any]:
        """Get subscription details."""
        result = await self.get(f"subscriptions/{subscription_id}")
        return result.get("data", {})  # type: ignore[no-any-return]

    async def list_price_points(
        self,
        subscription_id: str,
        territory: str | None = None,
        include_territory: bool = True,
    ) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        """List price points for a subscription.

        Args:
            subscription_id: The subscription ID
            territory: Optional territory filter (e.g., "USA", "GBR")
            include_territory: Whether to include territory details

        Returns:
            Tuple of (price_points, included_territories_map)
        """
        params: dict[str, Any] = {"limit": 200}
        if territory:
            params["filter[territory]"] = territory
        if include_territory:
            params["include"] = "territory"

        all_price_points: list[dict[str, Any]] = []
        included_map: dict[str, dict[str, Any]] = {}
        next_url: str | None = f"subscriptions/{subscription_id}/pricePoints"

        while next_url:
            # Handle both relative and absolute URLs
            if next_url.startswith("http"):
                # Extract the path from full URL
                from urllib.parse import urlparse

                parsed = urlparse(next_url)
                endpoint = parsed.path.replace("/v1/", "")
                if parsed.query:
                    endpoint += f"?{parsed.query}"
                result = await self.get(endpoint)
            else:
                result = await self.get(
                    next_url,
                    params if next_url == f"subscriptions/{subscription_id}/pricePoints" else None,
                )

            all_price_points.extend(result.get("data", []))

            # Build map of included territories
            for inc in result.get("included", []):
                if inc.get("type") == "territories":
                    included_map[inc["id"]] = inc

            # Check for next page
            links = result.get("links", {})
            next_url = links.get("next")

        return all_price_points, included_map

    async def list_all_price_points_by_territory(
        self,
        subscription_id: str,
    ) -> dict[str, list[dict[str, Any]]]:
        """Get all price points organized by territory.

        Returns:
            Dict mapping territory ID to list of price points
        """
        price_points, _ = await self.list_price_points(subscription_id)

        by_territory: dict[str, list[dict[str, Any]]] = {}
        for pp in price_points:
            territory_data = pp.get("relationships", {}).get("territory", {}).get("data", {})
            territory_id = territory_data.get("id", "UNKNOWN")
            if territory_id not in by_territory:
                by_territory[territory_id] = []
            by_territory[territory_id].append(pp)

        return by_territory

    async def find_price_point_by_usd(
        self,
        subscription_id: str,
        usd_price: float,
        territory: str = "USA",
    ) -> dict[str, Any] | None:
        """Find a price point matching the given USD price.

        Args:
            subscription_id: The subscription ID
            usd_price: Target price in USD (e.g., 2.99)
            territory: Territory to search in (default USA)

        Returns:
            The matching price point or None
        """
        price_points, _ = await self.list_price_points(
            subscription_id, territory=territory, include_territory=False
        )

        # Find exact or closest match
        target = str(usd_price)
        for pp in price_points:
            customer_price = pp.get("attributes", {}).get("customerPrice", "")
            if customer_price == target:
                return pp

        return None

    async def find_equalizing_price_points(
        self,
        subscription_id: str,
        base_price_point_id: str,
    ) -> list[dict[str, Any]]:
        """Find price points in other territories that equalize to a base price point.

        This uses Apple's automatic price equalization feature.

        Args:
            subscription_id: The subscription ID
            base_price_point_id: The base price point ID (usually USA)

        Returns:
            List of equalizing price points for all territories
        """
        result = await self.get(
            f"subscriptionPricePoints/{base_price_point_id}/equalizations",
            {"limit": 200, "include": "territory"},
        )

        all_points: list[dict[str, Any]] = []
        all_points.extend(result.get("data", []))

        # Handle pagination
        links = result.get("links", {})
        next_url = links.get("next")

        while next_url:
            from urllib.parse import urlparse

            parsed = urlparse(next_url)
            endpoint = parsed.path.replace("/v1/", "")
            if parsed.query:
                endpoint += f"?{parsed.query}"
            result = await self.get(endpoint)
            all_points.extend(result.get("data", []))
            links = result.get("links", {})
            next_url = links.get("next")

        return all_points

    async def list_subscription_prices(self, subscription_id: str) -> list[dict[str, Any]]:
        """List current prices for a subscription."""
        result = await self.get(f"subscriptions/{subscription_id}/prices")
        return result.get("data", [])  # type: ignore[no-any-return]

    async def create_subscription_price(
        self,
        subscription_id: str,
        price_point_id: str,
        start_date: str | None = None,
        preserve_current_price: bool = False,
    ) -> dict[str, Any]:
        """Create/update a subscription price."""
        data: dict[str, Any] = {
            "data": {
                "type": "subscriptionPrices",
                "attributes": {},
                "relationships": {
                    "subscription": {"data": {"type": "subscriptions", "id": subscription_id}},
                    "subscriptionPricePoint": {
                        "data": {"type": "subscriptionPricePoints", "id": price_point_id}
                    },
                },
            }
        }

        if start_date:
            data["data"]["attributes"]["startDate"] = start_date
        if preserve_current_price:
            data["data"]["attributes"]["preserveCurrentPrice"] = True

        return await self.post("subscriptionPrices", data)

    async def list_introductory_offers(self, subscription_id: str) -> list[dict[str, Any]]:
        """List introductory offers for a subscription."""
        result = await self.get(f"subscriptions/{subscription_id}/introductoryOffers")
        return result.get("data", [])  # type: ignore[no-any-return]

    async def create_introductory_offer(
        self,
        subscription_id: str,
        territory_id: str,
        offer_mode: str,  # "freeTrial", "payAsYouGo", "payUpFront"
        duration: str,  # e.g., "P1W", "P2W", "P1M", "P3M"
        number_of_periods: int = 1,
        subscription_price_point_id: str | None = None,
    ) -> dict[str, Any]:
        """Create an introductory offer."""
        data: dict[str, Any] = {
            "data": {
                "type": "subscriptionIntroductoryOffers",
                "attributes": {
                    "duration": duration,
                    "offerMode": offer_mode,
                    "numberOfPeriods": number_of_periods,
                },
                "relationships": {
                    "subscription": {"data": {"type": "subscriptions", "id": subscription_id}},
                    "territory": {"data": {"type": "territories", "id": territory_id}},
                },
            }
        }

        if subscription_price_point_id:
            data["data"]["relationships"]["subscriptionPricePoint"] = {
                "data": {"type": "subscriptionPricePoints", "id": subscription_price_point_id}
            }

        return await self.post("subscriptionIntroductoryOffers", data)

    async def delete_introductory_offer(self, offer_id: str) -> bool:
        """Delete an introductory offer."""
        return await self.delete(f"subscriptionIntroductoryOffers/{offer_id}")

    async def list_territories(self) -> list[dict[str, Any]]:
        """List all territories."""
        result = await self.get("territories", {"limit": 200})
        return result.get("data", [])  # type: ignore[no-any-return]

    async def list_subscription_localizations(self, subscription_id: str) -> list[dict[str, Any]]:
        """List localizations for a subscription."""
        result = await self.get(f"subscriptions/{subscription_id}/subscriptionLocalizations")
        return result.get("data", [])  # type: ignore[no-any-return]

    async def get_subscription_availability(
        self,
        subscription_id: str,
    ) -> dict[str, Any] | None:
        """Get subscription availability settings."""
        import httpx

        try:
            result = await self.get(
                f"subscriptions/{subscription_id}/subscriptionAvailability",
                {"include": "availableTerritories"},
            )
            return result.get("data")
        except httpx.HTTPStatusError as e:
            # 404 is expected when no availability is set yet
            if e.response.status_code == 404:
                return None
            # Re-raise other HTTP errors (401, 403, 429, 500, etc.)
            raise

    async def set_subscription_availability(
        self,
        subscription_id: str,
        territory_ids: list[str],
        available_in_new_territories: bool = True,
    ) -> dict[str, Any]:
        """Set subscription availability for territories.

        Args:
            subscription_id: The subscription ID
            territory_ids: List of territory IDs to make available
            available_in_new_territories: Auto-enable in new territories

        Returns:
            The created/updated availability
        """
        data: dict[str, Any] = {
            "data": {
                "type": "subscriptionAvailabilities",
                "attributes": {
                    "availableInNewTerritories": available_in_new_territories,
                },
                "relationships": {
                    "subscription": {"data": {"type": "subscriptions", "id": subscription_id}},
                    "availableTerritories": {
                        "data": [{"type": "territories", "id": tid} for tid in territory_ids]
                    },
                },
            }
        }

        return await self.post("subscriptionAvailabilities", data)


class APIError(Exception):
    """API request error."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")
