from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from prodapi.database import get_session
from prodapi.deps import get_current_api_key
from prodapi.models import ApiKey, Automation, Schedule
from prodapi.schemas.schedule import ScheduleCreate, ScheduleResponse, ScheduleUpdate
from prodapi.services.scheduler import scheduler_service

router = APIRouter(prefix="/automations", tags=["schedules"])


@router.put("/{automation_id}/schedule", response_model=ScheduleResponse)
async def create_or_update_schedule(
    automation_id: UUID,
    data: ScheduleCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_key: Annotated[ApiKey, Depends(get_current_api_key)],
) -> ScheduleResponse:
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

    existing_stmt = select(Schedule).where(Schedule.automation_id == automation_id)
    existing_result = await session.execute(existing_stmt)
    schedule = existing_result.scalar_one_or_none()

    try:
        if schedule:
            schedule.cron = data.cron
            schedule.timezone = data.timezone
            schedule.enabled = data.enabled
        else:
            schedule = Schedule(
                automation_id=automation_id,
                cron=data.cron,
                timezone=data.timezone,
                enabled=data.enabled,
            )
            session.add(schedule)

        await session.commit()
        await session.refresh(schedule)

        if schedule.enabled:
            scheduler_service.add_schedule(
                schedule_id=schedule.id,
                automation_id=automation_id,
                cron=schedule.cron,
                timezone=schedule.timezone,
            )
        else:
            scheduler_service.remove_schedule(schedule.id)

    except (ValueError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e

    return ScheduleResponse.model_validate(schedule)


@router.patch("/{automation_id}/schedule", response_model=ScheduleResponse)
async def update_schedule(
    automation_id: UUID,
    data: ScheduleUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_key: Annotated[ApiKey, Depends(get_current_api_key)],
) -> ScheduleResponse:
    stmt = (
        select(Schedule)
        .join(Automation)
        .where(
            Schedule.automation_id == automation_id,
            Automation.owner_key_id == current_key.id,
        )
    )
    result = await session.execute(stmt)
    schedule = result.scalar_one_or_none()

    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    try:
        if data.cron is not None:
            schedule.cron = data.cron
        if data.timezone is not None:
            schedule.timezone = data.timezone
        if data.enabled is not None:
            schedule.enabled = data.enabled

        await session.commit()
        await session.refresh(schedule)

        if schedule.enabled:
            scheduler_service.add_schedule(
                schedule_id=schedule.id,
                automation_id=automation_id,
                cron=schedule.cron,
                timezone=schedule.timezone,
            )
        else:
            scheduler_service.remove_schedule(schedule.id)

    except (ValueError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e

    return ScheduleResponse.model_validate(schedule)


@router.delete("/{automation_id}/schedule", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    automation_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_key: Annotated[ApiKey, Depends(get_current_api_key)],
) -> None:
    stmt = (
        select(Schedule)
        .join(Automation)
        .where(
            Schedule.automation_id == automation_id,
            Automation.owner_key_id == current_key.id,
        )
    )
    result = await session.execute(stmt)
    schedule = result.scalar_one_or_none()

    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    scheduler_service.remove_schedule(schedule.id)
    await session.delete(schedule)
    await session.commit()
