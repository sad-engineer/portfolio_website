import pytest
from httpx import AsyncClient

from portfolio.main import app


@pytest.mark.asyncio
async def test_index_returns_ok() -> None:
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert "Resume" in response.text or "портфолио" in response.text.lower()

