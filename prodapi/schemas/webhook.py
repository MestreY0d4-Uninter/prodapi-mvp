from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class WebhookPayload(BaseModel):
    event: str
    automation_id: UUID
    run_id: UUID
    status: str
    type: str
    summary: dict[str, Any] | None
    error: str | None
    timestamp: datetime
