import pytest

@pytest.mark.asyncio
async def test_register_user(async_client):
    response = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "newuser@example.com", "password": "newpassword"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_login_user(async_client, test_user):
    response = await async_client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "testpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_read_users_me(async_client, auth_headers):
    response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
