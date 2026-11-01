async def test_health_and_security_headers(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["cache-control"] == "no-store"
    assert "default-src 'none'" in response.headers["content-security-policy"]


async def test_openapi_is_available_outside_production(client):
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    assert "/api/v1/auth/login" in response.text


async def test_oversized_body_is_rejected(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"login": "Admin", "password": "A" * 70_000},
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "Request body too large"
