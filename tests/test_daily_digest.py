from prodapi.automations.daily_digest import DailyDigestExecutor


def test_daily_digest_validate_config() -> None:
    config = {"webhook_url": "https://example.com/webhook"}
    validated = DailyDigestExecutor.validate_config(config)
    assert validated.webhook_url is not None
    assert validated.timezone == "UTC"
    assert validated.runs_window_hours == 24


async def test_daily_digest_execute() -> None:
    config = {
        "webhook_url": "https://example.com/webhook",
        "timezone": "UTC",
        "runs_window_hours": 24,
    }
    result = await DailyDigestExecutor.execute(config)

    assert "title" in result
    assert "total_runs" in result
    assert "success" in result
    assert "failed" in result
    assert "failures" in result
