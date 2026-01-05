"""Comprehensive auth module tests to reach 90%+ coverage.

Tests file I/O operations, environment loading, credential saving,
and token generation that were previously untested.
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import jwt
import pytest

from asc_cli.api.auth import (
    AuthenticationError,
    AuthManager,
    Credentials,
)


class TestCredentialsFromFile:
    """Tests for Credentials.from_file() method."""

    def test_from_file_valid(self, tmp_path: Path) -> None:
        """Test loading from valid config file."""
        # Create a private key file
        private_key_path = tmp_path / "AuthKey_TEST.p8"
        private_key_content = (
            "-----BEGIN PRIVATE KEY-----\ntest_key_content\n-----END PRIVATE KEY-----"
        )
        private_key_path.write_text(private_key_content)

        # Create credentials config file
        config_file = tmp_path / "credentials"
        config_content = f"""# asc-cli credentials
issuer_id=test-issuer-123
key_id=TESTKEY456
private_key_path={private_key_path}
"""
        config_file.write_text(config_content)

        # Load and verify
        result = Credentials.from_file(config_file)
        assert result is not None
        assert result.issuer_id == "test-issuer-123"
        assert result.key_id == "TESTKEY456"
        assert result.private_key == private_key_content

    def test_from_file_with_quoted_values(self, tmp_path: Path) -> None:
        """Test loading with quoted values in config."""
        private_key_path = tmp_path / "AuthKey_TEST.p8"
        private_key_path.write_text("-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----")

        config_file = tmp_path / "credentials"
        config_content = f"""issuer_id="quoted-issuer"
key_id="QUOTEDKEY"
private_key_path="{private_key_path}"
"""
        config_file.write_text(config_content)

        result = Credentials.from_file(config_file)
        assert result is not None
        assert result.issuer_id == "quoted-issuer"
        assert result.key_id == "QUOTEDKEY"

    def test_from_file_with_comments(self, tmp_path: Path) -> None:
        """Test loading with comments in config."""
        private_key_path = tmp_path / "AuthKey_TEST.p8"
        private_key_path.write_text("-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----")

        config_file = tmp_path / "credentials"
        config_content = f"""# This is a comment
issuer_id=test-issuer
# Another comment
key_id=TESTKEY
private_key_path={private_key_path}
# Final comment
"""
        config_file.write_text(config_content)

        result = Credentials.from_file(config_file)
        assert result is not None
        assert result.issuer_id == "test-issuer"

    def test_from_file_missing_field(self, tmp_path: Path) -> None:
        """Test loading with missing required field."""
        config_file = tmp_path / "credentials"
        config_content = """issuer_id=test-issuer
key_id=TESTKEY
# missing private_key_path
"""
        config_file.write_text(config_content)

        result = Credentials.from_file(config_file)
        assert result is None

    def test_from_file_missing_private_key_file(self, tmp_path: Path) -> None:
        """Test loading when private key file doesn't exist."""
        config_file = tmp_path / "credentials"
        config_content = """issuer_id=test-issuer
key_id=TESTKEY
private_key_path=/nonexistent/AuthKey_TEST.p8
"""
        config_file.write_text(config_content)

        result = Credentials.from_file(config_file)
        assert result is None

    def test_from_file_with_tilde_path(self, tmp_path: Path) -> None:
        """Test loading with tilde-expanded path."""
        # Create private key in tmp dir
        private_key_path = tmp_path / "AuthKey_TEST.p8"
        private_key_path.write_text("-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----")

        # Use tilde in config but patch expanduser to point to tmp_path
        config_file = tmp_path / "credentials"
        config_content = """issuer_id=test-issuer
key_id=TESTKEY
private_key_path=~/AuthKey_TEST.p8
"""
        config_file.write_text(config_content)

        # Mock expanduser to return our tmp path
        with patch.object(Path, "expanduser", return_value=private_key_path):
            result = Credentials.from_file(config_file)
            assert result is not None
            assert result.issuer_id == "test-issuer"

    def test_from_file_uses_default_path(self, tmp_path: Path) -> None:
        """Test from_file() uses default CREDENTIALS_FILE when no path given."""
        # Patch the default path to our tmp directory
        with patch("asc_cli.api.auth.CREDENTIALS_FILE", tmp_path / "nonexistent"):
            result = Credentials.from_file()
            assert result is None


