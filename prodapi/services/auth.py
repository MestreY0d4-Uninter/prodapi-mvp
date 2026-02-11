import hashlib
import secrets
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from prodapi.models import ApiKey


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


async def create_api_key(session: AsyncSession, label: str) -> tuple[ApiKey, str]:
    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)

    api_key = ApiKey(
        label=label,
        key_hash=key_hash,
    )
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)

    return api_key, raw_key


async def verify_api_key(session: AsyncSession, raw_key: str) -> ApiKey | None:
    key_hash = hash_api_key(raw_key)

    stmt = select(ApiKey).where(
        ApiKey.key_hash == key_hash,
        ApiKey.revoked_at.is_(None),
    )
    result = await session.execute(stmt)
    api_key = result.scalar_one_or_none()

    if api_key:
        api_key.last_used_at = datetime.now(UTC)
        await session.commit()

    return api_key


async def revoke_api_key(session: AsyncSession, key_id: UUID) -> ApiKey | None:
    stmt = select(ApiKey).where(ApiKey.id == key_id)
    result = await session.execute(stmt)
    api_key = result.scalar_one_or_none()

    if api_key and api_key.revoked_at is None:
        api_key.revoked_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(api_key)

    return api_key
