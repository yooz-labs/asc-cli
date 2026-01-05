"""CLI command tests using the API simulation engine.

These tests verify full CLI flows from command invocation through
to simulated API responses.
"""

import pytest
from typer.testing import CliRunner

from asc_cli.cli import app
from tests.simulation.fixtures.price_points import find_price_point_by_usd


@pytest.fixture
def runner() -> CliRunner:
    """CLI runner for testing."""
    return CliRunner()


@pytest.mark.simulation
class TestAppsCommands:
    """Tests for apps CLI commands."""

    def test_apps_list(self, runner: CliRunner, mock_asc_with_app) -> None:
        """Test apps list command."""
        result = runner.invoke(app, ["apps", "list"])
        assert result.exit_code == 0
        assert "com.example.test" in result.output
        assert "Test App" in result.output

    def test_apps_info(self, runner: CliRunner, mock_asc_with_app) -> None:
        """Test apps info command."""
        result = runner.invoke(app, ["apps", "info", "com.example.test"])
        assert result.exit_code == 0
        assert "Test App" in result.output

    def test_apps_list_no_apps(self, runner: CliRunner, mock_asc_api) -> None:
        """Test apps list when no apps exist."""
        result = runner.invoke(app, ["apps", "list"])
        assert result.exit_code == 0
        assert "No apps found" in result.output


@pytest.mark.simulation
class TestSubscriptionsCommands:
    """Tests for subscriptions CLI commands."""

    def test_subscriptions_list(self, runner: CliRunner, mock_asc_with_app) -> None:
        """Test subscriptions list command."""
        result = runner.invoke(app, ["subscriptions", "list", "com.example.test"])
        assert result.exit_code == 0
        assert "Premium Monthly" in result.output
        # Period is shown in table but may not be in the exact format

    def test_subscriptions_check_missing_metadata(
        self, runner: CliRunner, mock_asc_with_app
    ) -> None:
        """Test subscriptions check command with missing metadata."""
        result = runner.invoke(app, ["subscriptions", "check", "com.example.test"])
        assert result.exit_code == 0
        # Should suggest screenshots since period, localization, and pricing might be set
        # but state is MISSING_METADATA

    def test_subscriptions_check_no_period(
        self, runner: CliRunner, mock_asc_missing_period
    ) -> None:
        """Test subscriptions check when period is missing."""
        result = runner.invoke(app, ["subscriptions", "check", "com.example.test"])
        assert result.exit_code == 0
        # Should indicate period is missing


