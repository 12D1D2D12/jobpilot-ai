import pytest

from services.resume_service import ResumeService


class FakeCompiledGraph:
    async def ainvoke(self, state):
        assert state["resume_text"] == "Resume with FastAPI experience."
        assert state["jd_text"] == "JD requiring OpenAI and LangGraph."
        return {
            **state,
            "match_score": 74,
            "strengths": ["FastAPI"],
            "missing_skills": ["LangGraph"],
            "resume_suggestions": ["Add OpenAI project metrics"],
            "project_rewrite_suggestions": ["Rewrite project impact"],
            "summary": "Good fit with one missing workflow skill.",
        }


class FakeWorkflow:
    compiled_graph = FakeCompiledGraph()

    def create_initial_state(self, resume_text: str, jd_text: str):
        return {
            "resume_text": resume_text,
            "jd_text": jd_text,
            "extracted_resume_skills": [],
            "jd_required_skills": [],
            "match_score": 0,
            "strengths": [],
            "missing_skills": [],
            "resume_suggestions": [],
            "project_rewrite_suggestions": [],
            "summary": "",
        }

    def to_result(self, state):
        return {
            "match_score": state["match_score"],
            "strengths": state["strengths"],
            "missing_skills": state["missing_skills"],
            "resume_suggestions": state["resume_suggestions"],
            "project_rewrite_suggestions": state["project_rewrite_suggestions"],
            "summary": state["summary"],
        }


class FakeDb:
    def __init__(self) -> None:
        self.records = []
        self.committed = False

    def add(self, record) -> None:
        self.records.append(record)

    def commit(self) -> None:
        self.committed = True


@pytest.mark.asyncio
async def test_resume_service_uses_compiled_graph() -> None:
    db = FakeDb()
    service = ResumeService(db=db, workflow=FakeWorkflow())

    result = await service.optimize_resume(
        resume_text="Resume with FastAPI experience.",
        jd_text="JD requiring OpenAI and LangGraph.",
    )

    assert result.match_score == 74
    assert result.missing_skills == ["LangGraph"]
    assert db.committed is True
    assert len(db.records) == 1
    assert db.records[0].summary == "Good fit with one missing workflow skill."
