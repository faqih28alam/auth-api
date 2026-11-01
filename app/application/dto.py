from dataclasses import dataclass

from app.domain.entities.user import User


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


@dataclass(frozen=True)
class UserPage:
    items: list[User]
    total: int
    page: int
    limit: int
