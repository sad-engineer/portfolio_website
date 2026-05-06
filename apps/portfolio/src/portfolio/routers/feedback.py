"""API формы обратной связи: приём и базовая валидация запроса."""

from __future__ import annotations

import asyncio
import json
import re
import smtplib
import time
from collections import deque
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Deque, Dict, List, Literal, Optional
from urllib import error, parse, request

from fastapi import APIRouter, HTTPException, Request, status
from portfolio.dependencies import get_settings
from pydantic import BaseModel, Field, field_validator, model_validator

router = APIRouter(prefix="/api", tags=["feedback"])

ChannelType = Literal["phone", "telegram", "email", "whatsapp", "viber", "call"]
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_feedback_rate_limit_events: Dict[str, Deque[float]] = {}
_feedback_last_request_ts: Dict[str, float] = {}
_feedback_rate_limit_lock = asyncio.Lock()


def _extract_client_ip(request_obj: Request) -> str:
    forwarded_for = request_obj.headers.get("x-forwarded-for", "")
    if forwarded_for:
        first_ip = forwarded_for.split(",", 1)[0].strip()
        if first_ip:
            return first_ip
    if request_obj.client and request_obj.client.host:
        return request_obj.client.host
    return "unknown"


async def _enforce_feedback_rate_limit(request_obj: Request) -> None:
    settings = get_settings()
    max_requests = max(1, settings.feedback_rate_limit_max_requests)
    window_seconds = max(1, settings.feedback_rate_limit_window_seconds)
    min_interval = max(0, settings.feedback_rate_limit_min_interval_seconds)
    client_ip = _extract_client_ip(request_obj)

    # Тестовый клиент FastAPI не должен ломаться из-за глобального in-memory лимитера.
    if client_ip == "testclient":
        return

    now_ts = time.monotonic()
    async with _feedback_rate_limit_lock:
        last_ts = _feedback_last_request_ts.get(client_ip)
        if last_ts is not None and now_ts - last_ts < min_interval:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Слишком частые запросы. Повторите позже.",
            )

        events = _feedback_rate_limit_events.get(client_ip)
        if events is None:
            events = deque()
            _feedback_rate_limit_events[client_ip] = events

        window_start = now_ts - window_seconds
        while events and events[0] < window_start:
            events.popleft()

        if len(events) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Превышен лимит запросов. Повторите позже.",
            )

        events.append(now_ts)
        _feedback_last_request_ts[client_ip] = now_ts


