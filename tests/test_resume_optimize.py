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
        return (
            "{"
            '"match_score": 86,'
            '"strengths": ["FastAPI backend experience", "AI application engineering"],'
            '"missing_skills": ["LangGraph production workflow experience"],'
            '"resume_suggestions": ["Add measurable API performance outcomes"],'
            '"project_rewrite_suggestions": ["Rewrite the AI project around agent workflow ownership"],'
            '"summary": "Strong match with room to clarify agent orchestration experience."'
            "}"
        )

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
    payload = response.json()
    assert payload["match_score"] == 86
    assert "strengths" in payload
    assert "missing_skills" in payload
    assert "resume_suggestions" in payload
    assert "project_rewrite_suggestions" in payload
    assert "summary" in payload


@pytest.mark.asyncio
async def test_resume_optimize_invalid_model_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_optimize_resume(
        self: ResumeOptimizerAgent,
        resume_text: str,
        jd_text: str,
    ) -> str:
        return "not-json"

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

    assert response.status_code == 502
    assert response.json()["detail"] == "Resume optimizer returned invalid JSON."
