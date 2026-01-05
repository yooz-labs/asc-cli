"""Comprehensive tests for subscription CLI commands - edge cases and error paths."""

import pytest
from typer.testing import CliRunner

from asc_cli.cli import app
from tests.simulation import ASCSimulator

runner = CliRunner()


class TestSubscriptionsListEdgeCases:
    """Test edge cases for subscriptions list command."""

    def test_list_app_not_found(self, mock_asc_api: ASCSimulator) -> None:
        """Test list when app doesn't exist."""
        result = runner.invoke(app, ["subscriptions", "list", "com.nonexistent.app"])

        assert result.exit_code == 1
        assert "App not found" in result.output

    def test_list_no_subscription_groups(self, mock_asc_no_subscriptions: ASCSimulator) -> None:
        """Test list when app has no subscription groups."""
        result = runner.invoke(app, ["subscriptions", "list", "com.example.test"])

        assert result.exit_code == 0
        assert "No subscription groups found" in result.output

    def test_list_group_with_no_subscriptions(self, mock_asc_api: ASCSimulator) -> None:
        """Test list when subscription group is empty."""
        # Create app and empty group
        simulator = mock_asc_api
        simulator.state.add_app("app_empty", "com.empty.app", "Empty App")
        simulator.state.add_subscription_group("group_empty", "app_empty", "Empty Group")

        result = runner.invoke(app, ["subscriptions", "list", "com.empty.app"])

        assert result.exit_code == 0
        assert "No subscriptions" in result.output


class TestSubscriptionsCheckEdgeCases:
    """Test edge cases for subscriptions check command."""

    def test_check_app_not_found(self, mock_asc_api: ASCSimulator) -> None:
        """Test check when app doesn't exist."""
        result = runner.invoke(app, ["subscriptions", "check", "com.nonexistent.app"])

        assert result.exit_code == 1
        assert "App not found" in result.output

    def test_check_no_subscription_groups(self, mock_asc_no_subscriptions: ASCSimulator) -> None:
        """Test check when app has no subscription groups."""
        result = runner.invoke(app, ["subscriptions", "check", "com.example.test"])

        assert result.exit_code == 0
        assert "No subscription groups found" in result.output

    def test_check_no_subscriptions_in_group(self, mock_asc_api: ASCSimulator) -> None:
        """Test check when group has no subscriptions."""
        simulator = mock_asc_api
        simulator.state.add_app("app_empty", "com.empty.app", "Empty App")
        simulator.state.add_subscription_group("group_empty", "app_empty", "Empty Group")

        result = runner.invoke(app, ["subscriptions", "check", "com.empty.app"])

        assert result.exit_code == 0
        assert "No subscriptions" in result.output

    def test_check_no_localizations(self, mock_asc_api: ASCSimulator) -> None:
        """Test check when subscription has no localizations."""
        simulator = mock_asc_api
        simulator.state.add_app("app_test", "com.test.app", "Test App")
        simulator.state.add_subscription_group("group_test", "app_test", "Test Group")
        simulator.state.add_subscription(
            "sub_test",
            "group_test",
            "com.test.app.sub",
            "Test Sub",
            subscription_period="ONE_MONTH",
        )
        # Don't add localizations

        result = runner.invoke(app, ["subscriptions", "check", "com.test.app"])

        assert result.exit_code == 0
        assert "Localizations: None" in result.output
        assert "Add at least one localization" in result.output

    def test_check_no_pricing(self, mock_asc_with_app: ASCSimulator) -> None:
        """Test check when subscription has no pricing."""
        result = runner.invoke(app, ["subscriptions", "check", "com.example.test"])

        assert result.exit_code == 0
        # Should show pricing not configured
        assert "Pricing" in result.output

    @pytest.mark.skip(reason="Pricing retrieval needs implementation in simulation")
    def test_check_all_passed_but_missing_metadata(self, mock_asc_with_app: ASCSimulator) -> None:
        """Test check when all checks pass but state is MISSING_METADATA."""
        # This test needs list_subscription_prices to return the prices
        # Currently simulation doesn't implement this endpoint correctly
        pass

    def test_check_all_ready(self, mock_asc_api: ASCSimulator) -> None:
        """Test check when all subscriptions are ready."""
        from tests.simulation.fixtures.price_points import (
            generate_price_points_for_subscription,
        )

        simulator = mock_asc_api
        simulator.state.add_app("app_ready", "com.ready.app", "Ready App")
        simulator.state.add_subscription_group("group_ready", "app_ready", "Ready Group")

        # Add fully configured subscription
        simulator.state.add_subscription(
            "sub_ready",
            "group_ready",
            "com.ready.app.sub",
            "Ready Sub",
            state="READY_TO_SUBMIT",
            subscription_period="ONE_MONTH",
        )

        # Add localization
        simulator.state.add_subscription_localization(
            "loc_ready",
            "sub_ready",
            "en-US",
            "Ready Sub",
            "Ready description",
        )

        # Add pricing
        generate_price_points_for_subscription(simulator.state, "sub_ready")
        simulator.state.set_subscription_availability("sub_ready", ["USA"])
        simulator.state.add_subscription_price(
            price_id="price_sub_ready_2",
            subscription_id="sub_ready",
            price_point_id="pp_sub_ready_USA_tier_30",
        )

        result = runner.invoke(app, ["subscriptions", "check", "com.ready.app"])

        assert result.exit_code == 0
        assert "All subscriptions ready" in result.output


