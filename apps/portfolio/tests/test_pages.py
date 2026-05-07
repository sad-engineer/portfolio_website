import pytest
from httpx import AsyncClient
from portfolio.dependencies import get_settings
from portfolio.main import app


@pytest.fixture(autouse=True)
def isolate_feedback_delivery_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FEEDBACK_SMTP_HOST", "")
    monkeypatch.setenv("FEEDBACK_SMTP_USER", "")
    monkeypatch.setenv("FEEDBACK_SMTP_PASSWORD", "")
    monkeypatch.setenv("FEEDBACK_SMTP_TO", "")
    monkeypatch.setenv("FEEDBACK_TELEGRAM_BOT_TOKEN", "")
    monkeypatch.setenv("FEEDBACK_TELEGRAM_CHAT_ID", "")
    monkeypatch.setenv("FEEDBACK_TURNSTILE_SITE_KEY", "")
    monkeypatch.setenv("FEEDBACK_TURNSTILE_SECRET_KEY", "")
    monkeypatch.setenv("FEEDBACK_RATE_LIMIT_MAX_REQUESTS", "1000")
    monkeypatch.setenv("FEEDBACK_RATE_LIMIT_MIN_INTERVAL_SECONDS", "0")
    monkeypatch.setenv("FEEDBACK_DATABASE_URL", "")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_index_returns_ok() -> None:
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert "Выберите направление, в котором я вам интересен" in response.text
    assert "Инженер-конструктор" in response.text


@pytest.mark.asyncio
async def test_feedback_post_success() -> None:
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.post(
            "/api/feedback",
            json={
                "phone": "+7 (912) 345-67-89",
                "channels": ["call"],
                "consent": True,
                "page": "/main",
                "lang": "ru",
            },
        )

    assert response.status_code == 200
    assert response.json()["status"] in {
        "delivered",
        "accepted",
        "accepted_without_delivery_config",
    }


@pytest.mark.asyncio
async def test_feedback_requires_consent() -> None:
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.post(
            "/api/feedback",
            json={
                "phone": "+7 (912) 345-67-89",
                "channels": ["telegram"],
                "consent": False,
                "page": "/main",
                "lang": "ru",
            },
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_feedback_requires_channels() -> None:
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.post(
            "/api/feedback",
            json={
                "phone": "+7 (912) 345-67-89",
                "channels": [],
                "consent": True,
                "page": "/main",
                "lang": "ru",
            },
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_feedback_email_required_if_channel_email_selected() -> None:
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.post(
            "/api/feedback",
            json={
                "phone": "+7 (912) 345-67-89",
                "channels": ["email"],
                "consent": True,
                "page": "/main",
                "lang": "ru",
            },
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_feedback_rejects_monotonic_phone_pattern() -> None:
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.post(
            "/api/feedback",
            json={
                "phone": "12345678",
                "channels": ["call"],
                "consent": True,
                "page": "/main",
                "lang": "ru",
            },
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_feedback_accepts_local_ru_phone_and_normalizes() -> None:
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.post(
            "/api/feedback",
            json={
                "phone": "8 (912) 345-67-89",
                "channels": ["call"],
                "consent": True,
                "page": "/main",
                "lang": "ru",
            },
        )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_feedback_requires_turnstile_token_when_secret_is_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FEEDBACK_TURNSTILE_SECRET_KEY", "test-secret")
    get_settings.cache_clear()
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.post(
            "/api/feedback",
            json={
                "phone": "+7 (912) 345-67-89",
                "channels": ["call"],
                "consent": True,
                "page": "/main",
                "lang": "ru",
            },
        )

    assert response.status_code == 403
