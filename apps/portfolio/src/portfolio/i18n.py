"""Сообщения API и прочие строки с поддержкой локали."""

from __future__ import annotations

from functools import lru_cache

from portfolio.dependencies import get_site_content


@lru_cache
def _feedback_message_tables(section: str) -> tuple[dict, dict]:
    basic = get_site_content().get("basic", {})
    ru_messages = basic.get("feedback", {}).get(section, {})
    en_messages = (
        basic.get("i18n", {})
        .get("en", {})
        .get("feedback", {})
        .get(section, {})
    )
    return (
        ru_messages if isinstance(ru_messages, dict) else {},
        en_messages if isinstance(en_messages, dict) else {},
    )


def _localized_message(section: str, key: str, lang: str, **kwargs: object) -> str:
    ru_messages, en_messages = _feedback_message_tables(section)
    normalized_lang = (lang or "ru").strip().lower() or "ru"
    messages = en_messages if normalized_lang == "en" else ru_messages
    template = messages.get(key) or ru_messages.get(key) or key
    if kwargs:
        return str(template).format(**kwargs)
    return str(template)


def feedback_api_message(key: str, lang: str, **kwargs: object) -> str:
    """Возвращает локализованное сообщение feedback API с fallback на ru."""
    return _localized_message("apiMessages", key, lang, **kwargs)


def feedback_staff_notification(key: str, lang: str, **kwargs: object) -> str:
    """Возвращает локализованную строку уведомления персоналу (email/Telegram)."""
    return _localized_message("staffNotifications", key, lang, **kwargs)


def build_feedback_staff_message(
    *,
    lang: str,
    datetime_utc: str,
    phone: str,
    email: str | None,
    channels: list[str],
    page: str,
) -> str:
    """Собирает тело уведомления о новой заявке для каналов доставки персоналу."""
    user_email = email or feedback_staff_notification("emailNotProvided", lang)
    channels_line = ", ".join(channels)
    lines = [
        feedback_staff_notification("bodyHeader", lang),
        feedback_staff_notification("datetimeLine", lang, datetime=datetime_utc),
        feedback_staff_notification("phoneLine", lang, phone=phone),
        feedback_staff_notification("emailLine", lang, email=user_email),
        feedback_staff_notification(
            "channelsLine", lang, channels=channels_line
        ),
        feedback_staff_notification("pageLine", lang, page=page),
        feedback_staff_notification("langLine", lang, locale=lang),
    ]
    return "\n".join(lines) + "\n"
