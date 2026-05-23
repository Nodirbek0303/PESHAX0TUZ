from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def verify_admin_password(plain_password: str) -> bool:
    if settings.admin_password_hash:
        return verify_password(plain_password, settings.admin_password_hash)
    return hmac.compare_digest(plain_password, settings.admin_password)


def create_admin_token() -> tuple[str, datetime, str]:
    expires = datetime.now(timezone.utc) + timedelta(hours=settings.admin_token_ttl_hours)
    jti = secrets.token_urlsafe(16)
    payload = {
        "sub": "admin",
        "role": "super_admin",
        "jti": jti,
        "iat": datetime.now(timezone.utc),
        "exp": expires,
    }
    token = jwt.encode(payload, settings.security_secret_key, algorithm=JWT_ALGORITHM)
    return token, expires, jti


def decode_admin_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.security_secret_key, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


def hash_token_fingerprint(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
