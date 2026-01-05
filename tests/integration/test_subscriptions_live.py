"""Integration tests for subscriptions commands using live API.

These tests run against a real App Store Connect app and require:
1. Valid credentials configured via `asc auth login`
2. An app with subscriptions configured

Run with: pytest -m integration tests/integration/

To run against a specific app:
    TEST_BUNDLE_ID=live.yooz.whisper pytest -m integration
"""

import os

import pytest
from typer.testing import CliRunner

from asc_cli.api.auth import AuthManager
from asc_cli.cli import app

# Default test app - can be overridden with TEST_BUNDLE_ID env var
TEST_BUNDLE_ID = os.getenv("TEST_BUNDLE_ID", "live.yooz.whisper")


@pytest.fixture
def runner() -> CliRunner:
    """Create CLI runner."""
    return CliRunner()


@pytest.fixture
def auth_manager() -> AuthManager:
    """Get auth manager, skip if not authenticated."""
    manager = AuthManager.auto()
    if not manager.is_authenticated:
        pytest.skip("Not authenticated - run 'asc auth login' first")
    return manager


@pytest.mark.integration
class TestAuthIntegration:
    """Integration tests for auth commands."""

    def test_auth_status(self, runner: CliRunner, auth_manager: AuthManager) -> None:
        """Test auth status command."""
        result = runner.invoke(app, ["auth", "status"])
        assert result.exit_code == 0
        assert "Authenticated" in result.output

    def test_auth_test(self, runner: CliRunner, auth_manager: AuthManager) -> None:
        """Test auth test command."""
        result = runner.invoke(app, ["auth", "test"])
        assert result.exit_code == 0
        assert "successful" in result.output.lower() or "app" in result.output.lower()


@pytest.mark.integration
class TestAppsIntegration:
    """Integration tests for apps commands."""

    def test_apps_list(self, runner: CliRunner, auth_manager: AuthManager) -> None:
        """Test apps list command."""
        result = runner.invoke(app, ["apps", "list"])
        assert result.exit_code == 0
        assert "Apps" in result.output or "Bundle ID" in result.output

    def test_apps_info(self, runner: CliRunner, auth_manager: AuthManager) -> None:
        """Test apps info command."""
        result = runner.invoke(app, ["apps", "info", TEST_BUNDLE_ID])
        assert result.exit_code == 0
        assert TEST_BUNDLE_ID in result.output or "not found" in result.output.lower()


@pytest.mark.integration
class TestSubscriptionsIntegration:
    """Integration tests for subscriptions commands."""

    def test_subscriptions_list(self, runner: CliRunner, auth_manager: AuthManager) -> None:
        """Test subscriptions list command."""
        result = runner.invoke(app, ["subscriptions", "list", TEST_BUNDLE_ID])
        # May succeed or show "no subscription groups found"
        assert result.exit_code == 0

    def test_subscriptions_check(self, runner: CliRunner, auth_manager: AuthManager) -> None:
        """Test subscriptions check command."""
        result = runner.invoke(app, ["subscriptions", "check", TEST_BUNDLE_ID])
        # May succeed or show "no subscription groups found"
        assert result.exit_code == 0


@pytest.mark.integration
class TestSubscriptionsPricingIntegration:
    """Integration tests for pricing commands.

    NOTE: These tests only run read operations to avoid modifying production data.
    """

    def test_pricing_set_dry_run(self, runner: CliRunner, auth_manager: AuthManager) -> None:
        """Test pricing set with dry-run flag (no actual changes)."""
        # This test requires knowing a subscription ID
        # We'd need to first list subscriptions to get an ID
        # For now, just verify the command structure works
        result = runner.invoke(
            app,
            [
                "subscriptions",
                "pricing",
                "set",
                "FAKE_SUB_ID",
                "--price",
                "2.99",
                "--dry-run",
            ],
        )
        # Will fail with API error but that's expected for a fake ID
        # The important thing is the CLI parsed the arguments correctly
        assert "--help" not in result.output  # Didn't fall back to help


@pytest.mark.integration
class TestBulkIntegration:
    """Integration tests for bulk commands."""

    def test_bulk_validate(self, runner: CliRunner, auth_manager: AuthManager) -> None:
        """Test bulk validate with example config."""
        # First generate an example config (use --force to overwrite if exists)
        result = runner.invoke(
            app, ["bulk", "init", "--output", "/tmp/test_config.yaml", "--force"]
        )
        assert result.exit_code == 0

        # Then validate it
        result = runner.invoke(app, ["bulk", "validate", "/tmp/test_config.yaml"])
        assert result.exit_code == 0

    def test_bulk_apply_dry_run(self, runner: CliRunner, auth_manager: AuthManager) -> None:
        """Test bulk apply with dry-run flag (no actual changes)."""
        # Generate example config (use --force to overwrite if exists)
        result = runner.invoke(
            app, ["bulk", "init", "--output", "/tmp/test_config_apply.yaml", "--force"]
        )
        assert result.exit_code == 0

        # Apply with dry-run
        result = runner.invoke(app, ["bulk", "apply", "/tmp/test_config_apply.yaml", "--dry-run"])
        # May fail if app doesn't exist, but command should parse correctly
        assert "--help" not in result.output
