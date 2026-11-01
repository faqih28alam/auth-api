from app.domain.entities.user import User
from app.domain.exceptions import UserNotFound
from app.domain.repositories.user_repository import UserRepository


class GetUser:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def execute(self, user_id: str) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFound()
        return user
