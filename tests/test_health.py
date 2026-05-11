from httpx import ASGITransport, AsyncClient
import pytest

from api.app import create_app


@pytest.mark.asyncio
async def test_health_check() -> None:
    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "JobPilot AI"
