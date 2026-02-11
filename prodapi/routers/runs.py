from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from prodapi.database import get_session
from prodapi.deps import get_current_api_key
from prodapi.models import ApiKey, Automation, Run, RunStatus, TriggerType
from prodapi.schemas.run import RunResponse, RunTriggerRequest
from prodapi.services.runner import enqueue_run

router = APIRouter(prefix="/automations", tags=["runs"])
runs_router = APIRouter(tags=["runs"])


@router.post(
    "/{automation_id}/run",
    response_model=RunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_run(
    automation_id: UUID,
    data: RunTriggerRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_key: Annotated[ApiKey, Depends(get_current_api_key)],
) -> RunResponse:
    stmt = select(Automation).where(
        Automation.id == automation_id,
        Automation.owner_key_id == current_key.id,
    )
    result = await session.execute(stmt)
    automation = result.scalar_one_or_none()

    if automation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation not found",
        )

    run = await enqueue_run(
        session=session,
        automation_id=automation_id,
        triggered_by=TriggerType.MANUAL,
        trigger_meta={"api_key_id": str(current_key.id)},
        idempotency_key=data.idempotency_key,
    )

    return RunResponse.model_validate(run)


@runs_router.get("/runs", response_model=list[RunResponse])
async def list_runs(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_key: Annotated[ApiKey, Depends(get_current_api_key)],
    automation_id: UUID | None = Query(None),
    status_filter: RunStatus | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    cursor: UUID | None = Query(None),
) -> list[RunResponse]:
    stmt = (
        select(Run)
        .join(Automation)
        .where(Automation.owner_key_id == current_key.id)
    )

    if automation_id:
        stmt = stmt.where(Run.automation_id == automation_id)

    if status_filter:
        stmt = stmt.where(Run.status == status_filter)

    if cursor:
        stmt = stmt.where(Run.id < cursor)

    stmt = stmt.order_by(Run.queued_at.desc()).limit(limit)

    result = await session.execute(stmt)
    runs = result.scalars().all()

    return [RunResponse.model_validate(r) for r in runs]


@runs_router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_key: Annotated[ApiKey, Depends(get_current_api_key)],
) -> RunResponse:
    stmt = (
        select(Run)
        .join(Automation)
        .where(
            Run.id == run_id,
            Automation.owner_key_id == current_key.id,
        )
    )
    result = await session.execute(stmt)
    run = result.scalar_one_or_none()

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    return RunResponse.model_validate(run)
