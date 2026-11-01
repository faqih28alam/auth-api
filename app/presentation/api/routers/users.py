from fastapi import APIRouter, Depends, status
from fastapi.responses import Response

from app.application.use_cases.change_password import ChangePassword
from app.domain.entities.user import User
from app.presentation.api.deps import get_change_password, get_current_user
from app.presentation.api.errors import domain_http
from app.presentation.api.schemas.auth import PasswordChangeRequest
from app.presentation.api.schemas.user import UserResponse, to_user_response

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> UserResponse:
    return to_user_response(user)


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: PasswordChangeRequest,
    user: User = Depends(get_current_user),
    use_case: ChangePassword = Depends(get_change_password),
) -> Response:
    async with domain_http():
        await use_case.execute(user.id or "", body.current_password, body.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
