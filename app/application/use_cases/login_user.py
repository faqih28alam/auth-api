from app.application.dto import TokenPair
from app.application.token_issuer import TokenIssuer
from app.domain.exceptions import InvalidCredentials, UserInactive
from app.domain.ports.password_hasher import PasswordHasher
from app.domain.repositories.user_repository import UserRepository


class LoginUser:
    def __init__(self, users: UserRepository, hasher: PasswordHasher, issuer: TokenIssuer) -> None:
        self._users = users
        self._hasher = hasher
        self._issuer = issuer

    async def execute(self, login: str, password: str) -> TokenPair:
        identifier = login.strip()
        if "@" in identifier:
            user = await self._users.get_by_email(identifier.lower())
        else:
            user = await self._users.get_by_username(identifier.lower())
        if user is None:
            self._hasher.verify(password, self._hasher.dummy_hash)
            raise InvalidCredentials()
        if not self._hasher.verify(password, user.password_hash):
            raise InvalidCredentials()
        if not user.is_active:
            raise UserInactive()
        return await self._issuer.issue(user)
