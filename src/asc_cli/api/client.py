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

    # TestFlight Methods

    async def list_builds(
        self,
        app_id: str,
        limit: int = 10,
        processing_state: str | None = None,
    ) -> list[dict[str, Any]]:
        """List builds for an app.

        Args:
            app_id: The app ID
            limit: Maximum number of builds to return
            processing_state: Filter by processing state (e.g., "VALID", "PROCESSING")

        Returns:
            List of build resources
        """
        params: dict[str, Any] = {
            "filter[app]": app_id,
            "limit": limit,
            "sort": "-uploadedDate",
        }
        if processing_state:
            params["filter[processingState]"] = processing_state

        result = await self.get("builds", params)
        return result.get("data", [])  # type: ignore[no-any-return]

    async def get_build(self, build_id: str) -> dict[str, Any]:
        """Get build details.

        Args:
            build_id: The build ID

        Returns:
            Build resource
        """
        result = await self.get(f"builds/{build_id}")
        return result.get("data", {})  # type: ignore[no-any-return]

    async def get_build_by_version(
        self,
        app_id: str,
        version: str,
    ) -> dict[str, Any] | None:
        """Find a build by version string.

        Args:
            app_id: The app ID
            version: The build version (CFBundleVersion)

        Returns:
            Build resource or None if not found
        """
        params: dict[str, Any] = {
            "filter[app]": app_id,
            "filter[version]": version,
        }
        result = await self.get("builds", params)
        builds = result.get("data", [])
        return builds[0] if builds else None

    async def list_beta_build_localizations(
        self,
        build_id: str,
    ) -> list[dict[str, Any]]:
        """List beta build localizations (What's New text).

        Args:
            build_id: The build ID

        Returns:
            List of beta build localization resources
        """
        result = await self.get(f"builds/{build_id}/betaBuildLocalizations")
        return result.get("data", [])  # type: ignore[no-any-return]

    async def create_beta_build_localization(
        self,
        build_id: str,
        locale: str,
        whats_new: str,
    ) -> dict[str, Any]:
        """Create a beta build localization (What's New text).

        Args:
            build_id: The build ID
            locale: Locale code (e.g., "en-US")
            whats_new: The What's New text

        Returns:
            Created beta build localization resource
        """
        data = {
            "data": {
                "type": "betaBuildLocalizations",
                "attributes": {
                    "locale": locale,
                    "whatsNew": whats_new,
                },
                "relationships": {"build": {"data": {"type": "builds", "id": build_id}}},
            }
        }
        return await self.post("betaBuildLocalizations", data)

    async def update_beta_build_localization(
        self,
        localization_id: str,
        whats_new: str,
    ) -> dict[str, Any]:
        """Update a beta build localization (What's New text).

        Args:
            localization_id: The localization ID
            whats_new: The new What's New text

        Returns:
            Updated beta build localization resource
        """
        data = {
            "data": {
                "type": "betaBuildLocalizations",
                "id": localization_id,
                "attributes": {
                    "whatsNew": whats_new,
                },
            }
        }
        return await self.patch(f"betaBuildLocalizations/{localization_id}", data)

    async def get_app_encryption_declaration(
        self,
        build_id: str,
    ) -> dict[str, Any] | None:
        """Get the encryption declaration for a build.

        Args:
            build_id: The build ID

        Returns:
            App encryption declaration resource or None
        """
        import httpx

        try:
            result = await self.get(f"builds/{build_id}/appEncryptionDeclaration")
            return result.get("data")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def create_app_encryption_declaration(
        self,
        build_id: str,
        uses_encryption: bool,
        is_exempt: bool = True,
    ) -> dict[str, Any]:
        """Create an encryption declaration for a build.

        Args:
            build_id: The build ID
            uses_encryption: Whether the app uses encryption
            is_exempt: Whether encryption is exempt (standard HTTPS, etc.)

        Returns:
            Created app encryption declaration resource
        """
        # If not using encryption or exempt, set appropriate values
        if not uses_encryption:
            code_value = "NONE"
        elif is_exempt:
            code_value = "EXEMPT"
        else:
            code_value = "CONTAINS_PROPRIETARY_CRYPTOGRAPHY"

        data = {
            "data": {
                "type": "appEncryptionDeclarations",
                "attributes": {
                    "usesEncryption": uses_encryption,
                    "codeValue": code_value,
                },
                "relationships": {"build": {"data": {"type": "builds", "id": build_id}}},
            }
        }
        return await self.post("appEncryptionDeclarations", data)

    async def submit_for_beta_review(
        self,
        build_id: str,
    ) -> dict[str, Any]:
        """Submit a build for beta app review.

        Args:
            build_id: The build ID

        Returns:
            Beta app review submission resource
        """
        data = {
            "data": {
                "type": "betaAppReviewSubmissions",
                "relationships": {"build": {"data": {"type": "builds", "id": build_id}}},
            }
        }
        return await self.post("betaAppReviewSubmissions", data)

    # Beta Groups

    async def list_beta_groups(
        self,
        app_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List beta groups for an app.

        Args:
            app_id: The app ID
            limit: Maximum number of groups to return

        Returns:
            List of beta group resources
        """
        result = await self.get(
            f"apps/{app_id}/betaGroups",
            {"limit": limit},
        )
        return result.get("data", [])  # type: ignore[no-any-return]

    async def get_beta_group(self, group_id: str) -> dict[str, Any]:
        """Get beta group details.

        Args:
            group_id: The beta group ID

        Returns:
            Beta group resource
        """
        result = await self.get(f"betaGroups/{group_id}")
        return result.get("data", {})  # type: ignore[no-any-return]

    async def create_beta_group(
        self,
        app_id: str,
        name: str,
        is_internal: bool = False,
        public_link_enabled: bool = False,
        public_link_limit: int | None = None,
        feedback_enabled: bool = True,
    ) -> dict[str, Any]:
        """Create a beta group.

        Args:
            app_id: The app ID
            name: Group name
            is_internal: Whether this is an internal group
            public_link_enabled: Enable public TestFlight link
            public_link_limit: Max testers via public link (None = unlimited)
            feedback_enabled: Allow testers to send feedback

        Returns:
            Created beta group resource
        """
        attributes: dict[str, Any] = {
            "name": name,
            "isInternalGroup": is_internal,
            "publicLinkEnabled": public_link_enabled,
            "feedbackEnabled": feedback_enabled,
        }
        if public_link_limit is not None:
            attributes["publicLinkLimit"] = public_link_limit

        data = {
            "data": {
                "type": "betaGroups",
                "attributes": attributes,
                "relationships": {"app": {"data": {"type": "apps", "id": app_id}}},
            }
        }
        return await self.post("betaGroups", data)

    async def update_beta_group(
        self,
        group_id: str,
        name: str | None = None,
        public_link_enabled: bool | None = None,
        public_link_limit: int | None = None,
        feedback_enabled: bool | None = None,
    ) -> dict[str, Any]:
        """Update a beta group.

        Args:
            group_id: The beta group ID
            name: New group name
            public_link_enabled: Enable/disable public link
            public_link_limit: Max testers via public link
            feedback_enabled: Allow testers to send feedback

        Returns:
            Updated beta group resource
        """
        attributes: dict[str, Any] = {}
        if name is not None:
            attributes["name"] = name
        if public_link_enabled is not None:
            attributes["publicLinkEnabled"] = public_link_enabled
        if public_link_limit is not None:
            attributes["publicLinkLimit"] = public_link_limit
        if feedback_enabled is not None:
            attributes["feedbackEnabled"] = feedback_enabled

        data = {
            "data": {
                "type": "betaGroups",
                "id": group_id,
                "attributes": attributes,
            }
        }
        return await self.patch(f"betaGroups/{group_id}", data)

    async def delete_beta_group(self, group_id: str) -> bool:
        """Delete a beta group.

        Args:
            group_id: The beta group ID

        Returns:
            True if deleted successfully
        """
        return await self.delete(f"betaGroups/{group_id}")

    async def add_builds_to_beta_group(
        self,
        group_id: str,
        build_ids: list[str],
    ) -> None:
        """Add builds to a beta group.

        Args:
            group_id: The beta group ID
            build_ids: List of build IDs to add
        """
        data = {"data": [{"type": "builds", "id": bid} for bid in build_ids]}
        await self.post(f"betaGroups/{group_id}/relationships/builds", data)

    # Beta Testers

    async def list_beta_testers(
        self,
        app_id: str | None = None,
        email: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List beta testers.

        Args:
            app_id: Filter by app ID
            email: Filter by email
            limit: Maximum number of testers to return

        Returns:
            List of beta tester resources
        """
        params: dict[str, Any] = {"limit": limit}
        if app_id:
            params["filter[apps]"] = app_id
        if email:
            params["filter[email]"] = email

        result = await self.get("betaTesters", params)
        return result.get("data", [])  # type: ignore[no-any-return]

    async def get_beta_tester(self, tester_id: str) -> dict[str, Any]:
        """Get beta tester details.

        Args:
            tester_id: The beta tester ID

        Returns:
            Beta tester resource
        """
        result = await self.get(f"betaTesters/{tester_id}")
        return result.get("data", {})  # type: ignore[no-any-return]

    async def create_beta_tester(
        self,
        email: str,
        first_name: str | None = None,
        last_name: str | None = None,
        group_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a beta tester.

        Args:
            email: Tester email address
            first_name: Tester first name
            last_name: Tester last name
            group_ids: Beta group IDs to add tester to

        Returns:
            Created beta tester resource
        """
        attributes: dict[str, Any] = {"email": email}
        if first_name:
            attributes["firstName"] = first_name
        if last_name:
            attributes["lastName"] = last_name

        data: dict[str, Any] = {
            "data": {
                "type": "betaTesters",
                "attributes": attributes,
            }
        }

        if group_ids:
            data["data"]["relationships"] = {
                "betaGroups": {"data": [{"type": "betaGroups", "id": gid} for gid in group_ids]}
            }

        return await self.post("betaTesters", data)

    async def delete_beta_tester(self, tester_id: str) -> bool:
        """Delete a beta tester.

        Args:
            tester_id: The beta tester ID

        Returns:
            True if deleted successfully
        """
        return await self.delete(f"betaTesters/{tester_id}")

    async def add_beta_tester_to_groups(
        self,
        tester_id: str,
        group_ids: list[str],
    ) -> None:
        """Add a beta tester to groups.

        Args:
            tester_id: The beta tester ID
            group_ids: List of group IDs to add tester to
        """
        data = {"data": [{"type": "betaGroups", "id": gid} for gid in group_ids]}
        await self.post(f"betaTesters/{tester_id}/relationships/betaGroups", data)

    async def remove_beta_tester_from_groups(
        self,
        tester_id: str,
        group_ids: list[str],
    ) -> None:
        """Remove a beta tester from groups.

        Args:
            tester_id: The beta tester ID
            group_ids: List of group IDs to remove tester from
        """
        data = {"data": [{"type": "betaGroups", "id": gid} for gid in group_ids]}
        # DELETE with body for relationship removal
        client = await self._get_client()
        response = await client.request(
            "DELETE",
            f"betaTesters/{tester_id}/relationships/betaGroups",
            headers=self._headers(),
            json=data,
        )
        response.raise_for_status()

    # Build Beta Details (auto-notify settings)

    async def get_build_beta_details(self, build_id: str) -> dict[str, Any]:
        """Get build beta details (auto-notify settings).

        Args:
            build_id: The build ID

        Returns:
            Build beta detail resource
        """
        result = await self.get(f"builds/{build_id}/buildBetaDetail")
        return result.get("data", {})  # type: ignore[no-any-return]

    async def update_build_beta_details(
        self,
        build_beta_detail_id: str,
        auto_notify_enabled: bool | None = None,
    ) -> dict[str, Any]:
        """Update build beta details.

        Args:
            build_beta_detail_id: The build beta detail ID
            auto_notify_enabled: Whether to auto-notify testers

        Returns:
            Updated build beta detail resource
        """
        attributes: dict[str, Any] = {}
        if auto_notify_enabled is not None:
            attributes["autoNotifyEnabled"] = auto_notify_enabled

        data = {
            "data": {
                "type": "buildBetaDetails",
                "id": build_beta_detail_id,
                "attributes": attributes,
            }
        }
        return await self.patch(f"buildBetaDetails/{build_beta_detail_id}", data)

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
