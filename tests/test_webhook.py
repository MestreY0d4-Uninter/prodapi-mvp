from unittest.mock import AsyncMock, patch
from uuid import uuid4

import httpx

from prodapi.services.webhook import deliver_webhook


async def test_deliver_webhook_success() -> None:
    with (
        patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post,
        patch("prodapi.services.webhook.logger") as mock_logger,
    ):
        mock_post.return_value.status_code = 200

        await deliver_webhook(
            webhook_url="https://example.com/webhook",
            automation_id=uuid4(),
            run_id=uuid4(),
            status="success",
            automation_type="daily_digest",
            summary={"test": "data"},
            error=None,
        )

        assert mock_post.called
        mock_logger.info.assert_called_once()


async def test_deliver_webhook_retry_on_error() -> None:
    with (
        patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post,
        patch("prodapi.services.webhook.logger") as mock_logger,
    ):
        mock_post.side_effect = httpx.HTTPStatusError(
            "Error", request=None, response=AsyncMock(status_code=500)
        )

        await deliver_webhook(
            webhook_url="https://example.com/webhook",
            automation_id=uuid4(),
            run_id=uuid4(),
            status="failed",
            automation_type="daily_digest",
            summary=None,
            error="Test error",
            max_retries=2,
        )

        assert mock_post.call_count == 2
        mock_logger.error.assert_called_once()


async def test_deliver_webhook_network_error() -> None:
    with (
        patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post,
        patch("prodapi.services.webhook.logger") as mock_logger,
    ):
        mock_post.side_effect = httpx.RequestError("Network error")

        await deliver_webhook(
            webhook_url="https://example.com/webhook",
            automation_id=uuid4(),
            run_id=uuid4(),
            status="failed",
            automation_type="daily_digest",
            summary=None,
            error="Test error",
            max_retries=1,
        )

        assert mock_post.called
        mock_logger.error.assert_called_once()
