import asyncio
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import httpx

from prodapi.schemas.webhook import WebhookPayload

logger = logging.getLogger(__name__)


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
                logger.info(
                    "Webhook delivered to %s for run %s",
                    webhook_url,
                    run_id,
                )
                return
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            if attempt == max_retries - 1:
                logger.error(
                    "Webhook delivery failed after %d retries to %s for run %s: %s",
                    max_retries,
                    webhook_url,
                    run_id,
                    str(e),
                )
                return

            backoff = 2**attempt
            await asyncio.sleep(backoff)
