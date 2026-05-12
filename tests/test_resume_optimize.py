from collections.abc import Generator

from httpx import ASGITransport, AsyncClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agents.resume_optimizer_agent import ResumeOptimizerAgent
from api.app import create_app
from database.models import ResumeAnalysisRecord
from database.session import Base, get_db


@pytest.fixture
def test_db(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'test_jobpilot.db'}"
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
    )
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    yield override_get_db, testing_session_local

    Base.metadata.drop_all(bind=engine)


@pytest.mark.asyncio
async def test_resume_optimize(
    monkeypatch: pytest.MonkeyPatch,
    test_db,
) -> None:
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

    override_get_db, testing_session_local = test_db
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
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

    with testing_session_local() as db:
        records = db.query(ResumeAnalysisRecord).all()

    assert len(records) == 1
    assert records[0].match_score == 86
    assert records[0].summary == payload["summary"]


@pytest.mark.asyncio
async def test_resume_optimize_invalid_model_json(
    monkeypatch: pytest.MonkeyPatch,
    test_db,
) -> None:
    async def fake_optimize_resume(
        self: ResumeOptimizerAgent,
        resume_text: str,
        jd_text: str,
    ) -> str:
        return "not-json"

    monkeypatch.setattr(ResumeOptimizerAgent, "optimize_resume", fake_optimize_resume)

    override_get_db, _ = test_db
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
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


@pytest.mark.asyncio
async def test_resume_history_returns_latest_records(test_db) -> None:
    override_get_db, testing_session_local = test_db
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with testing_session_local() as db:
        for index in range(25):
            db.add(
                ResumeAnalysisRecord(
                    resume_text=f"Resume {index}",
                    jd_text=f"JD {index}",
                    match_score=index,
                    strengths=["FastAPI"],
                    missing_skills=["LangGraph"],
                    resume_suggestions=["Add metrics"],
                    project_rewrite_suggestions=["Rewrite project impact"],
                    summary=f"Summary {index}",
                )
            )
        db.commit()

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/resume/history")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 20
    assert payload[0]["summary"] == "Summary 24"
