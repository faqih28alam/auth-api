from app.domain.entities.user import UserStats
from app.domain.repositories.user_repository import UserRepository


class GetUserStats:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def execute(self) -> UserStats:
        return await self._users.stats()