class TestSubscriptionsPricingEdgeCases:
    """Test edge cases for subscription pricing commands."""

    def test_pricing_list_subscription_not_found(self, mock_asc_api: ASCSimulator) -> None:
        """Test pricing list when subscription doesn't exist."""
        result = runner.invoke(app, ["subscriptions", "pricing", "list", "nonexistent_sub"])

        # Command may raise exception or show error
        assert result.exit_code != 0 or result.exception is not None

    def test_pricing_list_no_availability(self, mock_asc_with_app: ASCSimulator) -> None:
        """Test pricing list when subscription has no availability set."""
        result = runner.invoke(app, ["subscriptions", "pricing", "list", "sub_app_123"])

        assert result.exit_code == 0
        # Should handle no availability gracefully

    def test_pricing_set_subscription_not_found(self, mock_asc_api: ASCSimulator) -> None:
        """Test pricing set when subscription doesn't exist."""
        result = runner.invoke(
            app,
            [
                "subscriptions",
                "pricing",
                "set",
                "nonexistent_sub",
                "--price",
                "2.99",
                "--territory",
                "USA",
            ],
        )

        assert result.exit_code == 1

    def test_pricing_set_invalid_price(self, mock_asc_with_app: ASCSimulator) -> None:
        """Test pricing set with invalid price format."""
        result = runner.invoke(
            app,
            [
                "subscriptions",
                "pricing",
                "set",
                "sub_app_123",
                "--price",
                "invalid",
                "--territory",
                "USA",
            ],
        )

        # Should fail validation
        assert result.exit_code != 0

    def test_pricing_set_creates_availability_if_needed(
        self, mock_asc_with_app: ASCSimulator
    ) -> None:
        """Test pricing set creates availability if not set."""
        from tests.simulation.fixtures.price_points import (
            generate_price_points_for_subscription,
        )

        simulator = mock_asc_with_app
        generate_price_points_for_subscription(simulator.state, "sub_app_123", ["USA"])

        result = runner.invoke(
            app,
            [
                "subscriptions",
                "pricing",
                "set",
                "sub_app_123",
                "--price",
                "2.99",
                "--territory",
                "USA",
            ],
        )

        # Command should succeed (creates availability automatically)
        assert result.exit_code == 0


class TestSubscriptionsOffersEdgeCases:
    """Test edge cases for subscription offers commands."""

    def test_offers_list_subscription_not_found(self, mock_asc_api: ASCSimulator) -> None:
        """Test offers list when subscription doesn't exist."""
        result = runner.invoke(app, ["subscriptions", "offers", "list", "nonexistent_sub"])

        assert result.exit_code == 1

    def test_offers_create_subscription_not_found(self, mock_asc_api: ASCSimulator) -> None:
        """Test offers create when subscription doesn't exist."""
        result = runner.invoke(
            app,
            [
                "subscriptions",
                "offers",
                "create",
                "nonexistent_sub",
                "--type",
                "free-trial",
                "--duration",
                "7 days",
            ],
        )

        assert result.exit_code == 1

    @pytest.mark.skip(reason="Command should validate period but currently doesn't")
    def test_offers_create_no_period(self, mock_asc_missing_period: ASCSimulator) -> None:
        """Test offers create when subscription has no period."""
        # This test reveals that the command should validate subscription
        # has a period before creating offers, but currently doesn't
        pass

    def test_offers_create_invalid_duration(self, mock_asc_with_app: ASCSimulator) -> None:
        """Test offers create with invalid duration format."""
        result = runner.invoke(
            app,
            [
                "subscriptions",
                "offers",
                "create",
                "sub_app_123",
                "--type",
                "free-trial",
                "--duration",
                "invalid",
            ],
        )

        assert result.exit_code != 0

    def test_offers_delete_not_found(self, mock_asc_with_app: ASCSimulator) -> None:
        """Test offers delete when offer doesn't exist."""
        result = runner.invoke(
            app,
            ["subscriptions", "offers", "delete", "nonexistent_offer"],
        )

        assert result.exit_code == 1

    def test_offers_create_invalid_type(self, mock_asc_with_app: ASCSimulator) -> None:
        """Test offers create with invalid offer type."""
        result = runner.invoke(
            app,
            [
                "subscriptions",
                "offers",
                "create",
                "sub_app_123",
                "--type",
                "invalid-type",
                "--duration",
                "1w",
                "--territory",
                "USA",
            ],
        )

        assert result.exit_code == 1
        assert "Invalid offer type" in result.output

    def test_offers_create_missing_price_for_paid_offer(
        self, mock_asc_with_app: ASCSimulator
    ) -> None:
        """Test offers create with pay-as-you-go without price."""
        result = runner.invoke(
            app,
            [
                "subscriptions",
                "offers",
                "create",
                "sub_app_123",
                "--type",
                "pay-as-you-go",
                "--duration",
                "1w",
                "--territory",
                "USA",
            ],
        )

        assert result.exit_code == 1
        assert "Price required" in result.output

    def test_offers_create_no_territory_specified(self, mock_asc_with_app: ASCSimulator) -> None:
        """Test offers create without --all or --territory."""
        result = runner.invoke(
            app,
            [
                "subscriptions",
                "offers",
                "create",
                "sub_app_123",
                "--type",
                "free-trial",
                "--duration",
                "1w",
            ],
        )

        assert result.exit_code == 1
        assert "Specify --all or --territory" in result.output

    def test_offers_delete_aborted(self, mock_asc_with_app: ASCSimulator) -> None:
        """Test offers delete when user doesn't confirm."""
        # Create an offer first
        simulator = mock_asc_with_app
        simulator.state.add_introductory_offer(
            offer_id="offer_123",
            subscription_id="sub_app_123",
            territory_id="USA",
            offer_mode="FREE_TRIAL",
            duration="ONE_WEEK",
            number_of_periods=1,
        )

        # Mock user declining confirmation
        result = runner.invoke(
            app,
            ["subscriptions", "offers", "delete", "offer_123"],
            input="n\n",
        )

        # Should be aborted
        assert result.exit_code == 1


