from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

uuid_pk = Annotated[UUID, mapped_column(primary_key=True, default=uuid4)]
timestamp = Annotated[
    datetime,
    mapped_column(server_default=func.now(), nullable=False),
]


class Base(DeclarativeBase):
    pass


class UUIDMixin:
    id: Mapped[uuid_pk]


class TimestampMixin:
    created_at: Mapped[timestamp]

    @staticmethod
    def utcnow() -> datetime:
        return datetime.now(UTC)
