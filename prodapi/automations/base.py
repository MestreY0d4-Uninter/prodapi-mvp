from typing import Any, Protocol

from pydantic import BaseModel


class AutomationExecutor(Protocol):
    @staticmethod
    def validate_config(config: dict[str, Any]) -> BaseModel: ...

    @staticmethod
    async def execute(config: dict[str, Any]) -> dict[str, Any]: ...
