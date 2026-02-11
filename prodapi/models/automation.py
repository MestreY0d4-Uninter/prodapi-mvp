from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from prodapi.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from prodapi.models.api_key import ApiKey
    from prodapi.models.run import Run
    from prodapi.models.schedule import Schedule


class AutomationType(StrEnum):
    DAILY_DIGEST = "daily_digest"
    GITHUB_MONITOR = "github_monitor"


class Automation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "automations"

    owner_key_id: Mapped[UUID] = mapped_column(
        ForeignKey("api_keys.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    config_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=TimestampMixin.utcnow,
        onupdate=TimestampMixin.utcnow,
        nullable=False,
    )

    owner: Mapped["ApiKey"] = relationship(lazy="joined")
    runs: Mapped[list["Run"]] = relationship(
        back_populates="automation",
        cascade="all, delete-orphan",
    )
    schedule: Mapped["Schedule | None"] = relationship(
        back_populates="automation",
        cascade="all, delete-orphan",
        uselist=False,
    )