class TestCredentialsFromEnv:
    """Tests for Credentials.from_env() method."""

    def test_from_env_with_key_path(self, tmp_path: Path) -> None:
        """Test loading with private key from file path."""
        private_key_path = tmp_path / "AuthKey_TEST.p8"
        private_key_content = "-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----"
        private_key_path.write_text(private_key_content)

        env = {
            "ASC_ISSUER_ID": "test-issuer",
            "ASC_KEY_ID": "TESTKEY123",
            "ASC_PRIVATE_KEY_PATH": str(private_key_path),
        }
        with (
            patch.dict(os.environ, env, clear=True),
            patch("asc_cli.api.auth.load_dotenv"),
        ):
            result = Credentials.from_env()
            assert result is not None
            assert result.issuer_id == "test-issuer"
            assert result.key_id == "TESTKEY123"
            assert result.private_key == private_key_content

    def test_from_env_with_quoted_key_path(self, tmp_path: Path) -> None:
        """Test loading with quoted private key path."""
        private_key_path = tmp_path / "AuthKey_TEST.p8"
        private_key_path.write_text("-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----")

        env = {
            "ASC_ISSUER_ID": "test-issuer",
            "ASC_KEY_ID": "TESTKEY",
            "ASC_PRIVATE_KEY_PATH": f'"{private_key_path}"',
        }
        with (
            patch.dict(os.environ, env, clear=True),
            patch("asc_cli.api.auth.load_dotenv"),
        ):
            result = Credentials.from_env()
            assert result is not None

    def test_from_env_with_single_quoted_key_path(self, tmp_path: Path) -> None:
        """Test loading with single-quoted private key path."""
        private_key_path = tmp_path / "AuthKey_TEST.p8"
        private_key_path.write_text("-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----")

        env = {
            "ASC_ISSUER_ID": "test-issuer",
            "ASC_KEY_ID": "TESTKEY",
            "ASC_PRIVATE_KEY_PATH": f"'{private_key_path}'",
        }
        with (
            patch.dict(os.environ, env, clear=True),
            patch("asc_cli.api.auth.load_dotenv"),
        ):
            result = Credentials.from_env()
            assert result is not None

    def test_from_env_with_tilde_in_key_path(self, tmp_path: Path) -> None:
        """Test loading with tilde-expanded key path."""
        private_key_path = tmp_path / "AuthKey_TEST.p8"
        private_key_path.write_text("-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----")

        env = {
            "ASC_ISSUER_ID": "test-issuer",
            "ASC_KEY_ID": "TESTKEY",
            "ASC_PRIVATE_KEY_PATH": "~/AuthKey_TEST.p8",
        }
        with (
            patch.dict(os.environ, env, clear=True),
            patch("asc_cli.api.auth.load_dotenv"),
            patch.object(Path, "expanduser", return_value=private_key_path),
        ):
            result = Credentials.from_env()
            assert result is not None

    def test_from_env_with_nonexistent_key_path(self) -> None:
        """Test loading with path to nonexistent key file."""
        env = {
            "ASC_ISSUER_ID": "test-issuer",
            "ASC_KEY_ID": "TESTKEY",
            "ASC_PRIVATE_KEY_PATH": "/nonexistent/AuthKey_TEST.p8",
        }
        with (
            patch.dict(os.environ, env, clear=True),
            patch("asc_cli.api.auth.load_dotenv"),
        ):
            result = Credentials.from_env()
            assert result is None

    def test_from_env_missing_key_id(self) -> None:
        """Test loading with missing key_id."""
        env = {
            "ASC_ISSUER_ID": "test-issuer",
            "ASC_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
        }
        with (
            patch.dict(os.environ, env, clear=True),
            patch("asc_cli.api.auth.load_dotenv"),
        ):
            result = Credentials.from_env()
            assert result is None

    def test_from_env_missing_issuer_id(self) -> None:
        """Test loading with missing issuer_id."""
        env = {
            "ASC_KEY_ID": "TESTKEY",
            "ASC_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
        }
        with (
            patch.dict(os.environ, env, clear=True),
            patch("asc_cli.api.auth.load_dotenv"),
        ):
            result = Credentials.from_env()
            assert result is None


