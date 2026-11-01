import logging

from app.domain.entities.user import Role, User
from app.domain.identity import normalize_email, normalize_username
from app.domain.password_policy import validate_password
from app.domain.ports.password_hasher import PasswordHasher
from app.domain.repositories.user_repository import UserRepository
from app.domain.time import utcnow

logger = logging.getLogger(__name__)


class SeedAdmin:
    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        *,
        email: str,
        username: str,
        password: str,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._email = email
        self._username = username
        self._password = password

    async def execute(self) -> bool:
        if await self._users.has_admin():
            return False
        validate_password(self._password)
        email = normalize_email(self._email)
        username = normalize_username(self._username)
        now = utcnow()
        user = User(
            id=None,
            email=email,
            username=username,
            username_normalized=username.lower(),
            password_hash=self._hasher.hash(self._password),
            role=Role.ADMIN,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        await self._users.add(user)
        logger.info("Seeded default admin user '%s'.", username)
        return True
