from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import create_test_api_key


async def test_create_api_key(client: AsyncClient) -> None:
    response = await client.post("/apikeys", json={"label": "test-key"})
    assert response.status_code == 201

    data = response.json()
    assert "api_key" in data
    assert "raw_key" in data
    assert data["api_key"]["label"] == "test-key"
    assert len(data["raw_key"]) > 20


async def test_revoke_api_key(session: AsyncSession, client: AsyncClient) -> None:
    api_key, _ = await create_test_api_key(session, "test-revoke")

    response = await client.post(f"/apikeys/revoke/{api_key.id}")
    assert response.status_code == 200

    data = response.json()
    assert data["revoked_at"] is not None


async def test_revoke_nonexistent_key(client: AsyncClient) -> None:
    response = await client.post("/apikeys/revoke/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


async def test_auth_with_valid_key(session: AsyncSession, client: AsyncClient) -> None:
    _, raw_key = await create_test_api_key(session, "test-auth")

    response = await client.get("/automations", headers={"X-API-Key": raw_key})
    assert response.status_code == 200


async def test_auth_with_invalid_key(client: AsyncClient) -> None:
    response = await client.get("/automations", headers={"X-API-Key": "invalid"})
    assert response.status_code == 401


async def test_auth_with_revoked_key(session: AsyncSession, client: AsyncClient) -> None:
    api_key, raw_key = await create_test_api_key(session, "test-revoked")

    await client.post(f"/apikeys/revoke/{api_key.id}")

    response = await client.get("/automations", headers={"X-API-Key": raw_key})
    assert response.status_code == 401
