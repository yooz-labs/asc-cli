"""Tests for authentication CLI commands."""

import os
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from asc_cli.api.auth import CREDENTIALS_FILE
from asc_cli.cli import app
from tests.test_keys import get_test_private_key

runner = CliRunner()


class TestAuthLogin:
    """Tests for 'asc auth login' command."""

    def test_login_with_all_options(self, tmp_path: Path) -> None:
        """Test login with all options provided."""
        # Create a test key file
        key_file = tmp_path / "test_key.p8"
        key_file.write_text(get_test_private_key())

        result = runner.invoke(
            app,
            [
                "auth",
                "login",
                "--issuer-id",
                "test-issuer",
                "--key-id",
                "test-key",
                "--key-path",
                str(key_file),
            ],
        )

        assert result.exit_code == 0
        assert "Authentication successful" in result.stdout
        assert "Credentials saved" in result.stdout

    def test_login_with_nonexistent_key_file(self) -> None:
        """Test login fails with nonexistent key file."""
        result = runner.invoke(
            app,
            [
                "auth",
                "login",
                "--issuer-id",
                "test-issuer",
                "--key-id",
                "test-key",
                "--key-path",
                "/nonexistent/path/key.p8",
            ],
        )

        assert result.exit_code == 1
        assert "Key file not found" in result.stdout

    def test_login_with_invalid_key_format(self, tmp_path: Path) -> None:
        """Test login fails with invalid key format."""
        key_file = tmp_path / "invalid_key.p8"
        key_file.write_text("not a valid private key")

        result = runner.invoke(
            app,
            [
                "auth",
                "login",
                "--issuer-id",
                "test-issuer",
                "--key-id",
                "test-key",
                "--key-path",
                str(key_file),
            ],
        )

        assert result.exit_code == 1
        assert "Invalid private key format" in result.stdout

    def test_login_interactive_mode(self, tmp_path: Path) -> None:
        """Test login in interactive mode."""
        # Create a test key file
        key_file = tmp_path / "test_key.p8"
        key_file.write_text(get_test_private_key())

        # Mock Prompt.ask to provide interactive input
        with patch("asc_cli.commands.auth.Prompt.ask") as mock_prompt:
            mock_prompt.side_effect = ["test-issuer", "test-key", str(key_file)]

            result = runner.invoke(app, ["auth", "login"])

            assert result.exit_code == 0
            assert "Authentication successful" in result.stdout
            assert mock_prompt.call_count == 3

    def test_login_with_token_generation_failure(self, tmp_path: Path) -> None:
        """Test login fails when token generation fails."""
        key_file = tmp_path / "test_key.p8"
        # Use a key with valid format but invalid content
        key_content = """-----BEGIN PRIVATE KEY-----
INVALID_KEY_CONTENT_THAT_WILL_FAIL_TOKEN_GENERATION
-----END PRIVATE KEY-----"""
        key_file.write_text(key_content)

        result = runner.invoke(
            app,
            [
                "auth",
                "login",
                "--issuer-id",
                "test-issuer",
                "--key-id",
                "test-key",
                "--key-path",
                str(key_file),
            ],
        )

        assert result.exit_code == 1
        assert "Authentication failed" in result.stdout


