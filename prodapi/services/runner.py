import asyncio
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from prodapi.automations import REGISTRY
from prodapi.models import Automation, AutomationType, Run, RunStatus, TriggerType


async def enqueue_run(
    session: AsyncSession,
    automation_id: UUID,
    triggered_by: TriggerType,
    trigger_meta: dict[str, object] | None = None,
    idempotency_key: str | None = None,
) -> Run:
    stmt = select(Automation).where(Automation.id == automation_id)
    result = await session.execute(stmt)
    automation = result.scalar_one_or_none()

    if automation is None:
        raise ValueError("Automation not found")

    if idempotency_key:
        existing_stmt = select(Run).where(
            Run.automation_id == automation_id,
            Run.idempotency_key == idempotency_key,
        )
        existing_result = await session.execute(existing_stmt)
        existing_run = existing_result.scalar_one_or_none()
        if existing_run:
            return existing_run

    run = Run(
        automation_id=automation_id,
        status=RunStatus.QUEUED,
        triggered_by=triggered_by,
        trigger_meta=trigger_meta or {},
        idempotency_key=idempotency_key,
    )

    session.add(run)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        existing_stmt = select(Run).where(
            Run.automation_id == automation_id,
            Run.idempotency_key == idempotency_key,
        )
        existing_result = await session.execute(existing_stmt)
        return existing_result.scalar_one()

    await session.refresh(run)

    asyncio.create_task(execute_run_background(run.id))

    return run


async def execute_run_background(run_id: UUID) -> None:
    from prodapi.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        await execute_run(session, run_id)


async def execute_run(session: AsyncSession, run_id: UUID) -> None:
    from prodapi.services.webhook import deliver_webhook

    stmt = select(Run).where(Run.id == run_id)
    result = await session.execute(stmt)
    run = result.scalar_one_or_none()

    if run is None:
        return

    run.status = RunStatus.RUNNING
    run.started_at = datetime.now(UTC)
    await session.commit()

    automation_stmt = select(Automation).where(Automation.id == run.automation_id)
    automation_result = await session.execute(automation_stmt)
    automation = automation_result.scalar_one()

    try:
        automation_type = AutomationType(automation.type)
        executor = REGISTRY[automation_type]

        summary = await executor.execute(automation.config_json)

        if automation_type == AutomationType.GITHUB_MONITOR and "updated_state" in summary:
            automation.config_json["state"] = summary["updated_state"]
            await session.commit()

        run.status = RunStatus.SUCCESS
        run.summary_json = summary
        run.error_text = None

    except Exception as e:
        run.status = RunStatus.FAILED
        run.summary_json = None
        run.error_text = str(e)

    run.ended_at = datetime.now(UTC)
    started = run.started_at
    ended = run.ended_at
    if started and ended:
        duration = ended - started
        run.duration_ms = int(duration.total_seconds() * 1000)

    await session.commit()

    webhook_url = automation.config_json.get("webhook_url")
    if webhook_url:
        asyncio.create_task(
            deliver_webhook(
                webhook_url=str(webhook_url),
                automation_id=automation.id,
                run_id=run.id,
                status=run.status,
                automation_type=automation.type,
                summary=run.summary_json,
                error=run.error_text,
            )
        )
