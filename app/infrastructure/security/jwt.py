import hashlib
import secrets
from datetime import timedelta

import jwt

from app.domain.exceptions import InvalidToken
from app.domain.time import utcnow
from app.infrastructure.config import Settings


class JwtTokenService:
    _algorithm = "HS256"

    def __init__(self, settings: Settings) -> None:
        self._secret = settings.jwt_secret
        self._ttl_seconds = settings.access_token_expire_minutes * 60

    def create_access_token(self, user_id: str, role: str) -> tuple[str, int]:
        now = utcnow()
        payload = {
            "sub": user_id,
            "role": role,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=self._ttl_seconds)).timestamp()),
        }
        token = jwt.encode(payload, self._secret, algorithm=self._algorithm)
        return token, self._ttl_seconds

    def decode_access_token(self, token: str) -> tuple[str, str]:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except jwt.PyJWTError as exc:
            raise InvalidToken() from exc
        subject = payload.get("sub")
        if payload.get("type") != "access" or not subject:
            raise InvalidToken()
        return str(subject), str(payload.get("role", ""))

    def create_refresh_token(self) -> str:
        return secrets.token_urlsafe(32)

    def hash_refresh_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