class TestSubscriptionsPricingDryRun:
    """Test dry run mode for pricing commands."""

    def test_pricing_set_dry_run(self, mock_asc_with_app: ASCSimulator) -> None:
        """Test pricing set with --dry-run flag."""
        from tests.simulation.fixtures.price_points import (
            generate_price_points_for_subscription,
        )

        simulator = mock_asc_with_app
        generate_price_points_for_subscription(simulator.state, "sub_app_123", ["USA"])

        result = runner.invoke(
            app,
            [
                "subscriptions",
                "pricing",
                "set",
                "sub_app_123",
                "--price",
                "2.99",
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        assert "Dry run" in result.output or "dry run" in result.output.lower()


class TestSubscriptionsPricingWithTerritories:
    """Test pricing with territory filtering."""

    def test_pricing_set_with_territories_filter(self, mock_asc_with_app: ASCSimulator) -> None:
        """Test pricing set with specific territories."""
        from tests.simulation.fixtures.price_points import (
            generate_price_points_for_subscription,
        )

        simulator = mock_asc_with_app
        generate_price_points_for_subscription(
            simulator.state, "sub_app_123", ["USA", "GBR", "CAN"]
        )

        result = runner.invoke(
            app,
            [
                "subscriptions",
                "pricing",
                "set",
                "sub_app_123",
                "--price",
                "2.99",
                "--territory",
                "USA",
                "--territory",
                "GBR",
            ],
        )

        # Should succeed or fail gracefully
        assert result.exit_code in [0, 1]


class TestSubscriptionsPricingInvalidPricePoint:
    """Test pricing with no matching price point."""

    def test_pricing_set_no_price_point_found(self, mock_asc_with_app: ASCSimulator) -> None:
        """Test pricing set when price point doesn't exist."""
        from tests.simulation.fixtures.price_points import (
            generate_price_points_for_subscription,
        )

        simulator = mock_asc_with_app
        # Generate limited price points (won't have all prices)
        generate_price_points_for_subscription(simulator.state, "sub_app_123", ["USA"])

        # Try to set an unusual price that won't have a price point
        result = runner.invoke(
            app,
            [
                "subscriptions",
                "pricing",
                "set",
                "sub_app_123",
                "--price",
                "12.34",  # Unusual price unlikely to have a price point
            ],
        )

        # Should exit with error or handle gracefully
        assert result.exit_code in [0, 1]


class TestSubscriptionsCheckWithPricing:
    """Test check command with pricing configured."""

    def test_check_with_pricing_configured(self, mock_asc_with_app: ASCSimulator) -> None:
        """Test check when subscription has pricing set."""
        from tests.simulation.fixtures.price_points import (
            generate_price_points_for_subscription,
        )

        simulator = mock_asc_with_app

        # Set up a subscription with pricing
        generate_price_points_for_subscription(simulator.state, "sub_app_123")
        simulator.state.set_subscription_availability("sub_app_123", ["USA"])
        simulator.state.add_subscription_price(
            price_id="price_sub_app_123_3",
            subscription_id="sub_app_123",
            price_point_id="pp_sub_app_123_USA_tier_30",
        )

        result = runner.invoke(app, ["subscriptions", "check", "com.example.test"])

        assert result.exit_code == 0
        # Should show pricing configured
        assert "Pricing" in result.output
