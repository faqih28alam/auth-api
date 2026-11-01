from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import Response

from app.application.dto import TokenPair
from app.application.use_cases.login_user import LoginUser
from app.application.use_cases.logout_user import LogoutUser
from app.application.use_cases.refresh_session import RefreshSession
from app.application.use_cases.register_user import RegisterUser
from app.domain.entities.user import User
from app.presentation.api.deps import (
    get_current_user,
    get_login_user,
    get_logout_user,
    get_refresh_session,
    get_register_user,
)
from app.presentation.api.errors import domain_http
from app.presentation.api.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.presentation.api.schemas.user import UserResponse, to_user_response
from app.presentation.rate_limit import LOGIN_LIMIT, REFRESH_LIMIT, REGISTER_LIMIT, limiter

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_response(pair: TokenPair) -> TokenResponse:
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        token_type=pair.token_type,
        expires_in=pair.expires_in,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(REGISTER_LIMIT)
async def register(
    request: Request,
    body: RegisterRequest,
    use_case: RegisterUser = Depends(get_register_user),
) -> UserResponse:
    async with domain_http():
        user = await use_case.execute(body.email, body.username, body.password)
    return to_user_response(user)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(LOGIN_LIMIT)
async def login(
    request: Request,
    body: LoginRequest,
    use_case: LoginUser = Depends(get_login_user),
) -> TokenResponse:
    async with domain_http():
        pair = await use_case.execute(body.login, body.password)
    return _token_response(pair)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(REFRESH_LIMIT)
async def refresh(
    request: Request,
    body: RefreshRequest,
    use_case: RefreshSession = Depends(get_refresh_session),
) -> TokenResponse:
    async with domain_http():
        pair = await use_case.execute(body.refresh_token)
    return _token_response(pair)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: LogoutRequest,
    user: User = Depends(get_current_user),
    use_case: LogoutUser = Depends(get_logout_user),
) -> Response:
    async with domain_http():
        await use_case.execute(user.id or "", body.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
