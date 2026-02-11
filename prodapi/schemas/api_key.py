from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ApiKeyCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=100)


class ApiKeyResponse(BaseModel):
    id: UUID
    label: str
    created_at: datetime
    revoked_at: datetime | None
    last_used_at: datetime | None

    model_config = {"from_attributes": True}


class ApiKeyCreated(BaseModel):
    api_key: ApiKeyResponse
    raw_key: str
