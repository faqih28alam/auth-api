from app.domain.exceptions import InvalidToken
from app.domain.ports.token_service import TokenService
from app.domain.repositories.refresh_token_repository import RefreshTokenRepository


class LogoutUser:
    def __init__(self, refresh_tokens: RefreshTokenRepository, tokens: TokenService) -> None:
        self._refresh_tokens = refresh_tokens
        self._tokens = tokens

    async def execute(self, user_id: str, raw_refresh_token: str) -> None:
        token_hash = self._tokens.hash_refresh_token(raw_refresh_token)
        record = await self._refresh_tokens.get(token_hash)
        if record is None or record.user_id != user_id:
            raise InvalidToken()
        await self._refresh_tokens.revoke(token_hash)
