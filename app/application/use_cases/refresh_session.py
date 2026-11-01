from app.application.dto import TokenPair
from app.application.token_issuer import TokenIssuer
from app.domain.exceptions import InvalidToken
from app.domain.ports.token_service import TokenService
from app.domain.repositories.refresh_token_repository import RefreshTokenRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.time import utcnow


class RefreshSession:
    def __init__(
        self,
        users: UserRepository,
        refresh_tokens: RefreshTokenRepository,
        tokens: TokenService,
        issuer: TokenIssuer,
    ) -> None:
        self._users = users
        self._refresh_tokens = refresh_tokens
        self._tokens = tokens
        self._issuer = issuer

    async def execute(self, raw_refresh_token: str) -> TokenPair:
        token_hash = self._tokens.hash_refresh_token(raw_refresh_token)
        record = await self._refresh_tokens.get(token_hash)
        if record is None:
            raise InvalidToken()
        if record.revoked:
            await self._refresh_tokens.revoke_all_for_user(record.user_id)
            raise InvalidToken()
        expires_at = record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=utcnow().tzinfo)
        if expires_at <= utcnow():
            raise InvalidToken()
        user = await self._users.get_by_id(record.user_id)
        if user is None or not user.is_active:
            raise InvalidToken()
        await self._refresh_tokens.revoke(token_hash)
        return await self._issuer.issue(user)
