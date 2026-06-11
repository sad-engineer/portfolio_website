"""Хранилище заявок обратной связи в PostgreSQL (SQLAlchemy)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

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
_logger = logging.getLogger(__name__)


def _database_url() -> str:
    return get_settings().feedback_database_url.strip()


def _async_database_url(raw_url: str) -> str:
    if raw_url.startswith("postgresql+asyncpg://"):
        return raw_url
    if raw_url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + raw_url[len("postgresql://") :]
    return raw_url


def _strip_ssl_query_params(raw_url: str) -> tuple[str, Optional[str]]:
    """Убирает ssl/sslmode из query string — asyncpg получает SSL через connect_args."""
    parsed = urlparse(raw_url)
    if not parsed.query:
        return raw_url, None

    query = parse_qs(parsed.query, keep_blank_values=True)
    ssl_mode: Optional[str] = None
    for key in ("sslmode", "ssl"):
        values = query.pop(key, None)
        if values and values[0]:
            ssl_mode = values[0].strip().lower()

    flattened_query = []
    for key, values in query.items():
        for value in values:
            flattened_query.append((key, value))
    clean_query = urlencode(flattened_query)
    clean_url = urlunparse(parsed._replace(query=clean_query))
    return clean_url, ssl_mode


def _resolve_ssl_mode(url_ssl_mode: Optional[str], raw_url: str) -> Optional[str]:
    configured = get_settings().feedback_database_ssl.strip().lower()
    if configured:
        return configured
    if url_ssl_mode:
        return url_ssl_mode
    hostname = (urlparse(raw_url).hostname or "").strip().lower()
    if hostname and hostname not in {"localhost", "127.0.0.1", "::1"}:
        return "require"
    return None


def _asyncpg_connect_args(ssl_mode: Optional[str]) -> dict:
    if not ssl_mode:
        return {}
    if ssl_mode in {"disable", "false", "0", "off"}:
        return {"ssl": False}
    if ssl_mode in {
        "require",
        "prefer",
        "true",
        "1",
        "on",
        "verify-ca",
        "verify-full",
    }:
        return {"ssl": True}
    return {"ssl": True}


def _get_engine() -> Optional[AsyncEngine]:
    global _feedback_engine
    db_url = _database_url()
    if not db_url:
        return None
    if _feedback_engine is None:
        clean_url, url_ssl_mode = _strip_ssl_query_params(db_url)
        ssl_mode = _resolve_ssl_mode(url_ssl_mode, clean_url)
        connect_args = _asyncpg_connect_args(ssl_mode)
        _feedback_engine = create_async_engine(
            _async_database_url(clean_url),
            future=True,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
    return _feedback_engine


def is_feedback_db_enabled() -> bool:
    return bool(_database_url())


async def init_feedback_db() -> None:
    engine = _get_engine()
    if engine is None:
        return
    try:
        async with engine.begin() as conn:
            await conn.run_sync(metadata.create_all)
    except Exception as exc:
        if get_settings().debug:
            _logger.warning(
                "Feedback DB init skipped (%s). "
                "For cloud PostgreSQL set FEEDBACK_DATABASE_SSL=require "
                "or add ?sslmode=require to FEEDBACK_DATABASE_URL.",
                exc,
            )
            return
        raise


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
