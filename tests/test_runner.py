from sqlalchemy.ext.asyncio import AsyncSession

from prodapi.models import RunStatus
from prodapi.services.runner import execute_run
from tests.factories import create_test_api_key, create_test_automation, create_test_run


async def test_execute_run_success(session: AsyncSession) -> None:
    api_key, _ = await create_test_api_key(session)
    automation = await create_test_automation(session, api_key.id)
    run = await create_test_run(session, automation.id)

    await execute_run(session, run.id)

    await session.refresh(run)
    assert run.status == RunStatus.SUCCESS
    assert run.started_at is not None
    assert run.ended_at is not None
    assert run.duration_ms is not None
    assert run.summary_json is not None


async def test_execute_run_with_invalid_config(session: AsyncSession) -> None:
    api_key, _ = await create_test_api_key(session)
    automation = await create_test_automation(
        session,
        api_key.id,
        config={"invalid": "config"},
    )
    run = await create_test_run(session, automation.id)

    await execute_run(session, run.id)

    await session.refresh(run)
    assert run.status == RunStatus.FAILED
    assert run.error_text is not None