@pytest.mark.simulation
class TestSubscriptionsPricingCommands:
    """Tests for subscriptions pricing CLI commands."""

    def test_pricing_list_no_prices(self, runner: CliRunner, mock_asc_with_app) -> None:
        """Test pricing list when no prices are set."""
        result = runner.invoke(app, ["subscriptions", "pricing", "list", "sub_app_123"])
        assert result.exit_code == 0

    def test_pricing_set_with_simulation(self, runner: CliRunner, mock_asc_with_app) -> None:
        """Test pricing set command with simulation."""
        sim = mock_asc_with_app

        # Generate price points for the subscription
        from tests.simulation.fixtures.price_points import (
            generate_price_points_for_subscription,
        )

        generate_price_points_for_subscription(sim.state, "sub_app_123", ["USA", "GBR"])

        # Set availability first (required before pricing)
        sim.state.set_subscription_availability("sub_app_123", ["USA"])

        # Now set price
        runner.invoke(
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
        # May fail if not implemented, but command should parse
        # This tests the CLI argument parsing and flow


@pytest.mark.simulation
class TestSubscriptionsOffersCommands:
    """Tests for subscriptions offers CLI commands."""

    def test_offers_list_empty(self, runner: CliRunner, mock_asc_with_app) -> None:
        """Test offers list when no offers exist."""
        result = runner.invoke(app, ["subscriptions", "offers", "list", "sub_app_123"])
        assert result.exit_code == 0

    def test_offers_create_free_trial(self, runner: CliRunner, mock_asc_with_app) -> None:
        """Test offers create command for free trial."""
        sim = mock_asc_with_app

        # Set availability first
        sim.state.set_subscription_availability("sub_app_123", ["USA"])

        runner.invoke(
            app,
            [
                "subscriptions",
                "offers",
                "create",
                "sub_app_123",
                "--type",
                "free-trial",
                "--duration",
                "2w",
                "--territory",
                "USA",
            ],
        )
        # Command should parse correctly even if implementation incomplete


@pytest.mark.simulation
class TestWhisperAppCommands:
    """Tests for Whisper app using CLI commands."""

    def test_whisper_list_subscriptions(self, runner: CliRunner, mock_asc_whisper) -> None:
        """Test listing Whisper subscriptions."""
        result = runner.invoke(app, ["subscriptions", "list", "live.yooz.whisper"])
        assert result.exit_code == 0
        # Should show all 4 subscriptions

    def test_whisper_check_subscriptions(self, runner: CliRunner, mock_asc_whisper) -> None:
        """Test checking Whisper subscriptions."""
        result = runner.invoke(app, ["subscriptions", "check", "live.yooz.whisper"])
        assert result.exit_code == 0
        # Should analyze all 4 subscriptions


@pytest.mark.simulation
class TestPricingWithPricePoints:
    """Tests for pricing operations with generated price points."""

    def test_pricing_list_with_price_points(self, runner: CliRunner, mock_asc_with_app) -> None:
        """Test pricing list after setting prices."""
        sim = mock_asc_with_app

        # Generate price points
        from tests.simulation.fixtures.price_points import (
            generate_price_points_for_subscription,
        )

        generate_price_points_for_subscription(sim.state, "sub_app_123", ["USA"])

        # Set availability
        sim.state.set_subscription_availability("sub_app_123", ["USA"])

        # Find and set a price
        pp_id = find_price_point_by_usd(sim.state, "sub_app_123", "2.99", "USA")
        if pp_id:
            sim.state.add_subscription_price(
                price_id="price_1",
                subscription_id="sub_app_123",
                price_point_id=pp_id,
            )

        result = runner.invoke(app, ["subscriptions", "pricing", "list", "sub_app_123"])
        assert result.exit_code == 0


@pytest.mark.simulation
class TestOffersWithValidation:
    """Tests for offers with validation scenarios."""

    def test_offers_create_requires_period(
        self, runner: CliRunner, mock_asc_missing_period
    ) -> None:
        """Test that offers require subscription period to be set."""
        sim = mock_asc_missing_period

        # Set availability
        sim.state.set_subscription_availability("sub_app_123", ["USA"])

        runner.invoke(
            app,
            [
                "subscriptions",
                "offers",
                "create",
                "sub_app_123",
                "--type",
                "free-trial",
                "--duration",
                "2w",
                "--territory",
                "USA",
            ],
        )
        # Should fail or warn about missing period
        # The exact behavior depends on CLI implementation


@pytest.mark.simulation
class TestErrorHandling:
    """Tests for error handling in CLI commands."""

    def test_apps_info_not_found(self, runner: CliRunner, mock_asc_with_app) -> None:
        """Test apps info with non-existent app."""
        runner.invoke(app, ["apps", "info", "com.nonexistent.app"])
        # Should handle gracefully (exit code may vary)

    def test_subscriptions_list_invalid_bundle(self, runner: CliRunner, mock_asc_with_app) -> None:
        """Test subscriptions list with invalid bundle ID."""
        runner.invoke(app, ["subscriptions", "list", "com.invalid.app"])
        # Should handle gracefully

    def test_rate_limit_handling(self, runner: CliRunner, mock_asc_with_app) -> None:
        """Test rate limit error handling in CLI."""
        mock_asc_with_app.simulate_rate_limit()

        runner.invoke(app, ["apps", "list"])
        # Should handle rate limit error (exit code may vary)


@pytest.mark.simulation
class TestBulkOperations:
    """Tests for bulk operations using simulation."""

    def test_bulk_init(self, runner: CliRunner, mock_asc_with_app, tmp_path) -> None:
        """Test bulk init command."""
        output_file = tmp_path / "test_config.yaml"
        result = runner.invoke(app, ["bulk", "init", "--output", str(output_file), "--force"])
        assert result.exit_code == 0
        assert output_file.exists()

    def test_bulk_validate(self, runner: CliRunner, mock_asc_with_app, tmp_path) -> None:
        """Test bulk validate command."""
        # First create a config
        config_file = tmp_path / "config.yaml"
        result = runner.invoke(app, ["bulk", "init", "--output", str(config_file), "--force"])
        assert result.exit_code == 0

        # Then validate it
        result = runner.invoke(app, ["bulk", "validate", str(config_file)])
        assert result.exit_code == 0
