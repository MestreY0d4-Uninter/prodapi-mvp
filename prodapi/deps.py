from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from prodapi.database import get_session
from prodapi.models import ApiKey
from prodapi.services.auth import verify_api_key


async def get_current_api_key(
    x_api_key: Annotated[str, Header()],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ApiKey:
    api_key = await verify_api_key(session, x_api_key)

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
        )

    return api_key
