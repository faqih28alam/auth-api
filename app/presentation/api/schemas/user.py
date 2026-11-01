from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.entities.user import Role, User


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    role: Role
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    limit: int


class UserStatsResponse(BaseModel):
    total: int
    active: int
    by_role: dict[str, int]


class UserUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Role | None = None
    is_active: bool | None = None


def to_user_response(user: User) -> UserResponse:
    if user.id is None:
        raise RuntimeError("User is missing an id.")
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
