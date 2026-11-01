from app.domain.exceptions import CurrentPasswordIncorrect, UserNotFound
from app.domain.password_policy import validate_password
from app.domain.ports.password_hasher import PasswordHasher
from app.domain.repositories.refresh_token_repository import RefreshTokenRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.time import utcnow


class ChangePassword:
    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        refresh_tokens: RefreshTokenRepository,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._refresh_tokens = refresh_tokens

    async def execute(self, user_id: str, current_password: str, new_password: str) -> None:
        user = await self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise UserNotFound()
        if not self._hasher.verify(current_password, user.password_hash):
            raise CurrentPasswordIncorrect()
        validate_password(new_password)
        user.password_hash = self._hasher.hash(new_password)
        user.updated_at = utcnow()
        await self._users.update(user)
        await self._refresh_tokens.revoke_all_for_user(user_id)
