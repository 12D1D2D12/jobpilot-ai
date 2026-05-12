from httpx import ASGITransport, AsyncClient
import pytest

from agents.job_search_agent import JobSearchAgent
from api.app import create_app


@pytest.mark.asyncio
async def test_job_analyze(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_analyze_jd(self: JobSearchAgent, jd_text: str) -> str:
        assert "FastAPI" in jd_text
        return "Job Summary: Backend AI Engineer\nCore Skills: FastAPI, OpenAI\nLearning Advice: Practice agent engineering"

    monkeypatch.setattr(JobSearchAgent, "analyze_jd", fake_analyze_jd)

    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/job/analyze",
            json={
                "jd_text": (
                    "FastAPI AI Engineer role responsible for OpenAI Agent "
                    "application development and workflow automation."
                )
            },
        )

    assert response.status_code == 200
    assert "Core Skills" in response.json()["result"]
