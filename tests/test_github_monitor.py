from unittest.mock import AsyncMock, patch

import httpx
import pytest

from prodapi.automations.github_monitor import GitHubMonitorExecutor


def test_github_monitor_validate_config() -> None:
    config = {
        "repo": "owner/repo",
        "webhook_url": "https://example.com/webhook",
        "events": ["issues", "pulls"],
    }
    validated = GitHubMonitorExecutor.validate_config(config)
    assert validated.repo == "owner/repo"
    assert validated.events == ["issues", "pulls"]


def test_github_monitor_validate_config_invalid_event() -> None:
    config = {
        "repo": "owner/repo",
        "webhook_url": "https://example.com/webhook",
        "events": ["invalid_event"],
    }
    with pytest.raises(ValueError, match="Invalid event type"):
        GitHubMonitorExecutor.validate_config(config)


async def test_github_monitor_execute_with_mock() -> None:
    config = {
        "repo": "owner/repo",
        "webhook_url": "https://example.com/webhook",
        "events": ["issues"],
        "state": {},
    }

    mock_response = AsyncMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status = AsyncMock()

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        result = await GitHubMonitorExecutor.execute(config)

        assert result["repo"] == "owner/repo"
        assert "new_items" in result
        assert "counts_by_type" in result


async def test_github_monitor_rate_limit_error() -> None:
    config = {
        "repo": "owner/repo",
        "webhook_url": "https://example.com/webhook",
        "events": ["issues"],
        "state": {},
    }

    mock_response = AsyncMock()
    mock_response.status_code = 403
    mock_error = httpx.HTTPStatusError(
        "Rate limit", request=AsyncMock(), response=mock_response
    )

    with patch("httpx.AsyncClient.get", side_effect=mock_error):
        with pytest.raises(ValueError, match="rate limit"):
            await GitHubMonitorExecutor.execute(config)
