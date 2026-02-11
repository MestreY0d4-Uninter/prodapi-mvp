import asyncio
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import httpx

from prodapi.schemas.webhook import WebhookPayload


async def deliver_webhook(
    webhook_url: str,
    automation_id: UUID,
    run_id: UUID,
    status: str,
    automation_type: str,
    summary: dict[str, Any] | None,
    error: str | None,
    max_retries: int = 3,
) -> None:
    payload = WebhookPayload(
        event="run.completed",
        automation_id=automation_id,
        run_id=run_id,
        status=status,
        type=automation_type,
        summary=summary,
        error=error,
        timestamp=datetime.now(UTC),
    )

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    webhook_url,
                    json=payload.model_dump(mode="json"),
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                return
        except (httpx.HTTPStatusError, httpx.RequestError):
            if attempt == max_retries - 1:
                return

            backoff = 2**attempt
            await asyncio.sleep(backoff)
