from contextlib import asynccontextmanager

from fastapi import HTTPException

from app.domain.exceptions import (
    CannotDeleteSelf,
    CurrentPasswordIncorrect,
    DomainError,
    InvalidCredentials,
    InvalidEmail,
    InvalidToken,
    InvalidUsername,
    LastAdminProtected,
    NoChangesProvided,
    UserAlreadyExists,
    UserInactive,
    UserNotFound,
    WeakPassword,
)

_STATUS = {
    UserAlreadyExists: 409,
    InvalidCredentials: 401,
    UserInactive: 401,
    InvalidToken: 401,
    UserNotFound: 404,
    LastAdminProtected: 409,
    CannotDeleteSelf: 409,
    WeakPassword: 422,
    InvalidUsername: 422,
    InvalidEmail: 422,
    CurrentPasswordIncorrect: 400,
    NoChangesProvided: 422,
}


@asynccontextmanager
async def domain_http():
    try:
        yield
    except DomainError as exc:
        raise HTTPException(status_code=_STATUS.get(type(exc), 400), detail=exc.message) from exc
