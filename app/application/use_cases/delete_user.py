from app.domain.entities.user import Role
from app.domain.exceptions import CannotDeleteSelf, LastAdminProtected, UserNotFound
from app.domain.repositories.refresh_token_repository import RefreshTokenRepository
from app.domain.repositories.user_repository import UserRepository


class DeleteUser:
    def __init__(self, users: UserRepository, refresh_tokens: RefreshTokenRepository) -> None:
        self._users = users
        self._refresh_tokens = refresh_tokens

    async def execute(self, actor_id: str, user_id: str) -> None:
        if actor_id == user_id:
            raise CannotDeleteSelf()
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFound()
        if user.role == Role.ADMIN and user.is_active:
            if await self._users.count_active_admins() <= 1:
                raise LastAdminProtected()
        await self._refresh_tokens.revoke_all_for_user(user_id)
        await self._users.delete(user_id)
