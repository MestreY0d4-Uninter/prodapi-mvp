from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import create_test_api_key, create_test_automation


async def test_create_automation(session: AsyncSession, client: AsyncClient) -> None:
    _, raw_key = await create_test_api_key(session)

    response = await client.post(
        "/automations",
        headers={"X-API-Key": raw_key},
        json={
            "name": "My Automation",
            "type": "daily_digest",
            "config_json": {"webhook_url": "https://example.com/hook"},
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Automation"
    assert data["type"] == "daily_digest"


async def test_create_automation_invalid_config(
    session: AsyncSession, client: AsyncClient
) -> None:
    _, raw_key = await create_test_api_key(session)

    response = await client.post(
        "/automations",
        headers={"X-API-Key": raw_key},
        json={
            "name": "Invalid",
            "type": "daily_digest",
            "config_json": {"invalid": "config"},
        },
    )
    assert response.status_code == 422


async def test_list_automations(session: AsyncSession, client: AsyncClient) -> None:
    api_key, raw_key = await create_test_api_key(session)
    await create_test_automation(session, api_key.id, "Auto 1")
    await create_test_automation(session, api_key.id, "Auto 2")

    response = await client.get("/automations", headers={"X-API-Key": raw_key})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


async def test_get_automation(session: AsyncSession, client: AsyncClient) -> None:
    api_key, raw_key = await create_test_api_key(session)
    automation = await create_test_automation(session, api_key.id)

    response = await client.get(
        f"/automations/{automation.id}", headers={"X-API-Key": raw_key}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(automation.id)


async def test_update_automation(session: AsyncSession, client: AsyncClient) -> None:
    api_key, raw_key = await create_test_api_key(session)
    automation = await create_test_automation(session, api_key.id)

    response = await client.patch(
        f"/automations/{automation.id}",
        headers={"X-API-Key": raw_key},
        json={"enabled": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is False


async def test_delete_automation(session: AsyncSession, client: AsyncClient) -> None:
    api_key, raw_key = await create_test_api_key(session)
    automation = await create_test_automation(session, api_key.id)

    response = await client.delete(
        f"/automations/{automation.id}", headers={"X-API-Key": raw_key}
    )
    assert response.status_code == 204

    response = await client.get(
        f"/automations/{automation.id}", headers={"X-API-Key": raw_key}
    )
    assert response.status_code == 404


async def test_owner_isolation(session: AsyncSession, client: AsyncClient) -> None:
    api_key1, raw_key1 = await create_test_api_key(session, "owner1")
    api_key2, raw_key2 = await create_test_api_key(session, "owner2")

    automation = await create_test_automation(session, api_key1.id)

    response = await client.get(
        f"/automations/{automation.id}", headers={"X-API-Key": raw_key2}
    )
    assert response.status_code == 404
