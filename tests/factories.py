from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from prodapi.models import ApiKey, Automation, Run, RunStatus, Schedule, TriggerType
from prodapi.services.auth import create_api_key


async def create_test_api_key(session: AsyncSession, label: str = "test") -> tuple[ApiKey, str]:
    return await create_api_key(session, label)


async def create_test_automation(
    session: AsyncSession,
    owner_key_id: UUID,
    name: str = "Test Automation",
    automation_type: str = "daily_digest",
    config: dict[str, Any] | None = None,
) -> Automation:
    if config is None:
        config = {"webhook_url": "https://example.com/webhook"}

    automation = Automation(
        owner_key_id=owner_key_id,
        name=name,
        type=automation_type,
        config_json=config,
        enabled=True,
    )
    session.add(automation)
    await session.commit()
    await session.refresh(automation)
    return automation


async def create_test_run(
    session: AsyncSession,
    automation_id: UUID,
    status: RunStatus = RunStatus.QUEUED,
) -> Run:
    run = Run(
        automation_id=automation_id,
        status=status,
        triggered_by=TriggerType.MANUAL,
        trigger_meta={},
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


async def create_test_schedule(
    session: AsyncSession,
    automation_id: UUID,
    cron: str = "0 0 * * *",
) -> Schedule:
    schedule = Schedule(
        automation_id=automation_id,
        cron=cron,
        timezone="UTC",
        enabled=True,
    )
    session.add(schedule)
    await session.commit()
    await session.refresh(schedule)
    return schedule
