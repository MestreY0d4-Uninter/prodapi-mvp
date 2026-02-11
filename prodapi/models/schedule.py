from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from prodapi.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from prodapi.models.automation import Automation


class Schedule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "schedules"

    automation_id: Mapped[UUID] = mapped_column(
        ForeignKey("automations.id", ondelete="CASCADE"),
        nullable=False,
    )
    cron: Mapped[str] = mapped_column(String(100), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=TimestampMixin.utcnow,
        onupdate=TimestampMixin.utcnow,
        nullable=False,
    )

    automation: Mapped["Automation"] = relationship(back_populates="schedule")

    __table_args__ = (UniqueConstraint("automation_id", name="uq_schedule_automation"),)
