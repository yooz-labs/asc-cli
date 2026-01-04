"""Authentication management for App Store Connect API."""

import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import jwt
from dotenv import load_dotenv

# Default config directory
CONFIG_DIR = Path.home() / ".config" / "asc-cli"
CREDENTIALS_FILE = CONFIG_DIR / "credentials"


@dataclass
class Credentials:
    """App Store Connect API credentials."""

    issuer_id: str
    key_id: str
    private_key: str

    @classmethod
    def from_env(cls) -> Optional["Credentials"]:
        """Load credentials from environment variables."""
        load_dotenv()

        issuer_id = os.getenv("ASC_ISSUER_ID")
        key_id = os.getenv("ASC_KEY_ID")
        private_key_path = os.getenv("ASC_PRIVATE_KEY_PATH")
        private_key = os.getenv("ASC_PRIVATE_KEY")

        if not issuer_id or not key_id:
            return None

        if private_key_path and not private_key:
            path = Path(private_key_path.strip('"').strip("'")).expanduser()
            if path.exists():
                private_key = path.read_text()

        if not private_key:
            return None

        return cls(issuer_id=issuer_id, key_id=key_id, private_key=private_key)

    @classmethod
    def from_file(cls, path: Path | None = None) -> Optional["Credentials"]:
        """Load credentials from config file."""
        config_path = path or CREDENTIALS_FILE
        if not config_path.exists():
            return None

        data: dict[str, str] = {}
        for line in config_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                data[key.strip()] = value.strip().strip('"')

        issuer_id = data.get("issuer_id")
        key_id = data.get("key_id")
        private_key_path = data.get("private_key_path")

        if not all([issuer_id, key_id, private_key_path]):
            return None

        # At this point private_key_path is guaranteed to be str
        assert private_key_path is not None
        path = Path(private_key_path).expanduser()
        if not path.exists():
            return None

        return cls(
            issuer_id=issuer_id,  # type: ignore[arg-type]
            key_id=key_id,  # type: ignore[arg-type]
            private_key=path.read_text(),
        )

    def save(self, private_key_path: Path) -> None:
        """Save credentials to config file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        content = f"""# asc-cli credentials
issuer_id={self.issuer_id}
key_id={self.key_id}
private_key_path={private_key_path}
"""
        CREDENTIALS_FILE.write_text(content)
        CREDENTIALS_FILE.chmod(0o600)


class AuthManager:
    """Manages authentication tokens for App Store Connect API."""

    def __init__(self, credentials: Credentials | None = None) -> None:
        """Initialize with optional credentials."""
        self._credentials = credentials
        self._token: str | None = None
        self._token_expiry: datetime | None = None

    @classmethod
    def from_env(cls) -> "AuthManager":
        """Create AuthManager from environment variables."""
        return cls(Credentials.from_env())

    @classmethod
    def from_file(cls, path: Path | None = None) -> "AuthManager":
        """Create AuthManager from config file."""
        return cls(Credentials.from_file(path))

    @classmethod
    def auto(cls) -> "AuthManager":
        """Create AuthManager, trying environment first, then config file."""
        credentials = Credentials.from_env() or Credentials.from_file()
        return cls(credentials)

    @property
    def is_authenticated(self) -> bool:
        """Check if we have valid credentials."""
        return self._credentials is not None

    @property
    def credentials(self) -> Credentials:
        """Get credentials, raising if not authenticated."""
        if not self._credentials:
            raise AuthenticationError("Not authenticated. Run 'asc auth login' first.")
        return self._credentials

    @property
    def token(self) -> str:
        """Get a valid JWT token, refreshing if needed."""
        now = datetime.now()

        if self._token and self._token_expiry and now < self._token_expiry:
            return self._token

        # Generate new token (valid for 20 minutes)
        expiry = now + timedelta(minutes=20)
        creds = self.credentials

        payload = {
            "iss": creds.issuer_id,
            "iat": int(time.time()),
            "exp": int(expiry.timestamp()),
            "aud": "appstoreconnect-v1",
        }

        self._token = jwt.encode(
            payload,
            creds.private_key,
            algorithm="ES256",
            headers={"kid": creds.key_id},
        )
        self._token_expiry = expiry - timedelta(minutes=5)  # Refresh buffer

        return self._token


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass
