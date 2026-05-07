"""Хранилище заявок обратной связи в PostgreSQL (SQLAlchemy)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from portfolio.dependencies import get_settings
from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, MetaData, String, Table
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

metadata = MetaData()
feedback_requests_table = Table(
    "feedback_requests",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("phone_raw", String(64), nullable=False),
    Column("phone_e164", String(32), nullable=False),
    Column("email", String(254), nullable=True),
    Column("channels", JSON, nullable=False),
    Column("consent", Boolean, nullable=False),
    Column("page", String(300), nullable=False),
    Column("lang", String(5), nullable=False),
    Column("source_ip", String(128), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

_feedback_engine: Optional[AsyncEngine] = None


def _database_url() -> str:
    return get_settings().feedback_database_url.strip()


def _async_database_url(raw_url: str) -> str:
    if raw_url.startswith("postgresql+asyncpg://"):
        return raw_url
    if raw_url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + raw_url[len("postgresql://") :]
    return raw_url


def _get_engine() -> Optional[AsyncEngine]:
    global _feedback_engine
    db_url = _database_url()
    if not db_url:
        return None
    if _feedback_engine is None:
        _feedback_engine = create_async_engine(
            _async_database_url(db_url),
            future=True,
            pool_pre_ping=True,
        )
    return _feedback_engine


def is_feedback_db_enabled() -> bool:
    return bool(_database_url())


async def init_feedback_db() -> None:
    engine = _get_engine()
    if engine is None:
        return
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)


async def save_feedback_request(
    *,
    phone_raw: str,
    phone_e164: str,
    email: Optional[str],
    channels: list[str],
    consent: bool,
    page: str,
    lang: str,
    source_ip: str,
) -> None:
    engine = _get_engine()
    if engine is None:
        return
    payload = {
        "phone_raw": phone_raw,
        "phone_e164": phone_e164,
        "email": email,
        "channels": channels,
        "consent": consent,
        "page": page,
        "lang": lang,
        "source_ip": source_ip,
        "created_at": datetime.now(timezone.utc),
    }
    async with engine.begin() as conn:
        await conn.execute(feedback_requests_table.insert().values(**payload))
