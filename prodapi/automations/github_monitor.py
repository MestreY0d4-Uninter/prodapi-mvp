from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator


class GitHubMonitorConfig(BaseModel):
    repo: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$")
    events: list[str] = Field(
        default_factory=lambda: ["issues", "pulls", "releases", "commits"]
    )
    github_token: str | None = None
    webhook_url: HttpUrl
    state: dict[str, str] = Field(default_factory=dict)

    @field_validator("events")
    @classmethod
    def validate_events(cls, v: list[str]) -> list[str]:
        allowed = {"issues", "pulls", "releases", "commits"}
        for event in v:
            if event not in allowed:
                raise ValueError(f"Invalid event type: {event}. Allowed: {allowed}")
        return v


class GitHubMonitorExecutor:
    @staticmethod
    def validate_config(config: dict[str, Any]) -> GitHubMonitorConfig:
        return GitHubMonitorConfig.model_validate(config)

    @staticmethod
    async def execute(config: dict[str, Any]) -> dict[str, Any]:
        from datetime import UTC, datetime

        import httpx

        validated = GitHubMonitorConfig.model_validate(config)

        state = validated.state
        new_items: list[dict[str, Any]] = []
        counts_by_type: dict[str, int] = {}

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ProdAPI-GitHubMonitor",
        }
        if validated.github_token:
            headers["Authorization"] = f"token {validated.github_token}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            for event_type in validated.events:
                cursor = state.get(event_type)
                endpoint = GitHubMonitorExecutor._get_endpoint(validated.repo, event_type)

                params = {}
                if cursor:
                    params["since"] = cursor

                try:
                    response = await client.get(
                        endpoint,
                        headers=headers,
                        params=params,
                    )
                    response.raise_for_status()
                    items = response.json()

                    if not isinstance(items, list):
                        items = []

                    for item in items:
                        created_at = item.get("created_at") or item.get("published_at")
                        if created_at:
                            new_items.append(
                                {
                                    "type": event_type,
                                    "title": item.get("title")
                                    or item.get("name")
                                    or item.get("sha", "")[:7],
                                    "url": item.get("html_url") or item.get("url", ""),
                                    "author": (item.get("user") or item.get("author") or {}).get(
                                        "login", "unknown"
                                    ),
                                    "created_at": created_at,
                                }
                            )

                    counts_by_type[event_type] = len(items)

                    if items:
                        latest = max(
                            (
                                item.get("created_at") or item.get("published_at")
                                for item in items
                                if item.get("created_at") or item.get("published_at")
                            ),
                            default=cursor,
                        )
                        if latest:
                            state[event_type] = latest

                except httpx.HTTPStatusError as e:
                    if e.response.status_code in (403, 429):
                        raise ValueError(
                            f"GitHub API rate limit exceeded for {event_type}. "
                            "Consider adding a github_token to your config."
                        ) from e
                    raise ValueError(
                        f"GitHub API error for {event_type}: {e.response.status_code}"
                    ) from e
                except httpx.RequestError as e:
                    raise ValueError(f"GitHub API request failed for {event_type}: {e}") from e

        return {
            "repo": validated.repo,
            "checked_at": datetime.now(UTC).isoformat(),
            "new_items": new_items,
            "counts_by_type": counts_by_type,
            "updated_state": state,
        }

    @staticmethod
    def _get_endpoint(repo: str, event_type: str) -> str:
        base = f"https://api.github.com/repos/{repo}"
        endpoints = {
            "issues": f"{base}/issues",
            "pulls": f"{base}/pulls",
            "releases": f"{base}/releases",
            "commits": f"{base}/commits",
        }
        return endpoints.get(event_type, f"{base}/{event_type}")
