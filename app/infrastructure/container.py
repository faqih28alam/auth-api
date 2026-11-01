from dataclasses import dataclass
from typing import Any

from app.domain.ports.password_hasher import PasswordHasher
from app.domain.ports.token_service import TokenService
from app.domain.repositories.refresh_token_repository import RefreshTokenRepository
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.config import Settings


@dataclass
class Container:
    settings: Settings
    mongo_client: Any
    users: UserRepository
    refresh_tokens: RefreshTokenRepository
    hasher: PasswordHasher
    tokens: TokenService
