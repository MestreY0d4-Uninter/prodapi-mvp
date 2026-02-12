from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from prodapi.database import get_session
from prodapi.deps import get_current_api_key
from prodapi.models import ApiKey
from prodapi.schemas.api_key import ApiKeyCreate, ApiKeyCreated, ApiKeyResponse
from prodapi.services.auth import create_api_key, revoke_api_key

router = APIRouter(prefix="/apikeys", tags=["api-keys"])


@router.post("", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_key(
    data: ApiKeyCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ApiKeyCreated:
    api_key, raw_key = await create_api_key(session, data.label)
    return ApiKeyCreated(
        api_key=ApiKeyResponse.model_validate(api_key),
        raw_key=raw_key,
    )


@router.post("/revoke/{key_id}", response_model=ApiKeyResponse)
async def revoke_key(
    key_id: UUID,
    current_key: Annotated[ApiKey, Depends(get_current_api_key)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ApiKeyResponse:
    if current_key.id != key_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot revoke another user's API key",
        )

    api_key = await revoke_api_key(session, key_id)

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return ApiKeyResponse.model_validate(api_key)
