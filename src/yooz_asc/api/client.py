"""App Store Connect API client."""

from typing import Any, Optional

import httpx

from yooz_asc.api.auth import AuthManager


class AppStoreConnectClient:
    """HTTP client for App Store Connect API."""

    BASE_URL = "https://api.appstoreconnect.apple.com/v1"

    def __init__(self, auth: Optional[AuthManager] = None) -> None:
        """Initialize client with optional auth manager."""
        self._auth = auth or AuthManager.auto()
        self._client: Optional[httpx.AsyncClient] = None

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
        params: Optional[dict[str, Any]] = None,
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

    async def get_app(self, bundle_id: str) -> Optional[dict[str, Any]]:
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

    async def list_price_points(self, subscription_id: str) -> list[dict[str, Any]]:
        """List price points for a subscription."""
        result = await self.get(
            f"subscriptions/{subscription_id}/pricePoints",
            {"filter[territory]": "USA", "include": "territory"},
        )
        return result.get("data", [])  # type: ignore[no-any-return]

    async def list_subscription_prices(self, subscription_id: str) -> list[dict[str, Any]]:
        """List current prices for a subscription."""
        result = await self.get(f"subscriptions/{subscription_id}/prices")
        return result.get("data", [])  # type: ignore[no-any-return]

    async def create_subscription_price(
        self,
        subscription_id: str,
        price_point_id: str,
        start_date: Optional[str] = None,
        preserve_current_price: bool = False,
    ) -> dict[str, Any]:
        """Create/update a subscription price."""
        data: dict[str, Any] = {
            "data": {
                "type": "subscriptionPrices",
                "attributes": {},
                "relationships": {
                    "subscription": {
                        "data": {"type": "subscriptions", "id": subscription_id}
                    },
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
        subscription_price_point_id: Optional[str] = None,
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
                    "subscription": {
                        "data": {"type": "subscriptions", "id": subscription_id}
                    },
                    "territory": {
                        "data": {"type": "territories", "id": territory_id}
                    },
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


class APIError(Exception):
    """API request error."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")
