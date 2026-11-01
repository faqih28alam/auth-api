from datetime import timedelta

from app.application.dto import TokenPair
from app.domain.entities.user import User
from app.domain.ports.token_service import TokenService
from app.domain.repositories.refresh_token_repository import RefreshTokenRepository
from app.domain.time import utcnow


class TokenIssuer:
    def __init__(
        self,
        tokens: TokenService,
        refresh_tokens: RefreshTokenRepository,
        refresh_days: int,
    ) -> None:
        self._tokens = tokens
        self._refresh_tokens = refresh_tokens
        self._refresh_days = refresh_days

    async def issue(self, user: User) -> TokenPair:
        if user.id is None:
            raise RuntimeError("Cannot issue tokens for an unsaved user.")
        access_token, expires_in = self._tokens.create_access_token(user.id, user.role.value)
        raw_refresh = self._tokens.create_refresh_token()
        await self._refresh_tokens.store(
            token_hash=self._tokens.hash_refresh_token(raw_refresh),
            user_id=user.id,
            expires_at=utcnow() + timedelta(days=self._refresh_days),
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=raw_refresh,
            token_type="bearer",
            expires_in=expires_in,
        )
