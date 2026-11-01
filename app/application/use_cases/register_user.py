from app.domain.entities.user import Role, User
from app.domain.exceptions import UserAlreadyExists
from app.domain.identity import normalize_email, normalize_username
from app.domain.password_policy import validate_password
from app.domain.ports.password_hasher import PasswordHasher
from app.domain.repositories.user_repository import UserRepository
from app.domain.time import utcnow


class RegisterUser:
    def __init__(self, users: UserRepository, hasher: PasswordHasher) -> None:
        self._users = users
        self._hasher = hasher

    async def execute(self, email: str, username: str, password: str) -> User:
        validate_password(password)
        normalized_email = normalize_email(email)
        display_username = normalize_username(username)
        username_normalized = display_username.lower()
        if await self._users.get_by_email(normalized_email) or await self._users.get_by_username(
            username_normalized
        ):
            raise UserAlreadyExists()
        now = utcnow()
        user = User(
            id=None,
            email=normalized_email,
            username=display_username,
            username_normalized=username_normalized,
            password_hash=self._hasher.hash(password),
            role=Role.USER,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        return await self._users.add(user)
