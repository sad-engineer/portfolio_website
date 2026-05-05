import pytest
from httpx import AsyncClient

from portfolio.main import app


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
                "channels": ["telegram"],
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
