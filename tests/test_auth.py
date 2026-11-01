import pytest

from app.infrastructure.config import Settings
from app.main import create_app
from tests.helpers import assert_public_user, bearer, login, register


def test_production_rejects_placeholder_secret():
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        create_app(
            Settings(
                environment="production",
                jwt_secret="change-me-to-a-long-random-string",
                cors_origins="https://app.example.com",
                trusted_hosts="api.example.com",
                mongodb_uri="mongodb://user:pass@mongo:27017/auth?authSource=admin",
            )
        )


def test_production_rejects_wildcard_cors():
    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        create_app(
            Settings(
                environment="production",
                jwt_secret="x" * 48,
                cors_origins="*",
                trusted_hosts="api.example.com",
                mongodb_uri="mongodb://user:pass@mongo:27017/auth?authSource=admin",
            )
        )


def test_production_hides_openapi():
    app = create_app(
        Settings(
            environment="production",
            jwt_secret="x" * 48,
            cors_origins="https://app.example.com",
            trusted_hosts="api.example.com",
            mongodb_uri="mongodb://user:pass@mongo:27017/auth?authSource=admin",
        )
    )
    assert app.docs_url is None
    assert app.redoc_url is None
    assert app.openapi_url is None


async def test_register_login_and_me(client):
    created = await register(client, "ada@example.com", "ada_lovelace")
    assert created["role"] == "user"
    assert created["email"] == "ada@example.com"
    assert_public_user(created)

    by_username = await login(client, "Ada_Lovelace", "Password1")
    by_email = await login(client, "Ada@Example.com", "Password1")
    assert by_username["token_type"] == "bearer"
    assert by_email["expires_in"] == 900

    me = await client.get("/api/v1/users/me", headers=bearer(by_email["access_token"]))
    assert me.status_code == 200
    assert me.json()["username"] == "ada_lovelace"
    assert_public_user(me.json())


async def test_register_rejects_role_and_weak_password(client):
    extra = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "role@example.com",
            "username": "role_user",
            "password": "Password1",
            "role": "admin",
        },
    )
    assert extra.status_code == 422

    weak = await client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "username": "weak_user", "password": "password"},
    )
    assert weak.status_code == 422

    operator = await client.post(
        "/api/v1/auth/login",
        json={"login": {"$gt": ""}, "password": "Password1"},
    )
    assert operator.status_code == 422


async def test_duplicate_identity_is_case_insensitive(client):
    await register(client, "dup@example.com", "DupUser")
    email_clash = await client.post(
        "/api/v1/auth/register",
        json={"email": "DUP@example.com", "username": "other_name", "password": "Password1"},
    )
    username_clash = await client.post(
        "/api/v1/auth/register",
        json={"email": "other@example.com", "username": "dupuser", "password": "Password1"},
    )
    assert email_clash.status_code == 409
    assert username_clash.status_code == 409


async def test_login_failures_share_one_message(client):
    await register(client, "known@example.com", "known_user")
    missing = await client.post(
        "/api/v1/auth/login",
        json={"login": "missing_user", "password": "Password1"},
    )
    wrong = await client.post(
        "/api/v1/auth/login",
        json={"login": "known_user", "password": "WrongPass1"},
    )
    assert missing.status_code == wrong.status_code == 401
    assert missing.json()["detail"] == wrong.json()["detail"] == "Invalid login or password."


async def test_refresh_reuse_revokes_the_new_token(client):
    tokens = await login(client, "Admin", "Admin123")
    refreshed = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refreshed.status_code == 200
    new_refresh = refreshed.json()["refresh_token"]

    reused = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert reused.status_code == 401

    revoked = await client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert revoked.status_code == 401


async def test_logout_and_password_change_revoke_refresh_tokens(client):
    first = await login(client, "Admin", "Admin123")
    logged_out = await client.post(
        "/api/v1/auth/logout",
        headers=bearer(first["access_token"]),
        json={"refresh_token": first["refresh_token"]},
    )
    assert logged_out.status_code == 204
    after_logout = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": first["refresh_token"]},
    )
    assert after_logout.status_code == 401

    second = await login(client, "Admin", "Admin123")
    changed = await client.patch(
        "/api/v1/users/me/password",
        headers=bearer(second["access_token"]),
        json={"current_password": "Admin123", "new_password": "BetterPass1"},
    )
    assert changed.status_code == 204
    old_login = await client.post(
        "/api/v1/auth/login",
        json={"login": "Admin", "password": "Admin123"},
    )
    assert old_login.status_code == 401
    new_login = await login(client, "admin@example.com", "BetterPass1")
    stale_refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": second["refresh_token"]},
    )
    assert stale_refresh.status_code == 401
    assert new_login["access_token"]
