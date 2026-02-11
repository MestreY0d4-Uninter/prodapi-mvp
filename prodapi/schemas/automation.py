from datetime import datetime
from typing import Any, cast
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from prodapi.models import AutomationType


class AutomationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: AutomationType
    config_json: dict[str, Any]
    enabled: bool = True


class AutomationUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    config_json: dict[str, Any] | None = None
    enabled: bool | None = None


class AutomationResponse(BaseModel):
    id: UUID
    owner_key_id: UUID
    name: str
    type: str
    config_json: dict[str, Any]
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("config_json", mode="before")
    @classmethod
    def sanitize_config(cls, v: Any) -> dict[str, Any]:
        if isinstance(v, dict) and "github_token" in v:
            safe_v = v.copy()
            safe_v["github_token"] = "***" if v["github_token"] else None
            return safe_v
        return cast(dict[str, Any], v)
