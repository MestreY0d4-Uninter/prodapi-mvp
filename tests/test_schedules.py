from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import create_test_api_key, create_test_automation


async def test_create_schedule(session: AsyncSession, client: AsyncClient) -> None:
    api_key, raw_key = await create_test_api_key(session)
    automation = await create_test_automation(session, api_key.id)

    response = await client.put(
        f"/automations/{automation.id}/schedule",
        headers={"X-API-Key": raw_key},
        json={"cron": "0 0 * * *", "timezone": "UTC"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["cron"] == "0 0 * * *"
    assert data["automation_id"] == str(automation.id)


async def test_create_schedule_invalid_cron(
    session: AsyncSession, client: AsyncClient
) -> None:
    api_key, raw_key = await create_test_api_key(session)
    automation = await create_test_automation(session, api_key.id)

    response = await client.put(
        f"/automations/{automation.id}/schedule",
        headers={"X-API-Key": raw_key},
        json={"cron": "invalid"},
    )
    assert response.status_code == 422


async def test_update_schedule(session: AsyncSession, client: AsyncClient) -> None:
    api_key, raw_key = await create_test_api_key(session)
    automation = await create_test_automation(session, api_key.id)

    await client.put(
        f"/automations/{automation.id}/schedule",
        headers={"X-API-Key": raw_key},
        json={"cron": "0 0 * * *"},
    )

    response = await client.patch(
        f"/automations/{automation.id}/schedule",
        headers={"X-API-Key": raw_key},
        json={"enabled": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is False


async def test_delete_schedule(session: AsyncSession, client: AsyncClient) -> None:
    api_key, raw_key = await create_test_api_key(session)
    automation = await create_test_automation(session, api_key.id)

    await client.put(
        f"/automations/{automation.id}/schedule",
        headers={"X-API-Key": raw_key},
        json={"cron": "0 0 * * *"},
    )

    response = await client.delete(
        f"/automations/{automation.id}/schedule",
        headers={"X-API-Key": raw_key},
    )
    assert response.status_code == 204
