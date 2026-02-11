from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from prodapi.models import RunStatus


class RunTriggerRequest(BaseModel):
    idempotency_key: str | None = None


class RunResponse(BaseModel):
    id: UUID
    automation_id: UUID
    status: str
    queued_at: datetime
    started_at: datetime | None
    ended_at: datetime | None
    duration_ms: int | None
    summary_json: dict[str, Any] | None
    error_text: str | None
    idempotency_key: str | None
    triggered_by: str
    trigger_meta: dict[str, Any]

    model_config = {"from_attributes": True}


class RunListParams(BaseModel):
    automation_id: UUID | None = None
    status: RunStatus | None = None
    limit: int = 50
    cursor: UUID | None = None
