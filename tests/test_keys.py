"""Test key management for authentication tests.

This module provides EC private keys for testing. Keys can be:
1. Provided via ASC_TEST_PRIVATE_KEY environment variable
2. Generated dynamically if not provided

The generated keys are valid EC P-256 keys suitable for JWT signing,
but are NOT real Apple App Store Connect keys.
"""

import os
from functools import lru_cache

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


@lru_cache(maxsize=1)
def get_test_private_key() -> str:
    """Get or generate a test EC private key.

    Returns the key from ASC_TEST_PRIVATE_KEY env var if set,
    otherwise generates a new P-256 key.

    Returns:
        PEM-encoded EC private key string
    """
    env_key = os.environ.get("ASC_TEST_PRIVATE_KEY")
    if env_key:
        return env_key

    # Generate a test key dynamically
    private_key = ec.generate_private_key(ec.SECP256R1())
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return pem.decode("utf-8")


def get_test_credentials() -> dict[str, str]:
    """Get complete test credentials.

    Returns:
        Dict with ASC_ISSUER_ID, ASC_KEY_ID, and ASC_PRIVATE_KEY
    """
    return {
        "ASC_ISSUER_ID": os.environ.get("ASC_TEST_ISSUER_ID", "test-issuer-id"),
        "ASC_KEY_ID": os.environ.get("ASC_TEST_KEY_ID", "test-key-id"),
        "ASC_PRIVATE_KEY": get_test_private_key(),
    }
