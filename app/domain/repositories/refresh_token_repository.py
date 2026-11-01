from datetime import datetime
from typing import Protocol

from app.domain.entities.refresh_token import RefreshToken


class RefreshTokenRepository(Protocol):
    async def store(self, *, token_hash: str, user_id: str, expires_at: datetime) -> None: ...

    async def get(self, token_hash: str) -> RefreshToken | None: ...

    async def revoke(self, token_hash: str) -> None: ...

    async def revoke_all_for_user(self, user_id: str) -> None: ...
