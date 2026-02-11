from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from prodapi.models import RunStatus
from tests.factories import create_test_api_key, create_test_automation, create_test_run


async def test_trigger_run(session: AsyncSession, client: AsyncClient) -> None:
    api_key, raw_key = await create_test_api_key(session)
    automation = await create_test_automation(session, api_key.id)

    response = await client.post(
        f"/automations/{automation.id}/run",
        headers={"X-API-Key": raw_key},
        json={},
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    assert data["automation_id"] == str(automation.id)


async def test_trigger_run_with_idempotency(
    session: AsyncSession, client: AsyncClient
) -> None:
    api_key, raw_key = await create_test_api_key(session)
    automation = await create_test_automation(session, api_key.id)

    response1 = await client.post(
        f"/automations/{automation.id}/run",
        headers={"X-API-Key": raw_key},
        json={"idempotency_key": "test-123"},
    )
    assert response1.status_code == 202
    run1_id = response1.json()["id"]

    response2 = await client.post(
        f"/automations/{automation.id}/run",
        headers={"X-API-Key": raw_key},
        json={"idempotency_key": "test-123"},
    )
    assert response2.status_code == 202
    run2_id = response2.json()["id"]

    assert run1_id == run2_id


async def test_list_runs(session: AsyncSession, client: AsyncClient) -> None:
    api_key, raw_key = await create_test_api_key(session)
    automation = await create_test_automation(session, api_key.id)
    await create_test_run(session, automation.id, RunStatus.SUCCESS)
    await create_test_run(session, automation.id, RunStatus.FAILED)

    response = await client.get("/runs", headers={"X-API-Key": raw_key})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


async def test_list_runs_with_filter(session: AsyncSession, client: AsyncClient) -> None:
    api_key, raw_key = await create_test_api_key(session)
    automation = await create_test_automation(session, api_key.id)
    await create_test_run(session, automation.id, RunStatus.SUCCESS)
    await create_test_run(session, automation.id, RunStatus.FAILED)

    response = await client.get(
        "/runs",
        headers={"X-API-Key": raw_key},
        params={"status": "failed"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "failed"


async def test_get_run(session: AsyncSession, client: AsyncClient) -> None:
    api_key, raw_key = await create_test_api_key(session)
    automation = await create_test_automation(session, api_key.id)
    run = await create_test_run(session, automation.id)

    response = await client.get(f"/runs/{run.id}", headers={"X-API-Key": raw_key})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(run.id)
