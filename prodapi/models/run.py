from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import JSON, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from prodapi.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from prodapi.models.automation import Automation


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class TriggerType(StrEnum):
    MANUAL = "manual"
    SCHEDULE = "schedule"


class Run(Base, UUIDMixin):
    __tablename__ = "runs"

    automation_id: Mapped[UUID] = mapped_column(
        ForeignKey("automations.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    queued_at: Mapped[datetime] = mapped_column(
        default=TimestampMixin.utcnow,
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(nullable=True)
    summary_json: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    error_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    triggered_by: Mapped[str] = mapped_column(String(20), nullable=False)
    trigger_meta: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    automation: Mapped["Automation"] = relationship(back_populates="runs")

    __table_args__ = (
        UniqueConstraint(
            "automation_id",
            "idempotency_key",
            name="uq_run_automation_idempotency",
        ),
        Index("ix_runs_automation_id", "automation_id"),
        Index("ix_runs_status", "status"),
        Index("ix_runs_queued_at", "queued_at"),
    )
