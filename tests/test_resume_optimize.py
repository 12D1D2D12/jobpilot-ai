from datetime import UTC, datetime

from httpx import ASGITransport, AsyncClient
import pytest

from api.app import create_app
from api.routes.resume import get_resume_service
from services.resume_service import ResumeAnalysisHistoryItem, ResumeOptimizeResult


class MockResumeService:
    async def optimize_resume(
        self,
        resume_text: str,
        jd_text: str,
    ) -> ResumeOptimizeResult:
        assert "FastAPI" in resume_text
        assert "OpenAI" in jd_text
        return ResumeOptimizeResult(
            match_score=86,
            strengths=["FastAPI backend experience", "AI application engineering"],
            missing_skills=["LangGraph production workflow experience"],
            resume_suggestions=["Add measurable API performance outcomes"],
            project_rewrite_suggestions=[
                "Rewrite the AI project around agent workflow ownership"
            ],
            summary="Strong match with room to clarify agent orchestration experience.",
        )

    async def get_history(self, limit: int = 20) -> list[ResumeAnalysisHistoryItem]:
        assert limit == 20
        return [
            ResumeAnalysisHistoryItem(
                id=1,
                resume_text="Candidate has FastAPI backend development experience.",
                jd_text="The role requires OpenAI SDK experience.",
                match_score=86,
                strengths=["FastAPI"],
                missing_skills=["LangGraph"],
                resume_suggestions=["Add metrics"],
                project_rewrite_suggestions=["Rewrite project impact"],
                summary="Strong match.",
                created_at=datetime.now(UTC),
            )
        ]


@pytest.fixture
def app():
    app = create_app()
    app.dependency_overrides[get_resume_service] = lambda: MockResumeService()
    yield app
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_resume_optimize(app) -> None:
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
async def test_resume_history(app) -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/resume/history")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["summary"] == "Strong match."
    assert payload[0]["match_score"] == 86
