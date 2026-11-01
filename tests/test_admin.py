from tests.helpers import assert_public_user, bearer, login, register


async def test_user_cannot_call_admin_routes(client):
    await register(client, "member@example.com", "member_user")
    tokens = await login(client, "member_user", "Password1")
    headers = bearer(tokens["access_token"])

    stats = await client.get("/api/v1/admin/users/stats", headers=headers)
    listing = await client.get("/api/v1/admin/users", headers=headers)
    assert stats.status_code == 403
    assert listing.status_code == 403


async def test_admin_stats_list_and_search(client):
    await register(client, "ada@example.com", "ada_lovelace")
    await register(client, "grace@example.com", "grace_hopper")
    admin = await login(client, "Admin", "Admin123")
    headers = bearer(admin["access_token"])

    stats = await client.get("/api/v1/admin/users/stats", headers=headers)
    assert stats.status_code == 200
    body = stats.json()
    assert body["total"] == 3
    assert body["active"] == 3
    assert body["by_role"] == {"admin": 1, "user": 2}

    listing = await client.get("/api/v1/admin/users", headers=headers, params={"limit": 1})
    assert listing.status_code == 200
    page = listing.json()
    assert page["total"] == 3
    assert page["limit"] == 1
    assert len(page["items"]) == 1
    assert_public_user(page["items"][0])

    search = await client.get(
        "/api/v1/admin/users",
        headers=headers,
        params={"search": "grace", "role": "user"},
    )
    assert search.status_code == 200
    assert search.json()["total"] == 1
    assert search.json()["items"][0]["username"] == "grace_hopper"

    operators = await client.get(
        "/api/v1/admin/users",
        headers=headers,
        params={"search": '{"$gt":""}'},
    )
    assert operators.status_code == 200
    assert operators.json()["total"] == 0


async def test_inactive_user_is_rejected_with_the_same_login_error(client):
    created = await register(client, "inactive@example.com", "inactive_user")
    admin = await login(client, "Admin", "Admin123")
    updated = await client.patch(
        f"/api/v1/admin/users/{created['id']}",
        headers=bearer(admin["access_token"]),
        json={"is_active": False},
    )
    assert updated.status_code == 200
    assert updated.json()["is_active"] is False

    inactive = await client.post(
        "/api/v1/auth/login",
        json={"login": "inactive_user", "password": "Password1"},
    )
    wrong = await client.post(
        "/api/v1/auth/login",
        json={"login": "inactive_user", "password": "WrongPass1"},
    )
    assert inactive.status_code == wrong.status_code == 401
    assert inactive.json()["detail"] == wrong.json()["detail"]


async def test_last_admin_and_self_delete_are_protected(client):
    admin = await login(client, "Admin", "Admin123")
    headers = bearer(admin["access_token"])
    me = await client.get("/api/v1/users/me", headers=headers)
    admin_id = me.json()["id"]

    demote = await client.patch(
        f"/api/v1/admin/users/{admin_id}",
        headers=headers,
        json={"role": "user"},
    )
    deactivate = await client.patch(
        f"/api/v1/admin/users/{admin_id}",
        headers=headers,
        json={"is_active": False},
    )
    delete_self = await client.delete(f"/api/v1/admin/users/{admin_id}", headers=headers)
    assert demote.status_code == 409
    assert deactivate.status_code == 409
    assert delete_self.status_code == 409

    created = await register(client, "second@example.com", "second_admin")
    promoted = await client.patch(
        f"/api/v1/admin/users/{created['id']}",
        headers=headers,
        json={"role": "admin"},
    )
    assert promoted.status_code == 200
    assert promoted.json()["role"] == "admin"

    still_self = await client.delete(f"/api/v1/admin/users/{admin_id}", headers=headers)
    assert still_self.status_code == 409

    demoted = await client.patch(
        f"/api/v1/admin/users/{admin_id}",
        headers=headers,
        json={"role": "user"},
    )
    assert demoted.status_code == 200

    second = await login(client, "second_admin", "Password1")
    last_demote = await client.patch(
        f"/api/v1/admin/users/{created['id']}",
        headers=bearer(second["access_token"]),
        json={"role": "user"},
    )
    assert last_demote.status_code == 409

    removed = await client.delete(
        f"/api/v1/admin/users/{admin_id}",
        headers=bearer(second["access_token"]),
    )
    assert removed.status_code == 204
    missing = await client.get(
        f"/api/v1/admin/users/{admin_id}",
        headers=bearer(second["access_token"]),
    )
    assert missing.status_code == 404
