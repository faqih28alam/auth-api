from httpx import AsyncClient


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def assert_public_user(payload: dict) -> None:
    assert "password" not in payload
    assert "password_hash" not in payload


async def register(client: AsyncClient, email: str, username: str, password: str = "Password1") -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def login(client: AsyncClient, identifier: str, password: str) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={"login": identifier, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()
