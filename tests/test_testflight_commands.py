"""Tests for TestFlight CLI commands using simulation engine.

These tests cover builds, groups, testers, and related operations.
"""

import pytest
from typer.testing import CliRunner

from asc_cli.cli import app


@pytest.fixture
def runner() -> CliRunner:
    """CLI runner for testing."""
    return CliRunner()


# =============================================================================
# Builds Commands
# =============================================================================


@pytest.mark.simulation
class TestTestFlightBuildsCommands:
    """Tests for TestFlight builds commands."""

    def test_builds_list(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test builds list command."""
        result = runner.invoke(app, ["testflight", "builds", "list", "com.example.test"])
        assert result.exit_code == 0
        assert "0.2.7" in result.output or "build_3" in result.output

    def test_builds_list_with_limit(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test builds list with limit."""
        result = runner.invoke(
            app, ["testflight", "builds", "list", "com.example.test", "--limit", "2"]
        )
        assert result.exit_code == 0

    def test_builds_list_no_builds(self, runner: CliRunner, mock_asc_api) -> None:
        """Test builds list when no builds exist."""
        mock_asc_api.state.add_app("app_empty", "com.example.empty", "Empty App")
        result = runner.invoke(app, ["testflight", "builds", "list", "com.example.empty"])
        assert result.exit_code == 0
        assert "No builds found" in result.output

    def test_builds_list_app_not_found(self, runner: CliRunner, mock_asc_api) -> None:
        """Test builds list with non-existent app."""
        result = runner.invoke(app, ["testflight", "builds", "list", "com.nonexistent.app"])
        assert result.exit_code == 0
        assert "not found" in result.output.lower()

    def test_builds_update_whats_new(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test builds update command with What's New text."""
        result = runner.invoke(
            app,
            [
                "testflight",
                "builds",
                "update",
                "com.example.test",
                "--build",
                "13",
                "--whats-new",
                "New feature: dark mode support",
            ],
        )
        assert result.exit_code == 0
        # Should either update existing or create new localization
        assert (
            "What's New" in result.output
            or "Updated" in result.output
            or "Created" in result.output
        )

    def test_builds_update_whats_new_from_file(
        self, runner: CliRunner, mock_asc_with_testflight, tmp_path
    ) -> None:
        """Test builds update command with What's New from file."""
        whats_new_file = tmp_path / "whats_new.txt"
        whats_new_file.write_text("Release notes from file\n- Bug fixes\n- Improvements")

        result = runner.invoke(
            app,
            [
                "testflight",
                "builds",
                "update",
                "com.example.test",
                "--build",
                "13",
                "--whats-new-file",
                str(whats_new_file),
            ],
        )
        assert result.exit_code == 0

    def test_builds_update_no_whats_new(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test builds update fails without What's New."""
        result = runner.invoke(
            app,
            ["testflight", "builds", "update", "com.example.test", "--build", "13"],
        )
        assert result.exit_code == 1
        assert "required" in result.output.lower()

    def test_builds_update_build_not_found(
        self, runner: CliRunner, mock_asc_with_testflight
    ) -> None:
        """Test builds update with non-existent build."""
        result = runner.invoke(
            app,
            [
                "testflight",
                "builds",
                "update",
                "com.example.test",
                "--build",
                "999",
                "--whats-new",
                "Test",
            ],
        )
        assert result.exit_code == 0
        assert "not found" in result.output.lower()

    def test_builds_encryption_exempt(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test builds encryption command with exempt flag."""
        result = runner.invoke(
            app,
            [
                "testflight",
                "builds",
                "encryption",
                "com.example.test",
                "--build",
                "13",
                "--no-encryption",
                "--exempt",
            ],
        )
        assert result.exit_code == 0
        assert "encryption" in result.output.lower()

    def test_builds_encryption_uses_encryption(
        self, runner: CliRunner, mock_asc_with_testflight
    ) -> None:
        """Test builds encryption command with uses-encryption flag."""
        result = runner.invoke(
            app,
            [
                "testflight",
                "builds",
                "encryption",
                "com.example.test",
                "--build",
                "13",
                "--uses-encryption",
                "--not-exempt",
            ],
        )
        assert result.exit_code == 0

    def test_builds_submit(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test builds submit command."""
        result = runner.invoke(
            app,
            [
                "testflight",
                "builds",
                "submit",
                "com.example.test",
                "--build",
                "13",
            ],
        )
        assert result.exit_code == 0
        assert "Submitted" in result.output or "review" in result.output.lower()

    def test_builds_submit_not_found(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test builds submit with non-existent build."""
        result = runner.invoke(
            app,
            [
                "testflight",
                "builds",
                "submit",
                "com.example.test",
                "--build",
                "999",
            ],
        )
        assert result.exit_code == 0
        assert "not found" in result.output.lower()


# =============================================================================
# Groups Commands
# =============================================================================


@pytest.mark.simulation
class TestTestFlightGroupsCommands:
    """Tests for TestFlight groups commands."""

    def test_groups_list(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test groups list command."""
        result = runner.invoke(app, ["testflight", "groups", "list", "com.example.test"])
        assert result.exit_code == 0
        assert "Internal Testers" in result.output or "External Testers" in result.output

    def test_groups_list_no_groups(self, runner: CliRunner, mock_asc_api) -> None:
        """Test groups list when no groups exist."""
        mock_asc_api.state.add_app("app_empty", "com.example.empty", "Empty App")
        result = runner.invoke(app, ["testflight", "groups", "list", "com.example.empty"])
        assert result.exit_code == 0
        assert "No beta groups found" in result.output

    def test_groups_create(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test groups create command."""
        result = runner.invoke(
            app,
            [
                "testflight",
                "groups",
                "create",
                "com.example.test",
                "--name",
                "New Testers",
            ],
        )
        assert result.exit_code == 0
        assert "Created" in result.output or "New Testers" in result.output

    def test_groups_create_public(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test groups create command with public flag."""
        result = runner.invoke(
            app,
            [
                "testflight",
                "groups",
                "create",
                "com.example.test",
                "--name",
                "Public Beta",
                "--public",
            ],
        )
        assert result.exit_code == 0
        assert "Created" in result.output

    def test_groups_create_public_with_limit(
        self, runner: CliRunner, mock_asc_with_testflight
    ) -> None:
        """Test groups create with public link limit."""
        result = runner.invoke(
            app,
            [
                "testflight",
                "groups",
                "create",
                "com.example.test",
                "--name",
                "Limited Beta",
                "--public",
                "--public-limit",
                "50",
            ],
        )
        assert result.exit_code == 0

    def test_groups_create_internal(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test groups create with internal flag."""
        result = runner.invoke(
            app,
            [
                "testflight",
                "groups",
                "create",
                "com.example.test",
                "--name",
                "Internal Only",
                "--internal",
            ],
        )
        assert result.exit_code == 0

    def test_groups_delete(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test groups delete command."""
        result = runner.invoke(
            app,
            ["testflight", "groups", "delete", "group_external", "--force"],
        )
        assert result.exit_code == 0
        assert "Deleted" in result.output

    def test_groups_delete_not_found(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test groups delete with non-existent group."""
        result = runner.invoke(
            app,
            ["testflight", "groups", "delete", "nonexistent_group", "--force"],
        )
        assert result.exit_code == 0
        # Should handle gracefully

    def test_groups_add_build(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test groups add-build command."""
        result = runner.invoke(
            app,
            [
                "testflight",
                "groups",
                "add-build",
                "group_internal",
                "--build",
                "build_2",
            ],
        )
        assert result.exit_code == 0
        assert "Added" in result.output


# =============================================================================
# Testers Commands
# =============================================================================


@pytest.mark.simulation
class TestTestFlightTestersCommands:
    """Tests for TestFlight testers commands."""

    def test_testers_list(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test testers list command."""
        result = runner.invoke(app, ["testflight", "testers", "list"])
        assert result.exit_code == 0
        assert "alice@example.com" in result.output or "bob@example.com" in result.output

    def test_testers_list_with_email_filter(
        self, runner: CliRunner, mock_asc_with_testflight
    ) -> None:
        """Test testers list with email filter."""
        result = runner.invoke(
            app, ["testflight", "testers", "list", "--email", "alice@example.com"]
        )
        assert result.exit_code == 0

    def test_testers_list_with_limit(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test testers list with limit."""
        result = runner.invoke(app, ["testflight", "testers", "list", "--limit", "1"])
        assert result.exit_code == 0

    def test_testers_list_no_testers(self, runner: CliRunner, mock_asc_api) -> None:
        """Test testers list when no testers exist."""
        result = runner.invoke(app, ["testflight", "testers", "list"])
        assert result.exit_code == 0
        assert "No testers found" in result.output

    def test_testers_add(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test testers add command."""
        result = runner.invoke(
            app,
            [
                "testflight",
                "testers",
                "add",
                "--email",
                "newtester@example.com",
            ],
        )
        assert result.exit_code == 0
        assert "Added" in result.output or "newtester@example.com" in result.output

    def test_testers_add_with_name(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test testers add command with name."""
        result = runner.invoke(
            app,
            [
                "testflight",
                "testers",
                "add",
                "--email",
                "named@example.com",
                "--first-name",
                "Test",
                "--last-name",
                "User",
            ],
        )
        assert result.exit_code == 0

    def test_testers_add_with_group(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test testers add command with group."""
        result = runner.invoke(
            app,
            [
                "testflight",
                "testers",
                "add",
                "--email",
                "grouped@example.com",
                "--group",
                "group_external",
            ],
        )
        assert result.exit_code == 0

    def test_testers_remove(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test testers remove command."""
        result = runner.invoke(
            app,
            ["testflight", "testers", "remove", "tester_2", "--force"],
        )
        assert result.exit_code == 0
        assert "Removed" in result.output

    def test_testers_remove_not_found(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test testers remove with non-existent tester."""
        result = runner.invoke(
            app,
            ["testflight", "testers", "remove", "nonexistent_tester", "--force"],
        )
        assert result.exit_code == 0
        # Should handle gracefully

    def test_testers_add_to_group(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test testers add-to-group command."""
        result = runner.invoke(
            app,
            [
                "testflight",
                "testers",
                "add-to-group",
                "tester_1",
                "--group",
                "group_external",
            ],
        )
        assert result.exit_code == 0
        assert "Added" in result.output

    def test_testers_remove_from_group(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test testers remove-from-group command."""
        result = runner.invoke(
            app,
            [
                "testflight",
                "testers",
                "remove-from-group",
                "tester_2",
                "--group",
                "group_external",
            ],
        )
        assert result.exit_code == 0
        assert "Removed" in result.output


# =============================================================================
# Whisper App Integration Tests
# =============================================================================


@pytest.mark.simulation
class TestWhisperTestFlightCommands:
    """Tests for Whisper app TestFlight commands."""

    def test_whisper_builds_list(self, runner: CliRunner, mock_asc_whisper_testflight) -> None:
        """Test listing Whisper builds."""
        result = runner.invoke(app, ["testflight", "builds", "list", "live.yooz.whisper"])
        assert result.exit_code == 0
        # Should show builds 0.2.6 and 0.2.7

    def test_whisper_groups_list(self, runner: CliRunner, mock_asc_whisper_testflight) -> None:
        """Test listing Whisper beta groups."""
        result = runner.invoke(app, ["testflight", "groups", "list", "live.yooz.whisper"])
        assert result.exit_code == 0
        assert "Beta Testers" in result.output


# =============================================================================
# Error Handling Tests
# =============================================================================


@pytest.mark.simulation
class TestTestFlightErrorHandling:
    """Tests for error handling in TestFlight commands."""

    def test_builds_list_rate_limit(self, runner: CliRunner, mock_asc_with_testflight) -> None:
        """Test rate limit handling for builds list."""
        mock_asc_with_testflight.simulate_rate_limit()
        runner.invoke(app, ["testflight", "builds", "list", "com.example.test"])
        # Should handle rate limit gracefully

    def test_groups_create_app_not_found(self, runner: CliRunner, mock_asc_api) -> None:
        """Test groups create with non-existent app."""
        result = runner.invoke(
            app,
            [
                "testflight",
                "groups",
                "create",
                "com.nonexistent.app",
                "--name",
                "Test Group",
            ],
        )
        assert result.exit_code == 0
        assert "not found" in result.output.lower()

    def test_testers_add_to_group_tester_not_found(
        self, runner: CliRunner, mock_asc_with_testflight
    ) -> None:
        """Test add-to-group with non-existent tester."""
        runner.invoke(
            app,
            [
                "testflight",
                "testers",
                "add-to-group",
                "nonexistent_tester",
                "--group",
                "group_external",
            ],
        )
        # Should handle gracefully


# =============================================================================
# State Tests
# =============================================================================


@pytest.mark.simulation
class TestTestFlightState:
    """Tests for TestFlight state management."""

    def test_state_build_creation(self, asc_state) -> None:
        """Test build creation in state."""
        asc_state.add_app("app_1", "com.test.app", "Test App")
        build = asc_state.add_build(
            "build_1",
            "app_1",
            version="1.0.0",
            build_number="1",
        )

        assert build["id"] == "build_1"
        assert build["attributes"]["version"] == "1.0.0"
        assert "build_1" in asc_state.app_builds.get("app_1", [])

    def test_state_beta_group_creation(self, asc_state) -> None:
        """Test beta group creation in state."""
        asc_state.add_app("app_1", "com.test.app", "Test App")
        group = asc_state.add_beta_group(
            "group_1",
            "app_1",
            "Test Group",
            is_internal=True,
        )

        assert group["id"] == "group_1"
        assert group["attributes"]["name"] == "Test Group"
        assert group["attributes"]["isInternalGroup"] is True

    def test_state_beta_tester_creation(self, asc_state) -> None:
        """Test beta tester creation in state."""
        tester = asc_state.add_beta_tester(
            "tester_1",
            "test@example.com",
            first_name="Test",
            last_name="User",
        )

        assert tester["id"] == "tester_1"
        assert tester["attributes"]["email"] == "test@example.com"

    def test_state_tester_group_relationship(self, asc_state) -> None:
        """Test tester-group relationship in state."""
        asc_state.add_app("app_1", "com.test.app", "Test App")
        asc_state.add_beta_group("group_1", "app_1", "Test Group")
        asc_state.add_beta_tester("tester_1", "test@example.com")

        asc_state.add_beta_tester_to_group("tester_1", "group_1")

        assert "tester_1" in asc_state.beta_group_testers.get("group_1", [])
        assert "group_1" in asc_state.tester_groups.get("tester_1", [])

    def test_state_remove_tester_from_group(self, asc_state) -> None:
        """Test removing tester from group in state."""
        asc_state.add_app("app_1", "com.test.app", "Test App")
        asc_state.add_beta_group("group_1", "app_1", "Test Group")
        asc_state.add_beta_tester("tester_1", "test@example.com")
        asc_state.add_beta_tester_to_group("tester_1", "group_1")

        asc_state.remove_beta_tester_from_group("tester_1", "group_1")

        assert "tester_1" not in asc_state.beta_group_testers.get("group_1", [])
        assert "group_1" not in asc_state.tester_groups.get("tester_1", [])

    def test_state_delete_beta_group(self, asc_state) -> None:
        """Test deleting beta group in state."""
        asc_state.add_app("app_1", "com.test.app", "Test App")
        asc_state.add_beta_group("group_1", "app_1", "Test Group")

        result = asc_state.delete_beta_group("group_1")

        assert result is True
        assert "group_1" not in asc_state.beta_groups

    def test_state_delete_beta_tester(self, asc_state) -> None:
        """Test deleting beta tester in state."""
        asc_state.add_beta_tester("tester_1", "test@example.com")

        result = asc_state.delete_beta_tester("tester_1")

        assert result is True
        assert "tester_1" not in asc_state.beta_testers

    def test_state_build_localization(self, asc_state) -> None:
        """Test build localization creation in state."""
        asc_state.add_app("app_1", "com.test.app", "Test App")
        asc_state.add_build("build_1", "app_1", "1.0.0", "1")

        localization = asc_state.add_beta_build_localization(
            "loc_1",
            "build_1",
            "en-US",
            "Bug fixes and improvements",
        )

        assert localization["attributes"]["whatsNew"] == "Bug fixes and improvements"
        assert "loc_1" in asc_state.build_localizations_map.get("build_1", [])

    def test_state_encryption_declaration(self, asc_state) -> None:
        """Test encryption declaration creation in state."""
        asc_state.add_app("app_1", "com.test.app", "Test App")
        asc_state.add_build("build_1", "app_1", "1.0.0", "1")

        declaration = asc_state.add_app_encryption_declaration(
            "decl_1",
            "build_1",
            uses_encryption=False,
            is_exempt=True,
        )

        assert declaration["attributes"]["usesEncryption"] is False
        assert declaration["attributes"]["isExempt"] is True

    def test_state_submit_for_review(self, asc_state) -> None:
        """Test submitting build for review in state."""
        asc_state.add_app("app_1", "com.test.app", "Test App")
        asc_state.add_build("build_1", "app_1", "1.0.0", "1")

        submission = asc_state.submit_build_for_beta_review("build_1")

        assert submission["type"] == "betaAppReviewSubmissions"
        assert submission["attributes"]["betaReviewState"] == "WAITING_FOR_REVIEW"

    def test_state_reset_clears_testflight(self, asc_state) -> None:
        """Test that reset clears TestFlight state."""
        asc_state.add_app("app_1", "com.test.app", "Test App")
        asc_state.add_build("build_1", "app_1", "1.0.0", "1")
        asc_state.add_beta_group("group_1", "app_1", "Test Group")
        asc_state.add_beta_tester("tester_1", "test@example.com")

        asc_state.reset()

        assert len(asc_state.builds) == 0
        assert len(asc_state.beta_groups) == 0
        assert len(asc_state.beta_testers) == 0
        assert len(asc_state.app_builds) == 0
