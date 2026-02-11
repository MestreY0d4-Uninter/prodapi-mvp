from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from prodapi.automations import validate_automation_config
from prodapi.database import get_session
from prodapi.deps import get_current_api_key
from prodapi.models import ApiKey, Automation, AutomationType
from prodapi.schemas.automation import (
    AutomationCreate,
    AutomationResponse,
    AutomationUpdate,
)

router = APIRouter(prefix="/automations", tags=["automations"])


@router.post("", response_model=AutomationResponse, status_code=status.HTTP_201_CREATED)
async def create_automation(
    data: AutomationCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_key: Annotated[ApiKey, Depends(get_current_api_key)],
) -> AutomationResponse:
    try:
        validated_config = validate_automation_config(data.type, data.config_json)
    except (ValidationError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e

    automation = Automation(
        owner_key_id=current_key.id,
        name=data.name,
        type=data.type.value,
        config_json=validated_config,
        enabled=data.enabled,
    )
    session.add(automation)
    await session.commit()
    await session.refresh(automation)

    return AutomationResponse.model_validate(automation)


@router.get("", response_model=list[AutomationResponse])
async def list_automations(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_key: Annotated[ApiKey, Depends(get_current_api_key)],
) -> list[AutomationResponse]:
    stmt = select(Automation).where(Automation.owner_key_id == current_key.id)
    result = await session.execute(stmt)
    automations = result.scalars().all()

    return [AutomationResponse.model_validate(a) for a in automations]


@router.get("/{automation_id}", response_model=AutomationResponse)
async def get_automation(
    automation_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_key: Annotated[ApiKey, Depends(get_current_api_key)],
) -> AutomationResponse:
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

    return AutomationResponse.model_validate(automation)


@router.patch("/{automation_id}", response_model=AutomationResponse)
async def update_automation(
    automation_id: UUID,
    data: AutomationUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_key: Annotated[ApiKey, Depends(get_current_api_key)],
) -> AutomationResponse:
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

    if data.config_json is not None:
        try:
            automation_type = AutomationType(automation.type)
            validated_config = validate_automation_config(automation_type, data.config_json)
            automation.config_json = validated_config
        except (ValidationError, ValueError) as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e),
            ) from e

    if data.name is not None:
        automation.name = data.name

    if data.enabled is not None:
        automation.enabled = data.enabled

    await session.commit()
    await session.refresh(automation)

    return AutomationResponse.model_validate(automation)


@router.delete("/{automation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_automation(
    automation_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_key: Annotated[ApiKey, Depends(get_current_api_key)],
) -> None:
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

    await session.delete(automation)
    await session.commit()
