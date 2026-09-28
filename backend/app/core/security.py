from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError
try:
    from pwdlib import PasswordHash
except ImportError:  # Development fallback; production requirements install pwdlib[argon2].
    PasswordHash = None


from app.core.config import get_settings

settings = get_settings()
if PasswordHash is not None:
    password_hasher = PasswordHash.recommended()
else:
    from argon2 import PasswordHasher
    _argon = PasswordHasher()
    class _FallbackHasher:
        def hash(self, value: str) -> str:
            return _argon.hash(value)
        def verify(self, value: str, hashed: str) -> bool:
            try:
                return _argon.verify(hashed, value)
            except Exception:
                return False
    password_hasher = _FallbackHasher()
DUMMY_HASH = password_hasher.hash("dummy-password-for-timing")
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(user_id: int, roles: list[str]) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "roles": roles,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
    except InvalidTokenError as exc:
        raise ValueError("Invalid or expired access token") from exc
    if payload.get("type") != "access":
        raise ValueError("Invalid token type")
    return payload


def create_refresh_token() -> tuple[str, datetime]:
    token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    return token, expires_at
