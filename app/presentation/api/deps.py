from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.token_issuer import TokenIssuer
from app.application.use_cases.change_password import ChangePassword
from app.application.use_cases.delete_user import DeleteUser
from app.application.use_cases.get_user import GetUser
from app.application.use_cases.get_user_stats import GetUserStats
from app.application.use_cases.list_users import ListUsers
from app.application.use_cases.login_user import LoginUser
from app.application.use_cases.logout_user import LogoutUser
from app.application.use_cases.refresh_session import RefreshSession
from app.application.use_cases.register_user import RegisterUser
from app.application.use_cases.update_user import UpdateUser
from app.domain.entities.user import Role, User
from app.domain.exceptions import InvalidToken
from app.infrastructure.container import Container

_bearer = HTTPBearer(auto_error=False)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_token_issuer(container: Container = Depends(get_container)) -> TokenIssuer:
    return TokenIssuer(
        container.tokens,
        container.refresh_tokens,
        container.settings.refresh_token_expire_days,
    )


def get_register_user(container: Container = Depends(get_container)) -> RegisterUser:
    return RegisterUser(container.users, container.hasher)


def get_login_user(
    container: Container = Depends(get_container),
    issuer: TokenIssuer = Depends(get_token_issuer),
) -> LoginUser:
    return LoginUser(container.users, container.hasher, issuer)


def get_refresh_session(
    container: Container = Depends(get_container),
    issuer: TokenIssuer = Depends(get_token_issuer),
) -> RefreshSession:
    return RefreshSession(container.users, container.refresh_tokens, container.tokens, issuer)


def get_logout_user(container: Container = Depends(get_container)) -> LogoutUser:
    return LogoutUser(container.refresh_tokens, container.tokens)


def get_change_password(container: Container = Depends(get_container)) -> ChangePassword:
    return ChangePassword(container.users, container.hasher, container.refresh_tokens)


def get_list_users(container: Container = Depends(get_container)) -> ListUsers:
    return ListUsers(container.users)


def get_user_stats(container: Container = Depends(get_container)) -> GetUserStats:
    return GetUserStats(container.users)


def get_user(container: Container = Depends(get_container)) -> GetUser:
    return GetUser(container.users)


def get_update_user(container: Container = Depends(get_container)) -> UpdateUser:
    return UpdateUser(container.users)


def get_delete_user(container: Container = Depends(get_container)) -> DeleteUser:
    return DeleteUser(container.users, container.refresh_tokens)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    container = get_container(request)
    try:
        user_id, _role = container.tokens.decode_access_token(credentials.credentials)
    except InvalidToken as exc:
        raise _unauthorized() from exc
    user = await container.users.get_by_id(user_id)
    if user is None or not user.is_active:
        raise _unauthorized()
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
