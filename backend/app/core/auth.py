"""Password hashing, signed access tokens, and request authorization."""
import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Callable, Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import UserModel
from app.db.session import get_db

TOKEN_ISSUER = "nexus"
_SCRYPT_N = 2 ** 14
_SCRYPT_R = 8
_SCRYPT_P = 1

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

def hash_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError("Password must contain at least 12 characters.")
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=64)
    return "scrypt$" + str(_SCRYPT_N) + "$" + _b64(salt) + "$" + _b64(digest)

def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, n_value, salt_value, digest_value = encoded.split("$", 3)
        if algorithm != "scrypt":
            return False
        salt, expected = _unb64(salt_value), _unb64(digest_value)
        actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=int(n_value), r=_SCRYPT_R, p=_SCRYPT_P, dklen=len(expected))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False

def _signing_key() -> bytes:
    secret = settings.AUTH_SECRET_KEY
    if not secret or len(secret) < 32:
        raise HTTPException(status_code=503, detail="Authentication is not configured. Set AUTH_SECRET_KEY (32+ characters).")
    return secret.encode("utf-8")

def create_access_token(user: UserModel) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"iss": TOKEN_ISSUER, "sub": user.id, "iat": now, "exp": now + max(1, settings.ACCESS_TOKEN_TTL_MINUTES) * 60, "ver": user.token_version}
    signing_input = _b64(json.dumps(header, separators=(",", ":"), sort_keys=True).encode()) + "." + _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signature = hmac.new(_signing_key(), signing_input.encode("ascii"), hashlib.sha256).digest()
    return signing_input + "." + _b64(signature)

def decode_access_token(token: str) -> dict:
    try:
        header_part, payload_part, signature_part = token.split(".")
        signing_input = header_part + "." + payload_part
        expected = hmac.new(_signing_key(), signing_input.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _unb64(signature_part)):
            raise ValueError("signature")
        header = json.loads(_unb64(header_part))
        payload = json.loads(_unb64(payload_part))
        now = int(time.time())
        if header != {"alg": "HS256", "typ": "JWT"}:
            raise ValueError("header")
        if payload.get("iss") != TOKEN_ISSUER or not isinstance(payload.get("sub"), str):
            raise ValueError("claims")
        if not isinstance(payload.get("exp"), int) or payload["exp"] <= now:
            raise ValueError("expired")
        if not isinstance(payload.get("iat"), int) or payload["iat"] > now + 30:
            raise ValueError("issued-at")
        if not isinstance(payload.get("ver"), int):
            raise ValueError("version")
        return payload
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired access token.", headers={"WWW-Authenticate": "Bearer"}) from exc

def get_current_user(authorization: Optional[str] = Header(None, alias="Authorization"), db: Session = Depends(get_db)) -> UserModel:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required.", headers={"WWW-Authenticate": "Bearer"})
    claims = decode_access_token(authorization[7:].strip())
    user = db.query(UserModel).filter(UserModel.id == claims["sub"]).first()
    if not user or not user.is_active or user.token_version != claims["ver"]:
        raise HTTPException(status_code=401, detail="Session is invalid or has been revoked.", headers={"WWW-Authenticate": "Bearer"})
    return user

def require_authenticated_user(user: UserModel = Depends(get_current_user)) -> UserModel:
    return user

def require_roles(*roles: str) -> Callable:
    def dependency(user: UserModel = Depends(get_current_user)) -> UserModel:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role.")
        return user
    return dependency
