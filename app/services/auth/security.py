from datetime import datetime, timedelta, timezone
import hashlib
import secrets

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import get_settings

settings = get_settings()
password_hasher = PasswordHash.recommended()

def hash_password(password: str) -> str:
    """
    returns the hashed password
    """
    return password_hasher.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    returns True if the password matches the hashed password
    """
    return password_hasher.verify(plain_password, hashed_password)

def create_access_token(
        subject: str,
        expires_delta: timedelta = timedelta(minutes=settings.access_token_expire_minutes)
) -> str:
    expire = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": subject,     # user info
        "exp": expire,      # expire time
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """
    returns the decoded token
    """
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError as exc:
        raise ValueError("Invalid token") from exc

def create_api_key() -> tuple[str, str, str]:
    api_key = f"sk-{settings.api_key_provider_note}-{secrets.token_urlsafe(32)}"
    key_hash = hash_api_key(api_key)
    prefix = api_key[:9+len(settings.api_key_provider_note)]
    return api_key, prefix, key_hash

def hash_api_key(api_key: str) -> str:
    """
    returns the hashed API key
    """
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()

def safe_compare(left: str, right: str) -> bool:
    return secrets.compare_digest(left, right)