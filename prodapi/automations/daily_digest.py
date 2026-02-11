from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


class DailyDigestConfig(BaseModel):
    webhook_url: HttpUrl
    timezone: str = "UTC"
    title: str = "Daily Digest"
    runs_window_hours: int = Field(default=24, gt=0)
    only_failures: bool = False
    format: Literal["json", "text"] = "json"
    max_items: int = Field(default=50, gt=0)


class DailyDigestExecutor:
    @staticmethod
    def validate_config(config: dict[str, Any]) -> DailyDigestConfig:
        return DailyDigestConfig.model_validate(config)

    @staticmethod
    async def execute(config: dict[str, Any]) -> dict[str, Any]:
        from datetime import UTC, datetime, timedelta

        from sqlalchemy import select

        from prodapi.database import AsyncSessionLocal
        from prodapi.models import Automation, Run, RunStatus

        validated = DailyDigestConfig.model_validate(config)

        now = datetime.now(UTC)
        window_start = now - timedelta(hours=validated.runs_window_hours)

        async with AsyncSessionLocal() as session:
            stmt = (
                select(Run)
                .join(Automation)
                .where(Run.queued_at >= window_start)
                .order_by(Run.queued_at.desc())
            )

            if validated.only_failures:
                stmt = stmt.where(Run.status == RunStatus.FAILED)

            stmt = stmt.limit(validated.max_items)

            result = await session.execute(stmt)
            runs = result.scalars().all()

            total = len(runs)
            success_count = sum(1 for r in runs if r.status == RunStatus.SUCCESS)
            failed_count = sum(1 for r in runs if r.status == RunStatus.FAILED)

            failures = [
                {
                    "run_id": str(r.id),
                    "automation_id": str(r.automation_id),
                    "error": r.error_text or "Unknown error",
                    "queued_at": r.queued_at.isoformat(),
                }
                for r in runs
                if r.status == RunStatus.FAILED
            ]

        return {
            "title": validated.title,
            "period_start": window_start.isoformat(),
            "period_end": now.isoformat(),
            "total_runs": total,
            "success": success_count,
            "failed": failed_count,
            "failures": failures[: validated.max_items],
        }
