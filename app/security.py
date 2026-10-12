import hashlib
import secrets


def generate_api_key() -> str:
    """Return a new random API key (43 URL-safe characters)."""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Return the SHA-256 hex digest of an API key.

    Keys are long and random, so a fast hash is safe here. Only the hash is
    stored; the raw key is shown to the tenant once and never saved.
    """
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()