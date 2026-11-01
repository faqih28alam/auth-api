from app.application.dto import UserPage
from app.domain.entities.user import Role
from app.domain.repositories.user_repository import UserRepository


class ListUsers:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def execute(
        self,
        *,
        page: int,
        limit: int,
        role: Role | None,
        search: str | None,
    ) -> UserPage:
        safe_page = max(page, 1)
        safe_limit = min(max(limit, 1), 100)
        cleaned = search.strip() if search else None
        if not cleaned:
            cleaned = None
        items, total = await self._users.list_users(
            page=safe_page,
            limit=safe_limit,
            role=role,
            search=cleaned,
        )
        return UserPage(items=items, total=total, page=safe_page, limit=safe_limit)
