"""Tests for authentication module."""

import os
from pathlib import Path
from unittest.mock import patch

from asc_cli.api.auth import AuthManager, Credentials


class TestCredentials:
    """Tests for Credentials class."""

    def test_from_env_missing(self) -> None:
        """Test loading from empty environment."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("asc_cli.api.auth.load_dotenv"),  # Prevent .env loading
        ):
            result = Credentials.from_env()
            assert result is None

    def test_from_env_partial(self) -> None:
        """Test loading with partial environment."""
        with (
            patch.dict(os.environ, {"ASC_ISSUER_ID": "test"}, clear=True),
            patch("asc_cli.api.auth.load_dotenv"),  # Prevent .env loading
        ):
            result = Credentials.from_env()
            assert result is None

    def test_from_env_with_key_content(self) -> None:
        """Test loading with key content in env."""
        env = {
            "ASC_ISSUER_ID": "test-issuer",
            "ASC_KEY_ID": "TESTKEY123",
            "ASC_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
        }
        with (
            patch.dict(os.environ, env, clear=True),
            patch("asc_cli.api.auth.load_dotenv"),  # Prevent .env loading
        ):
            result = Credentials.from_env()
            assert result is not None
            assert result.issuer_id == "test-issuer"
            assert result.key_id == "TESTKEY123"

    def test_from_file_missing(self, tmp_path: Path) -> None:
        """Test loading from missing file."""
        result = Credentials.from_file(tmp_path / "nonexistent")
        assert result is None


class TestAuthManager:
    """Tests for AuthManager class."""

    def test_not_authenticated(self) -> None:
        """Test unauthenticated state."""
        auth = AuthManager(None)
        assert not auth.is_authenticated

    def test_authenticated(self) -> None:
        """Test authenticated state."""
        creds = Credentials(
            issuer_id="test",
            key_id="test",
            private_key="-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
        )
        auth = AuthManager(creds)
        assert auth.is_authenticated

    def test_auto_no_credentials(self) -> None:
        """Test auto() with no credentials available."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("asc_cli.api.auth.load_dotenv"),  # Prevent .env loading
            patch("asc_cli.api.auth.Credentials.from_file", return_value=None),
        ):
            auth = AuthManager.auto()
            assert not auth.is_authenticated
