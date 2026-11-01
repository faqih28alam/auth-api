from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response

from app.application.use_cases.delete_user import DeleteUser
from app.application.use_cases.get_user import GetUser
from app.application.use_cases.get_user_stats import GetUserStats
from app.application.use_cases.list_users import ListUsers
from app.application.use_cases.update_user import UpdateUser
from app.domain.entities.user import Role, User
from app.presentation.api.deps import (
    get_delete_user,
    get_list_users,
    get_update_user,
    get_user,
    get_user_stats,
    require_admin,
)
from app.presentation.api.errors import domain_http
from app.presentation.api.schemas.user import (
    UserListResponse,
    UserResponse,
    UserStatsResponse,
    UserUpdateRequest,
    to_user_response,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users/stats", response_model=UserStatsResponse)
async def user_stats(
    _admin: User = Depends(require_admin),
    use_case: GetUserStats = Depends(get_user_stats),
) -> UserStatsResponse:
    stats = await use_case.execute()
    return UserStatsResponse(total=stats.total, active=stats.active, by_role=stats.by_role)


@router.get("/users", response_model=UserListResponse)
async def list_users(
    _admin: User = Depends(require_admin),
    use_case: ListUsers = Depends(get_list_users),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    role: Role | None = None,
    search: str | None = Query(default=None, max_length=100),
) -> UserListResponse:
    page_result = await use_case.execute(page=page, limit=limit, role=role, search=search)
    return UserListResponse(
        items=[to_user_response(user) for user in page_result.items],
        total=page_result.total,
        page=page_result.page,
        limit=page_result.limit,
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    _admin: User = Depends(require_admin),
    use_case: GetUser = Depends(get_user),
) -> UserResponse:
    async with domain_http():
        user = await use_case.execute(user_id)
    return to_user_response(user)


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    body: UserUpdateRequest,
    _admin: User = Depends(require_admin),
    use_case: UpdateUser = Depends(get_update_user),
) -> UserResponse:
    async with domain_http():
        user = await use_case.execute(user_id, role=body.role, is_active=body.is_active)
    return to_user_response(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    admin: User = Depends(require_admin),
    use_case: DeleteUser = Depends(get_delete_user),
) -> Response:
    async with domain_http():
        await use_case.execute(admin.id or "", user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
