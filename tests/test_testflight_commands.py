"""Tests for TestFlight CLI commands."""

from typer.testing import CliRunner

from asc_cli.cli import app

runner = CliRunner()


class TestTestFlightBuildsCommands:
    """Tests for TestFlight builds commands."""

    def test_builds_list(self) -> None:
        """Test builds list command (stub)."""
        result = runner.invoke(app, ["testflight", "builds", "list", "com.example.app"])

        assert result.exit_code == 0
        assert "Build listing coming soon" in result.output

    def test_builds_expire(self) -> None:
        """Test builds expire command (stub)."""
        result = runner.invoke(app, ["testflight", "builds", "expire", "build-123"])

        assert result.exit_code == 0
        assert "Build expiration coming soon" in result.output


class TestTestFlightGroupsCommands:
    """Tests for TestFlight groups commands."""

    def test_groups_list(self) -> None:
        """Test groups list command (stub)."""
        result = runner.invoke(app, ["testflight", "groups", "list", "com.example.app"])

        assert result.exit_code == 0
        assert "Group listing coming soon" in result.output

    def test_groups_create(self) -> None:
        """Test groups create command (stub)."""
        result = runner.invoke(
            app,
            [
                "testflight",
                "groups",
                "create",
                "com.example.app",
                "--name",
                "Beta Testers",
            ],
        )

        assert result.exit_code == 0
        assert "Group creation coming soon" in result.output

    def test_groups_create_public(self) -> None:
        """Test groups create command with public flag (stub)."""
        result = runner.invoke(
            app,
            [
                "testflight",
                "groups",
                "create",
                "com.example.app",
                "--name",
                "Public Beta",
                "--public",
            ],
        )

        assert result.exit_code == 0
        assert "Group creation coming soon" in result.output


class TestTestFlightTestersCommands:
    """Tests for TestFlight testers commands."""

    def test_testers_list(self) -> None:
        """Test testers list command (stub)."""
        result = runner.invoke(app, ["testflight", "testers", "list", "com.example.app"])

        assert result.exit_code == 0
        assert "Tester listing coming soon" in result.output

    def test_testers_add(self) -> None:
        """Test testers add command (stub)."""
        result = runner.invoke(
            app,
            [
                "testflight",
                "testers",
                "add",
                "com.example.app",
                "--email",
                "tester@example.com",
            ],
        )

        assert result.exit_code == 0
        assert "Tester addition coming soon" in result.output

    def test_testers_add_with_group(self) -> None:
        """Test testers add command with group (stub)."""
        result = runner.invoke(
            app,
            [
                "testflight",
                "testers",
                "add",
                "com.example.app",
                "--email",
                "tester@example.com",
                "--group",
                "Beta Testers",
            ],
        )

        assert result.exit_code == 0
        assert "Tester addition coming soon" in result.output

    def test_testers_remove(self) -> None:
        """Test testers remove command (stub)."""
        result = runner.invoke(
            app,
            [
                "testflight",
                "testers",
                "remove",
                "com.example.app",
                "--email",
                "tester@example.com",
            ],
        )

        assert result.exit_code == 0
        assert "Tester removal coming soon" in result.output
