from portfolio.services.html_sanitize import (
    build_bubble_footer_github_html,
    build_feedback_consent_html,
    build_hero_bottom_legal_html,
    is_safe_href,
    linkify_phrase,
    sanitize_legal_html,
)


def test_is_safe_href_rejects_javascript() -> None:
    assert not is_safe_href("javascript:alert(1)")
    assert is_safe_href("/main?lang=ru")
    assert is_safe_href("https://example.com")


def test_sanitize_legal_html_strips_script() -> None:
    raw = '<p>Hello</p><script>alert(1)</script><a href="/main">link</a>'
    cleaned = sanitize_legal_html(raw)
    assert "<script>" not in cleaned
    assert 'href="/main"' in cleaned


def test_linkify_phrase_escapes_surrounding_text() -> None:
    html = linkify_phrase(
        'Text <bad> & "quotes"',
        "Text",
        "/privacy?lang=ru",
        css_class="consent__link",
    )
    assert "&lt;bad&gt;" in html
    assert 'href="/privacy?lang=ru"' in html
    assert 'class="consent__link"' in html


def test_build_feedback_consent_html() -> None:
    html = build_feedback_consent_html(
        "Я согласен с политикой.",
        "политикой",
        "/politika-konfidencialnosti?lang=ru",
    )
    assert "<script>" not in html
    assert "политикой" in html


def test_build_bubble_footer_github_html() -> None:
    html = build_bubble_footer_github_html(
        "Вы можете ознакомиться с ними на ",
        "GitHab",
        "https://github.com/example",
    )
    assert 'href="https://github.com/example"' in html
    assert 'class="profession-portfolio-bubbles__footer-link"' in html
    assert 'target="_blank"' in html
    assert 'rel="noopener noreferrer"' in html
    assert "GitHab" in html


def test_build_hero_bottom_legal_html_with_name_and_agreement() -> None:
    html = build_hero_bottom_legal_html(
        "Иван Иванов. Соглашение.",
        "Иван Иванов",
        "/main?lang=ru",
        "Соглашение",
        "/polzovatelskoe-soglashenie?lang=ru",
    )
    assert 'href="/main?lang=ru"' in html
    assert 'href="/polzovatelskoe-soglashenie?lang=ru"' in html
    assert "<script>" not in html
