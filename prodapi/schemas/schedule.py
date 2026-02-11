from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ScheduleCreate(BaseModel):
    cron: str = Field(..., min_length=9, max_length=100)
    timezone: str = "UTC"
    enabled: bool = True

    @field_validator("cron")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        parts = v.split()
        if len(parts) != 5:
            raise ValueError("Cron expression must have exactly 5 fields")
        return v


class ScheduleUpdate(BaseModel):
    cron: str | None = Field(None, min_length=9, max_length=100)
    timezone: str | None = None
    enabled: bool | None = None

    @field_validator("cron")
    @classmethod
    def validate_cron(cls, v: str | None) -> str | None:
        if v is not None:
            parts = v.split()
            if len(parts) != 5:
                raise ValueError("Cron expression must have exactly 5 fields")
        return v


class ScheduleResponse(BaseModel):
    id: UUID
    automation_id: UUID
    cron: str
    timezone: str
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