class TestCredentialsSave:
    """Tests for Credentials.save() method."""

    def test_save_creates_directory(self, tmp_path: Path) -> None:
        """Test save() creates config directory if it doesn't exist."""
        creds = Credentials(
            issuer_id="test-issuer",
            key_id="TESTKEY",
            private_key="-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
        )

        private_key_path = tmp_path / "AuthKey_TEST.p8"
        private_key_path.write_text(creds.private_key)

        config_dir = tmp_path / "config"
        config_file = config_dir / "credentials"

        # Mock the config paths
        with (
            patch("asc_cli.api.auth.CONFIG_DIR", config_dir),
            patch("asc_cli.api.auth.CREDENTIALS_FILE", config_file),
        ):
            creds.save(private_key_path)

            assert config_dir.exists()
            assert config_file.exists()

    def test_save_writes_correct_content(self, tmp_path: Path) -> None:
        """Test save() writes correct credential content."""
        creds = Credentials(
            issuer_id="test-issuer-123",
            key_id="TESTKEY456",
            private_key="-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
        )

        private_key_path = tmp_path / "AuthKey_TEST.p8"
        config_file = tmp_path / "credentials"

        with (
            patch("asc_cli.api.auth.CONFIG_DIR", tmp_path),
            patch("asc_cli.api.auth.CREDENTIALS_FILE", config_file),
        ):
            creds.save(private_key_path)

            content = config_file.read_text()
            assert "issuer_id=test-issuer-123" in content
            assert "key_id=TESTKEY456" in content
            assert f"private_key_path={private_key_path}" in content
            assert "# asc-cli credentials" in content

    def test_save_sets_file_permissions(self, tmp_path: Path) -> None:
        """Test save() sets secure file permissions (0o600)."""
        creds = Credentials(
            issuer_id="test-issuer",
            key_id="TESTKEY",
            private_key="-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
        )

        private_key_path = tmp_path / "AuthKey_TEST.p8"
        config_file = tmp_path / "credentials"

        with (
            patch("asc_cli.api.auth.CONFIG_DIR", tmp_path),
            patch("asc_cli.api.auth.CREDENTIALS_FILE", config_file),
        ):
            creds.save(private_key_path)

            # Check file permissions
            stat_info = config_file.stat()
            mode = stat_info.st_mode & 0o777
            assert mode == 0o600


class TestAuthManagerTokenGeneration:
    """Tests for AuthManager token generation."""

    # Valid EC private key for testing
    # Generated with: openssl ecparam -name prime256v1 -genkey -noout
    TEST_EC_PRIVATE_KEY = """-----BEGIN EC PRIVATE KEY-----
MHcCAQEEIKsQyM6o5V0A9xxruTQZpj/0ZxVLYixgbj0FCcifI0NAoAoGCCqGSM49
AwEHoUQDQgAEXYy3zF3er3NkqpyTaJX+x0jhn3l5Zgv89eBb727jouJnKqtOMZL7
ajPlCHDPHjNwbt6SCWOC5+1XV1VwTgplgw==
-----END EC PRIVATE KEY-----"""

    def test_token_generation(self) -> None:
        """Test JWT token is generated correctly."""
        creds = Credentials(
            issuer_id="test-issuer",
            key_id="TESTKEY123",
            private_key=self.TEST_EC_PRIVATE_KEY,
        )
        auth = AuthManager(creds)

        token = auth.token
        assert token is not None
        assert isinstance(token, str)

        # Decode and verify token (without verification for testing)
        decoded = jwt.decode(token, options={"verify_signature": False})
        assert decoded["iss"] == "test-issuer"
        assert decoded["aud"] == "appstoreconnect-v1"
        assert "iat" in decoded
        assert "exp" in decoded

    def test_token_caching(self) -> None:
        """Test token is cached and reused."""
        creds = Credentials(
            issuer_id="test-issuer",
            key_id="TESTKEY123",
            private_key=self.TEST_EC_PRIVATE_KEY,
        )
        auth = AuthManager(creds)

        token1 = auth.token
        token2 = auth.token

        # Should return same token (cached)
        assert token1 == token2

    def test_token_refresh_after_expiry(self) -> None:
        """Test token is refreshed after expiry."""
        creds = Credentials(
            issuer_id="test-issuer",
            key_id="TESTKEY123",
            private_key=self.TEST_EC_PRIVATE_KEY,
        )
        auth = AuthManager(creds)

        # Get first token
        token1 = auth.token

        # Force expiry by setting _token_expiry to past
        auth._token_expiry = datetime.now() - timedelta(minutes=1)

        # Get new token (should be different)
        token2 = auth.token
        assert token1 != token2

    def test_token_without_credentials_raises(self) -> None:
        """Test getting token without credentials raises error."""
        auth = AuthManager(None)

        with pytest.raises(AuthenticationError, match="Not authenticated"):
            _ = auth.token

    def test_credentials_property_without_auth_raises(self) -> None:
        """Test accessing credentials property without auth raises error."""
        auth = AuthManager(None)

        with pytest.raises(AuthenticationError, match="Not authenticated"):
            _ = auth.credentials


