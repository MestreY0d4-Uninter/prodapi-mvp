from typing import Any

from prodapi.automations.base import AutomationExecutor
from prodapi.automations.daily_digest import DailyDigestExecutor
from prodapi.automations.github_monitor import GitHubMonitorExecutor
from prodapi.models import AutomationType

REGISTRY: dict[AutomationType, AutomationExecutor] = {
    AutomationType.DAILY_DIGEST: DailyDigestExecutor(),
    AutomationType.GITHUB_MONITOR: GitHubMonitorExecutor(),
}


def validate_automation_config(
    automation_type: AutomationType, config: dict[str, Any]
) -> dict[str, Any]:
    executor = REGISTRY.get(automation_type)
    if executor is None:
        raise ValueError(f"Unknown automation type: {automation_type}")

    validated = executor.validate_config(config)
    return validated.model_dump(mode="json")


__all__ = ["REGISTRY", "validate_automation_config"]
