"""Санация HTML перед выводом через |safe в шаблонах."""

from __future__ import annotations

import re
from urllib.parse import urlparse

import bleach
from markupsafe import escape

_UNSAFE_HREF_RE = re.compile(r"^\s*javascript:", re.I)

_LEGAL_ALLOWED_TAGS = ["a", "br", "em", "strong"]
_LEGAL_ALLOWED_ATTRIBUTES = {"a": ["href", "class", "target", "rel"]}

_INLINE_ALLOWED_TAGS = ["a"]
_INLINE_ALLOWED_ATTRIBUTES = {"a": ["href", "class", "rel", "target"]}


def is_safe_href(href: str) -> bool:
    """Проверяет, что href не содержит опасных схем."""
    normalized = href.strip()
    if not normalized or _UNSAFE_HREF_RE.match(normalized):
        return False
    if normalized.startswith("/") and not normalized.startswith("//"):
        return True
    parsed = urlparse(normalized)
    return parsed.scheme in ("http", "https", "mailto", "tel")


def static_asset_url(path: str) -> str:
    """Возвращает URL статического файла (mount /static)."""
    return f"/static/{path.lstrip('/')}"


def _secure_external_links(html: str) -> str:
    """Добавляет rel=\"noopener noreferrer\" к внешним ссылкам с target=\"_blank\"."""

    def _inject_rel(match: re.Match[str]) -> str:
        tag = match.group(0)
        if "rel=" in tag.lower():
            return tag
        return tag[:-1] + ' rel="noopener noreferrer">'

    return re.sub(
        r'<a[^>]*\s+target="_blank"[^>]*>',
        _inject_rel,
        html,
        flags=re.IGNORECASE,
    )


def sanitize_legal_html(html: str) -> str:
    """Санитизирует HTML блоков юридических документов из доверенного JSON."""
    cleaned = bleach.clean(
        html,
        tags=_LEGAL_ALLOWED_TAGS,
        attributes=_LEGAL_ALLOWED_ATTRIBUTES,
        strip=True,
    )
    return _secure_external_links(cleaned)


def sanitize_inline_html(html: str) -> str:
    """Санитизирует короткие HTML-фрагменты (consent, footer)."""
    cleaned = bleach.clean(
        html,
        tags=_INLINE_ALLOWED_TAGS,
        attributes=_INLINE_ALLOWED_ATTRIBUTES,
        strip=True,
    )
    return _secure_external_links(cleaned)


def linkify_phrase(
    text: str,
    phrase: str,
    href: str,
    *,
    css_class: str = "",
    open_in_new_tab: bool = False,
) -> str:
    """Заменяет фразу на безопасную ссылку; остальной текст экранируется."""
    if not phrase or phrase not in text:
        return str(escape(text))
    if not is_safe_href(href):
        return str(escape(text))

    before, _, after = text.partition(phrase)
    class_attr = f' class="{escape(css_class)}"' if css_class else ""
    blank_attr = ""
    if open_in_new_tab and href.strip().lower().startswith("http"):
        blank_attr = ' target="_blank" rel="noopener noreferrer"'
    link = (
        f'<a{class_attr} href="{escape(href)}"{blank_attr}>'
        f"{escape(phrase)}</a>"
    )
    raw_html = f"{escape(before)}{link}{escape(after)}"
    return sanitize_inline_html(raw_html)


def _link_markers(
    text: str,
    phrases: list[tuple[str, str]],
) -> str:
    """Собирает HTML из текста, подставляя безопасные ссылки для указанных фраз."""
    markers: list[tuple[int, int, str]] = []
    for phrase, href in phrases:
        if not phrase or phrase not in text or not is_safe_href(href):
            continue
        start = text.index(phrase)
        markers.append((start, start + len(phrase), href))

    markers.sort(key=lambda item: item[0])
    parts: list[str] = []
    cursor = 0
    for start, end, href in markers:
        if start < cursor:
            continue
        parts.append(str(escape(text[cursor:start])))
        phrase = text[start:end]
        parts.append(f'<a href="{escape(href)}">{escape(phrase)}</a>')
        cursor = end
    parts.append(str(escape(text[cursor:])))
    return sanitize_inline_html("".join(parts))


def build_feedback_consent_html(
    consent_text: str,
    privacy_phrase: str,
    privacy_href: str,
) -> str:
    """Текст согласия формы с кликабельной ссылкой на политику конфиденциальности."""
    return linkify_phrase(
        consent_text,
        privacy_phrase,
        privacy_href,
        css_class="consent__link",
    )


def build_bubble_footer_github_html(
    line_before: str,
    link_label: str,
    github_href: str,
) -> str:
    """Вторая строка подписи пузырькового портфолио со ссылкой на GitHub (GITHUB_URL)."""
    full_text = f"{line_before}{link_label}"
    return linkify_phrase(
        full_text,
        link_label,
        github_href,
        css_class="profession-portfolio-bubbles__footer-link",
        open_in_new_tab=True,
    )


def build_hero_bottom_legal_html(
    legal_text: str,
    full_name: str,
    home_href: str,
    agreement_phrase: str,
    agreement_href: str,
) -> str:
    """Нижний legal-блок с кликабельным именем и ссылкой на пользовательское соглашение."""
    phrases: list[tuple[str, str]] = []
    if full_name:
        phrases.append((full_name, home_href))
    if agreement_phrase and agreement_phrase in legal_text:
        phrases.append((agreement_phrase, agreement_href))

    if phrases:
        html = _link_markers(legal_text, phrases)
    else:
        html = str(escape(legal_text))

    if agreement_phrase and agreement_phrase not in legal_text:
        if is_safe_href(agreement_href):
            separator = "" if legal_text.rstrip().endswith(".") else "."
            tail = (
                f'{separator} <a href="{escape(agreement_href)}">'
                f"{escape(agreement_phrase)}</a>."
            )
            html = sanitize_inline_html(f"{html}{tail}")

    return html
