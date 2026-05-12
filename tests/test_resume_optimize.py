from httpx import ASGITransport, AsyncClient
import pytest

from agents.resume_optimizer_agent import ResumeOptimizerAgent
from api.app import create_app


@pytest.mark.asyncio
async def test_resume_optimize(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_optimize_resume(
        self: ResumeOptimizerAgent,
        resume_text: str,
        jd_text: str,
    ) -> str:
        assert "FastAPI" in resume_text
        assert "OpenAI" in jd_text
        return "Resume Match Analysis: good fit\nPriority Optimization Advice: highlight FastAPI and OpenAI Agent projects"

    monkeypatch.setattr(ResumeOptimizerAgent, "optimize_resume", fake_optimize_resume)

    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/resume/optimize",
            json={
                "resume_text": (
                    "Candidate has FastAPI backend development experience "
                    "and worked on AI application engineering."
                ),
                "jd_text": (
                    "The role requires Python, OpenAI SDK, agent workflows, "
                    "and API service development."
                ),
            },
        )

    assert response.status_code == 200
    assert "Priority Optimization Advice" in response.json()["result"]
