from app.domain.entities.user import Role, User
from app.domain.exceptions import LastAdminProtected, NoChangesProvided, UserNotFound
from app.domain.repositories.user_repository import UserRepository
from app.domain.time import utcnow


class UpdateUser:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def execute(
        self,
        user_id: str,
        *,
        role: Role | None,
        is_active: bool | None,
    ) -> User:
        if role is None and is_active is None:
            raise NoChangesProvided()
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFound()
        new_role = role if role is not None else user.role
        new_active = user.is_active if is_active is None else is_active
        losing_admin = user.role == Role.ADMIN and user.is_active and not (
            new_role == Role.ADMIN and new_active
        )
        if losing_admin and await self._users.count_active_admins() <= 1:
            raise LastAdminProtected()
        user.role = new_role
        user.is_active = new_active
        user.updated_at = utcnow()
        return await self._users.update(user)
