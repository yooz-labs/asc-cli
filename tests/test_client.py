"""Tests for API client."""

from asc_cli.api.client import AppStoreConnectClient


class TestClientProperties:
    """Test client properties and setup."""

    def test_auth_property(self, mock_asc_api) -> None:
        """Test auth property returns auth manager."""
        client = AppStoreConnectClient()

        assert client.auth is not None
        assert client.auth.is_authenticated

    async def test_close_client(self, mock_asc_api) -> None:
        """Test closing the client."""
        client = AppStoreConnectClient()

        # Get client to initialize it
        await client._get_client()

        # Close it
        await client.close()

        # Should be closed
        assert client._client is not None
        assert client._client.is_closed


class TestClientMethods:
    """Test client API methods."""

    async def test_list_apps(self, mock_asc_with_app) -> None:
        """Test listing apps."""
        client = AppStoreConnectClient()

        try:
            apps = await client.list_apps()
            assert isinstance(apps, list)
            assert len(apps) > 0
        finally:
            await client.close()

    async def test_get_app(self, mock_asc_with_app) -> None:
        """Test getting app by bundle ID."""
        client = AppStoreConnectClient()

        try:
            app = await client.get_app("com.example.test")
            assert app is not None
            assert app.get("attributes", {}).get("bundleId") == "com.example.test"
        finally:
            await client.close()

    async def test_get_app_not_found(self, mock_asc_api) -> None:
        """Test getting non-existent app."""
        client = AppStoreConnectClient()

        try:
            app = await client.get_app("com.nonexistent.app")
            assert app is None
        finally:
            await client.close()

    async def test_list_subscription_groups(self, mock_asc_with_app) -> None:
        """Test listing subscription groups."""
        client = AppStoreConnectClient()

        try:
            # Get app first
            app = await client.get_app("com.example.test")
            assert app is not None

            # List groups
            groups = await client.list_subscription_groups(app["id"])
            assert isinstance(groups, list)
        finally:
            await client.close()

    async def test_list_subscriptions(self, mock_asc_with_app) -> None:
        """Test listing subscriptions."""
        client = AppStoreConnectClient()

        try:
            # Get app and groups
            app = await client.get_app("com.example.test")
            groups = await client.list_subscription_groups(app["id"])

            if groups:
                # List subscriptions
                subs = await client.list_subscriptions(groups[0]["id"])
                assert isinstance(subs, list)
        finally:
            await client.close()

    async def test_get_subscription(self, mock_asc_with_app) -> None:
        """Test getting a subscription."""
        client = AppStoreConnectClient()

        try:
            sub = await client.get_subscription("sub_app_123")
            assert sub is not None
        finally:
            await client.close()

    async def test_list_territories(self, mock_asc_api) -> None:
        """Test listing territories."""
        client = AppStoreConnectClient()

        try:
            territories = await client.list_territories()
            assert isinstance(territories, list)
            assert len(territories) > 0
        finally:
            await client.close()

    async def test_list_all_price_points_by_territory(self, mock_asc_with_app) -> None:
        """Test listing all price points by territory."""
        from tests.simulation.fixtures.price_points import (
            generate_price_points_for_subscription,
        )

        client = AppStoreConnectClient()
        simulator = mock_asc_with_app

        # Generate price points for multiple territories
        generate_price_points_for_subscription(simulator.state, "sub_app_123", ["USA", "GBR"])

        try:
            grouped = await client.list_all_price_points_by_territory("sub_app_123")
            assert isinstance(grouped, dict)
        finally:
            await client.close()

    async def test_list_price_points_with_territory_filter(self, mock_asc_with_app) -> None:
        """Test listing price points with territory filter."""
        from tests.simulation.fixtures.price_points import (
            generate_price_points_for_subscription,
        )

        client = AppStoreConnectClient()
        simulator = mock_asc_with_app
        generate_price_points_for_subscription(simulator.state, "sub_app_123", ["USA"])

        try:
            price_points, territories = await client.list_price_points(
                "sub_app_123", territory="USA", include_territory=True
            )
            assert isinstance(price_points, list)
            assert isinstance(territories, dict)
        finally:
            await client.close()
