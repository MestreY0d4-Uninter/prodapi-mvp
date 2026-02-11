from uuid import UUID

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from prodapi.models import Automation, Schedule, TriggerType
from prodapi.services.runner import enqueue_run


class SchedulerService:
    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown()

    async def restore_schedules(self, session: AsyncSession) -> None:
        stmt = select(Schedule).where(Schedule.enabled == True)  # noqa: E712
        result = await session.execute(stmt)
        schedules = result.scalars().all()

        for schedule in schedules:
            self.add_schedule(
                schedule_id=schedule.id,
                automation_id=schedule.automation_id,
                cron=schedule.cron,
                timezone=schedule.timezone,
            )

    def add_schedule(
        self,
        schedule_id: UUID,
        automation_id: UUID,
        cron: str,
        timezone: str,
    ) -> None:
        job_id = str(schedule_id)

        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        trigger = CronTrigger.from_crontab(cron, timezone=timezone)

        self.scheduler.add_job(
            func=self._trigger_automation,
            trigger=trigger,
            id=job_id,
            kwargs={"automation_id": automation_id},
            replace_existing=True,
        )

    def remove_schedule(self, schedule_id: UUID) -> None:
        job_id = str(schedule_id)
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

    @staticmethod
    async def _trigger_automation(automation_id: UUID) -> None:
        from prodapi.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            stmt = select(Automation).where(Automation.id == automation_id)
            result = await session.execute(stmt)
            automation = result.scalar_one_or_none()

            if automation and automation.enabled:
                await enqueue_run(
                    session=session,
                    automation_id=automation_id,
                    triggered_by=TriggerType.SCHEDULE,
                    trigger_meta={"scheduled": True},
                )


scheduler_service = SchedulerService()
