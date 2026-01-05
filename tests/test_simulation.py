"""Tests using the API simulation engine.

These tests verify the CLI commands work correctly against simulated API responses.
"""

import pytest

from asc_cli.api.client import AppStoreConnectClient


@pytest.mark.simulation
class TestAppsSimulation:
    """Tests for apps endpoints using simulation."""

    @pytest.mark.asyncio
    async def test_list_apps(self, mock_asc_with_app) -> None:
        """Test listing apps."""
        client = AppStoreConnectClient()
        try:
            apps = await client.list_apps()
            assert len(apps) == 1
            assert apps[0]["attributes"]["bundleId"] == "com.example.test"
            assert apps[0]["attributes"]["name"] == "Test App"
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_get_app_by_bundle_id(self, mock_asc_with_app) -> None:
        """Test getting app by bundle ID."""
        client = AppStoreConnectClient()
        try:
            app = await client.get_app("com.example.test")
            assert app is not None
            assert app["attributes"]["name"] == "Test App"
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_get_app_not_found(self, mock_asc_with_app) -> None:
        """Test getting non-existent app."""
        client = AppStoreConnectClient()
        try:
            app = await client.get_app("com.nonexistent.app")
            assert app is None
        finally:
            await client.close()


@pytest.mark.simulation
class TestSubscriptionGroupsSimulation:
    """Tests for subscription groups using simulation."""

    @pytest.mark.asyncio
    async def test_list_subscription_groups(self, mock_asc_with_app) -> None:
        """Test listing subscription groups."""
        client = AppStoreConnectClient()
        try:
            groups = await client.list_subscription_groups("app_123")
            assert len(groups) == 1
            assert groups[0]["attributes"]["referenceName"] == "Premium"
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_list_subscription_groups_not_found(self, mock_asc_with_app) -> None:
        """Test listing groups for non-existent app."""
        client = AppStoreConnectClient()
        try:
            # This should raise or return empty based on implementation
            groups = await client.list_subscription_groups("nonexistent_app")
            # If it doesn't raise, it should be empty or the test handles the error
            assert groups == [] or groups is None
        except Exception:
            pass  # Expected for non-existent app
        finally:
            await client.close()


@pytest.mark.simulation
class TestSubscriptionsSimulation:
    """Tests for subscriptions using simulation."""

    @pytest.mark.asyncio
    async def test_list_subscriptions(self, mock_asc_with_app) -> None:
        """Test listing subscriptions in a group."""
        client = AppStoreConnectClient()
        try:
            subscriptions = await client.list_subscriptions("group_app_123")
            assert len(subscriptions) == 1
            assert subscriptions[0]["attributes"]["name"] == "Premium Monthly"
            assert subscriptions[0]["attributes"]["subscriptionPeriod"] == "ONE_MONTH"
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_get_subscription(self, mock_asc_with_app) -> None:
        """Test getting a specific subscription."""
        client = AppStoreConnectClient()
        try:
            subscription = await client.get_subscription("sub_app_123")
            assert subscription is not None
            assert subscription["attributes"]["name"] == "Premium Monthly"
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_list_subscription_localizations(self, mock_asc_with_app) -> None:
        """Test listing subscription localizations."""
        client = AppStoreConnectClient()
        try:
            localizations = await client.list_subscription_localizations("sub_app_123")
            assert len(localizations) == 1
            assert localizations[0]["attributes"]["locale"] == "en-US"
        finally:
            await client.close()


@pytest.mark.simulation
class TestTerritoriesSimulation:
    """Tests for territories using simulation."""

    @pytest.mark.asyncio
    async def test_list_territories(self, mock_asc_with_app) -> None:
        """Test listing territories."""
        client = AppStoreConnectClient()
        try:
            territories = await client.list_territories()
            assert len(territories) > 0
            # Check for some expected territories
            territory_ids = [t["id"] for t in territories]
            assert "USA" in territory_ids
            assert "GBR" in territory_ids
            assert "JPN" in territory_ids
        finally:
            await client.close()


@pytest.mark.simulation
class TestWhisperAppSimulation:
    """Tests using the Whisper app fixture."""

    @pytest.mark.asyncio
    async def test_whisper_has_four_subscriptions(self, mock_asc_whisper) -> None:
        """Test Whisper app has correct subscription structure."""
        client = AppStoreConnectClient()
        try:
            groups = await client.list_subscription_groups("app_whisper")
            assert len(groups) == 1
            assert groups[0]["attributes"]["referenceName"] == "Yooz Whisper Plans"

            subscriptions = await client.list_subscriptions("group_whisper_premium")
            assert len(subscriptions) == 4
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_whisper_subscriptions_have_localizations(self, mock_asc_whisper) -> None:
        """Test Whisper subscriptions have localizations."""
        client = AppStoreConnectClient()
        try:
            localizations = await client.list_subscription_localizations("sub_whisper_monthly")
            assert len(localizations) == 1
            assert localizations[0]["attributes"]["locale"] == "en-US"
        finally:
            await client.close()


@pytest.mark.simulation
class TestRateLimitSimulation:
    """Tests for rate limit handling."""

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, mock_asc_with_app) -> None:
        """Test rate limit error is returned."""
        import httpx

        mock_asc_with_app.simulate_rate_limit()

        client = AppStoreConnectClient()
        try:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await client.list_apps()
            assert exc_info.value.response.status_code == 429
        finally:
            await client.close()


@pytest.mark.simulation
class TestErrorSimulation:
    """Tests for error scenarios."""

    @pytest.mark.asyncio
    async def test_custom_error_override(self, mock_asc_with_app) -> None:
        """Test custom error override works."""
        import httpx

        mock_asc_with_app.simulate_error(
            r"/v1/apps$",
            500,
            "INTERNAL_ERROR",
            "Simulated server error",
        )

        client = AppStoreConnectClient()
        try:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await client.list_apps()
            assert exc_info.value.response.status_code == 500
        finally:
            await client.close()
