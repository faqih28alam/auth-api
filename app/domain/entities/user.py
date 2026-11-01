from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    USER = "user"


@dataclass
class User:
    id: str | None
    email: str
    username: str
    username_normalized: str
    password_hash: str
    role: Role
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class UserStats:
    total: int
    active: int
    by_role: dict[str, int]