def _verify_turnstile_token_sync(
    *,
    secret_key: str,
    token: str,
    remote_ip: str,
    timeout_seconds: int,
) -> bool:
    payload = {
        "secret": secret_key,
        "response": token,
    }
    if remote_ip and remote_ip != "unknown":
        payload["remoteip"] = remote_ip

    encoded = parse.urlencode(payload).encode("utf-8")
    verify_req = request.Request(
        url="https://challenges.cloudflare.com/turnstile/v0/siteverify",
        data=encoded,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with request.urlopen(verify_req, timeout=max(3, timeout_seconds)) as response:
        verify_payload = json.loads(response.read().decode("utf-8"))
    return bool(verify_payload.get("success"))


def _build_feedback_message(payload: "FeedbackRequest") -> str:
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    channels_line = ", ".join(payload.channels)
    user_email = payload.email or "не указан"
    return (
        "Запрос обратной связи:\n"
        f"Дата/время: {now_utc}\n"
        f"Телефон: {payload.phone}\n"
        f"Email пользователя: {user_email}\n"
        f"Мессенджер/тип связи: {channels_line}\n"
        f"Страница отправки: {payload.page}\n"
        f"Локаль: {payload.lang}\n"
    )


def _send_feedback_email_sync(
    *,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    from_email: str,
    to_email: str,
    body: str,
    timeout_seconds: int,
    security_mode: str,
) -> None:
    message = EmailMessage()
    message["Subject"] = "Новая заявка с формы обратной связи"
    message["From"] = from_email
    message["To"] = to_email
    message.set_content(body)

    timeout = max(5, timeout_seconds)
    normalized_mode = security_mode.strip().lower() if security_mode else "auto"

    def _send_via_ssl(port: int) -> None:
        with smtplib.SMTP_SSL(smtp_host, port, timeout=timeout) as smtp:
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(message, from_addr=smtp_user)

    def _send_via_starttls(port: int) -> None:
        with smtplib.SMTP(smtp_host, port, timeout=timeout) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(message, from_addr=smtp_user)

    if normalized_mode == "ssl":
        _send_via_ssl(smtp_port)
        return
    if normalized_mode == "starttls":
        _send_via_starttls(smtp_port)
        return

    # auto: сначала пробуем SSL с заданным портом, затем fallback на STARTTLS:587.
    try:
        _send_via_ssl(smtp_port)
    except Exception:
        _send_via_starttls(587)


def _send_feedback_telegram_sync(*, bot_token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url=url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=10) as response:
            if response.status >= 400:
                raise RuntimeError(f"Telegram API вернул статус {response.status}")
    except error.HTTPError as exc:
        raise RuntimeError(f"Telegram API HTTPError: {exc.code}") from exc
    except error.URLError as exc:
        raise RuntimeError("Не удалось подключиться к Telegram API") from exc


async def _run_with_retry(coro_factory, retries: int, delay_ms: int) -> None:
    attempts = max(1, retries)
    last_error: Optional[Exception] = None
    for attempt in range(attempts):
        try:
            await coro_factory()
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt + 1 >= attempts:
                break
            await asyncio.sleep(max(0, delay_ms) / 1000)
    if last_error is not None:
        raise last_error


class FeedbackRequest(BaseModel):
    """Тело запроса для отправки заявки формы обратной связи."""

    phone: str = Field(min_length=1, max_length=64)
    email: Optional[str] = Field(default=None, max_length=254)
    fullname: Optional[str] = Field(default=None, max_length=254)
    turnstile_token: Optional[str] = Field(default=None, max_length=4096)
    channels: List[ChannelType]
    consent: bool
    page: str = Field(min_length=1, max_length=300)
    lang: str = Field(default="ru", min_length=2, max_length=5)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Телефон обязателен.")
        digits = "".join(ch for ch in normalized if ch.isdigit())
        if len(digits) < 8:
            raise ValueError("Телефон имеет некорректный формат.")
        return normalized

    @field_validator("channels")
    @classmethod
    def validate_channels(cls, value: List[ChannelType]) -> List[ChannelType]:
        if not value:
            raise ValueError("Выберите хотя бы один канал связи.")
        # Убираем дубли, сохраняя порядок.
        unique_channels: List[ChannelType] = []
        for channel in value:
            if channel not in unique_channels:
                unique_channels.append(channel)
        return unique_channels

    @field_validator("lang")
    @classmethod
    def validate_lang(cls, value: str) -> str:
        normalized = value.strip().lower()
        return normalized or "ru"

    @model_validator(mode="after")
    def validate_cross_fields(self) -> "FeedbackRequest":
        if not self.consent:
            raise ValueError("Необходимо согласие на обработку данных.")

        if "email" in self.channels:
            if not self.email or not self.email.strip():
                raise ValueError("Email обязателен, если выбран канал email.")
            if not _EMAIL_RE.match(self.email.strip()):
                raise ValueError("Email имеет некорректный формат.")
            self.email = self.email.strip()
        elif self.email:
            self.email = self.email.strip()

        if self.fullname:
            self.fullname = self.fullname.strip()
        if self.turnstile_token:
            self.turnstile_token = self.turnstile_token.strip()

        self.page = self.page.strip()
        return self


@router.post("/feedback")
async def post_feedback(
    payload: FeedbackRequest, request_obj: Request
) -> dict[str, str]:
    """Принимает заявку, валидирует и отправляет уведомления в каналы."""
    if not payload.page:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Поле page обязательно.",
        )

    await _enforce_feedback_rate_limit(request_obj)

    # Honeypot: если скрытое поле заполнено, считаем запрос ботом и ничего не доставляем.
    if payload.fullname:
        return {
            "status": "accepted",
            "message": "Заявка принята.",
            "delivery_channels": "",
            "skipped_channels": "",
        }

    settings = get_settings()
    if settings.feedback_turnstile_secret_key:
        if not payload.turnstile_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Проверка anti-bot не пройдена. Обновите страницу и повторите.",
            )
        try:
            is_valid_turnstile = await asyncio.to_thread(
                _verify_turnstile_token_sync,
                secret_key=settings.feedback_turnstile_secret_key,
                token=payload.turnstile_token,
                remote_ip=_extract_client_ip(request_obj),
                timeout_seconds=settings.feedback_turnstile_timeout_seconds,
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Ошибка проверки anti-bot: {exc}",
            ) from exc
        if not is_valid_turnstile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Проверка anti-bot не пройдена. Обновите страницу и повторите.",
            )
    message = _build_feedback_message(payload)
    delivered: List[str] = []
    skipped: List[str] = []

    smtp_ready = all(
        [
            settings.feedback_smtp_host,
            settings.feedback_smtp_user,
            settings.feedback_smtp_password,
        ]
    )
    if not smtp_ready:
        skipped.append("email")
    else:
        from_email = settings.feedback_smtp_user
        to_email = settings.feedback_smtp_to or settings.feedback_smtp_user

        async def _send_email() -> None:
            await asyncio.to_thread(
                _send_feedback_email_sync,
                smtp_host=settings.feedback_smtp_host,
                smtp_port=settings.feedback_smtp_port,
                smtp_user=settings.feedback_smtp_user,
                smtp_password=settings.feedback_smtp_password,
                from_email=from_email,
                to_email=to_email,
                body=message,
                timeout_seconds=settings.feedback_smtp_timeout_seconds,
                security_mode=settings.feedback_smtp_security,
            )

        try:
            await _run_with_retry(
                _send_email,
                retries=settings.feedback_delivery_retries,
                delay_ms=settings.feedback_delivery_retry_delay_ms,
            )
            delivered.append("email")
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Не удалось отправить заявку в email: {exc}",
            ) from exc

    if "telegram" in payload.channels:
        telegram_ready = bool(settings.feedback_telegram_bot_token) and bool(
            settings.feedback_telegram_chat_id
        )
        if not telegram_ready:
            skipped.append("telegram")
        else:

            async def _send_telegram() -> None:
                await asyncio.to_thread(
                    _send_feedback_telegram_sync,
                    bot_token=settings.feedback_telegram_bot_token,
                    chat_id=settings.feedback_telegram_chat_id,
                    text=message,
                )

            try:
                await _run_with_retry(
                    _send_telegram,
                    retries=settings.feedback_delivery_retries,
                    delay_ms=settings.feedback_delivery_retry_delay_ms,
                )
                delivered.append("telegram")
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Не удалось отправить заявку в telegram: {exc}",
                ) from exc

    delivery_state = "delivered" if delivered else "accepted"
    if skipped and not delivered:
        delivery_state = "accepted_without_delivery_config"

    return {
        "status": delivery_state,
        "message": "Заявка принята.",
        "delivery_channels": ", ".join(delivered) if delivered else "",
        "skipped_channels": ", ".join(skipped) if skipped else "",
    }