class TestAuthStatus:
    """Tests for 'asc auth status' command."""

    def test_status_when_authenticated(self, tmp_path: Path) -> None:
        """Test status command when authenticated."""
        with patch.dict(
            os.environ,
            {
                "ASC_ISSUER_ID": "test-issuer",
                "ASC_KEY_ID": "test-key",
                "ASC_PRIVATE_KEY": get_test_private_key(),
            },
        ):
            result = runner.invoke(app, ["auth", "status"])

            assert result.exit_code == 0
            assert "Authenticated" in result.stdout
            assert "Token generation: OK" in result.stdout

    def test_status_with_invalid_credentials(self, tmp_path: Path) -> None:
        """Test status command shows warning when token generation fails."""
        # Create invalid key to trigger token generation failure
        key_file = tmp_path / "invalid_key.p8"
        key_file.write_text("-----BEGIN EC PRIVATE KEY-----\ninvalid\n-----END EC PRIVATE KEY-----")

        with patch.dict(
            os.environ,
            {
                "ASC_ISSUER_ID": "test-issuer",
                "ASC_KEY_ID": "test-key",
                "ASC_PRIVATE_KEY": key_file.read_text(),
            },
        ):
            result = runner.invoke(app, ["auth", "status"])

            assert result.exit_code == 0
            assert "Authenticated" in result.stdout
            assert "Warning" in result.stdout or "failed" in result.stdout

    def test_status_when_not_authenticated(self) -> None:
        """Test status command when not authenticated."""
        # Mock both credential sources to return None
        with (
            patch("asc_cli.api.auth.Credentials.from_env", return_value=None),
            patch("asc_cli.api.auth.Credentials.from_file", return_value=None),
        ):
            result = runner.invoke(app, ["auth", "status"])

            assert result.exit_code == 0
            assert "Not authenticated" in result.stdout
            assert "asc auth login" in result.stdout


class TestAuthLogout:
    """Tests for 'asc auth logout' command."""

    def test_logout_removes_credentials(self, tmp_path: Path) -> None:
        """Test logout removes stored credentials."""
        # First login to create credentials
        key_file = tmp_path / "test_key.p8"
        key_file.write_text(get_test_private_key())

        # Login first
        result = runner.invoke(
            app,
            [
                "auth",
                "login",
                "--issuer-id",
                "test-issuer",
                "--key-id",
                "test-key",
                "--key-path",
                str(key_file),
            ],
        )
        assert result.exit_code == 0

        # Now logout
        result = runner.invoke(app, ["auth", "logout"])

        assert result.exit_code == 0
        assert "Credentials removed" in result.stdout

    def test_logout_when_no_credentials(self) -> None:
        """Test logout when no credentials exist."""
        # Ensure credentials file doesn't exist
        if CREDENTIALS_FILE.exists():
            CREDENTIALS_FILE.unlink()

        result = runner.invoke(app, ["auth", "logout"])

        assert result.exit_code == 0
        assert "No stored credentials found" in result.stdout


class TestAuthTest:
    """Tests for 'asc auth test' command."""

    def test_auth_test_successful(self, mock_asc_api: None) -> None:
        """Test 'asc auth test' command with successful connection."""
        result = runner.invoke(app, ["auth", "test"])

        assert result.exit_code == 0
        assert "Connection successful" in result.stdout
        assert "Found" in result.stdout
        assert "app(s)" in result.stdout

    def test_auth_test_with_multiple_apps(self, mock_asc_whisper: None) -> None:
        """Test 'asc auth test' displays app list."""
        result = runner.invoke(app, ["auth", "test"])

        assert result.exit_code == 0
        assert "Connection successful" in result.stdout
        assert "Yooz Whisper" in result.stdout

    def test_auth_test_connection_failure(self) -> None:
        """Test 'asc auth test' handles connection errors."""
        # Set invalid credentials
        with patch.dict(
            os.environ,
            {
                "ASC_ISSUER_ID": "invalid",
                "ASC_KEY_ID": "invalid",
                "ASC_PRIVATE_KEY": "invalid",
            },
        ):
            result = runner.invoke(app, ["auth", "test"])

            assert result.exit_code == 1
            assert "Error" in result.stdout

    def test_auth_test_with_many_apps(self, mock_asc_api) -> None:
        """Test 'asc auth test' displays truncated list with many apps."""
        # Add 10 apps to trigger the "... and X more" message
        for i in range(10):
            mock_asc_api.state.add_app(f"app_{i}", f"com.test.app{i}", f"Test App {i}")

        result = runner.invoke(app, ["auth", "test"])

        assert result.exit_code == 0
        assert "Connection successful" in result.stdout
        assert "Found 10 app(s)" in result.stdout
        # Should show "... and 5 more" message
        assert "... and 5 more" in result.stdout