class TestAuthManagerFactoryMethods:
    """Tests for AuthManager factory methods."""

    def test_from_env(self, tmp_path: Path) -> None:
        """Test AuthManager.from_env() factory method."""
        private_key_path = tmp_path / "AuthKey_TEST.p8"
        private_key_path.write_text("-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----")

        env = {
            "ASC_ISSUER_ID": "test-issuer",
            "ASC_KEY_ID": "TESTKEY",
            "ASC_PRIVATE_KEY_PATH": str(private_key_path),
        }
        with (
            patch.dict(os.environ, env, clear=True),
            patch("asc_cli.api.auth.load_dotenv"),
        ):
            auth = AuthManager.from_env()
            assert auth.is_authenticated

    def test_from_file(self, tmp_path: Path) -> None:
        """Test AuthManager.from_file() factory method."""
        private_key_path = tmp_path / "AuthKey_TEST.p8"
        private_key_path.write_text("-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----")

        config_file = tmp_path / "credentials"
        config_content = f"""issuer_id=test-issuer
key_id=TESTKEY
private_key_path={private_key_path}
"""
        config_file.write_text(config_content)

        auth = AuthManager.from_file(config_file)
        assert auth.is_authenticated

    def test_auto_prefers_env(self, tmp_path: Path) -> None:
        """Test auto() prefers environment over file."""
        # Set up both env and file
        private_key_path = tmp_path / "AuthKey_TEST.p8"
        private_key_path.write_text("-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----")

        env = {
            "ASC_ISSUER_ID": "env-issuer",
            "ASC_KEY_ID": "ENVKEY",
            "ASC_PRIVATE_KEY_PATH": str(private_key_path),
        }

        config_file = tmp_path / "credentials"
        config_content = f"""issuer_id=file-issuer
key_id=FILEKEY
private_key_path={private_key_path}
"""
        config_file.write_text(config_content)

        with (
            patch.dict(os.environ, env, clear=True),
            patch("asc_cli.api.auth.load_dotenv"),
            patch("asc_cli.api.auth.CREDENTIALS_FILE", config_file),
        ):
            auth = AuthManager.auto()
            assert auth.is_authenticated
            assert auth.credentials.issuer_id == "env-issuer"

    def test_auto_falls_back_to_file(self, tmp_path: Path) -> None:
        """Test auto() falls back to file when env is not set."""
        private_key_path = tmp_path / "AuthKey_TEST.p8"
        private_key_path.write_text("-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----")

        config_file = tmp_path / "credentials"
        config_content = f"""issuer_id=file-issuer
key_id=FILEKEY
private_key_path={private_key_path}
"""
        config_file.write_text(config_content)

        with (
            patch.dict(os.environ, {}, clear=True),
            patch("asc_cli.api.auth.load_dotenv"),
            patch("asc_cli.api.auth.CREDENTIALS_FILE", config_file),
        ):
            auth = AuthManager.auto()
            assert auth.is_authenticated
            assert auth.credentials.issuer_id == "file-issuer"
