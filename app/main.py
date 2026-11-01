import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.application.use_cases.seed_admin import SeedAdmin
from app.domain.exceptions import DomainError, UserAlreadyExists
from app.infrastructure.config import DEFAULT_ADMIN_PASSWORD, Settings, ensure_production_safe
from app.infrastructure.container import Container
from app.infrastructure.database.mongo import create_mongo_client
from app.infrastructure.repositories.mongo_refresh_token_repository import (
    MongoRefreshTokenRepository,
)
from app.infrastructure.repositories.mongo_user_repository import MongoUserRepository
from app.infrastructure.security.jwt import JwtTokenService
from app.infrastructure.security.password import Argon2PasswordHasher
from app.presentation.api.router import api_router
from app.presentation.middleware import LimitRequestSizeMiddleware, SecurityHeadersMiddleware
from app.presentation.rate_limit import limiter

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings()
    ensure_production_safe(resolved)
    limiter.enabled = resolved.environment.lower() != "test"

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        client = create_mongo_client(resolved.mongodb_uri)
        database = client[resolved.mongodb_db]
        users = MongoUserRepository(database)
        refresh_tokens = MongoRefreshTokenRepository(database)
        hasher = Argon2PasswordHasher(testing=resolved.environment.lower() == "test")
        tokens = JwtTokenService(resolved)
        try:
            await users.ensure_indexes()
            await refresh_tokens.ensure_indexes()
            app.state.container = Container(
                settings=resolved,
                mongo_client=client,
                users=users,
                refresh_tokens=refresh_tokens,
                hasher=hasher,
                tokens=tokens,
            )
            try:
                await SeedAdmin(
                    users,
                    hasher,
                    email=resolved.admin_email,
                    username=resolved.admin_username,
                    password=resolved.admin_password,
                ).execute()
            except UserAlreadyExists:
                logger.info("Admin user already exists.")
            except DomainError as exc:
                raise RuntimeError(f"Cannot seed admin: {exc.message}") from exc
            if resolved.is_production and resolved.admin_password == DEFAULT_ADMIN_PASSWORD:
                logger.warning(
                    "Default admin password is still in use. Change it before exposing this service."
                )
            yield
        finally:
            await client.close()

    app = FastAPI(
        title="Auth API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None if resolved.is_production else "/docs",
        redoc_url=None if resolved.is_production else "/redoc",
        openapi_url=None if resolved.is_production else "/openapi.json",
    )
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})

    @app.exception_handler(Exception)
    async def unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    if resolved.is_production:
        allowed_hosts = list(resolved.trusted_host_list)
        for extra in ("localhost", "127.0.0.1"):
            if extra not in allowed_hosts:
                allowed_hosts.append(extra)
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.add_middleware(LimitRequestSizeMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.include_router(api_router)
    return app


app = create_app()
