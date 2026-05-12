import pytest

from workflow.resume_workflow import ResumeWorkflow


class FakeResumeAgent:
    async def run_json_task(self, system_prompt: str, user_prompt: str) -> str:
        if "extracted_resume_skills" in system_prompt:
            return '{"extracted_resume_skills": ["FastAPI", "OpenAI"]}'
        if "jd_required_skills" in system_prompt:
            return '{"jd_required_skills": ["FastAPI", "LangGraph", "OpenAI"]}'
        if "match_score" in system_prompt:
            return '{"match_score": 82}'
        return (
            "{"
            '"strengths": ["FastAPI and OpenAI experience match"],'
            '"missing_skills": ["LangGraph"],'
            '"resume_suggestions": ["Add agent workflow experience"],'
            '"project_rewrite_suggestions": ["Highlight end-to-end AI delivery"],'
            '"summary": "Strong match, with room to strengthen LangGraph experience."'
            "}"
        )


@pytest.mark.asyncio
async def test_resume_workflow_runs_all_nodes() -> None:
    workflow = ResumeWorkflow(agent=FakeResumeAgent())

    result = await workflow.run(
        resume_text="Built FastAPI services with OpenAI integrations.",
        jd_text="Requires FastAPI, OpenAI, and LangGraph experience.",
    )

    assert result["match_score"] == 82
    assert result["strengths"] == ["FastAPI and OpenAI experience match"]
    assert result["missing_skills"] == ["LangGraph"]
    assert result["resume_suggestions"] == ["Add agent workflow experience"]
    assert result["project_rewrite_suggestions"] == ["Highlight end-to-end AI delivery"]
    assert result["summary"] == (
        "Strong match, with room to strengthen LangGraph experience."
    )


class MissingSummaryAgent:
    async def run_json_task(self, system_prompt: str, user_prompt: str) -> str:
        if "extracted_resume_skills" in system_prompt:
            return '{"extracted_resume_skills": ["FastAPI"]}'
        if "jd_required_skills" in system_prompt:
            return '{"jd_required_skills": ["FastAPI", "LangGraph"]}'
        if "match_score" in system_prompt:
            return '{"match_score": "high"}'
        return (
            "{"
            '"strengths": ["FastAPI experience"],'
            '"resume_suggestions": ["Add workflow details"]'
            "}"
        )


@pytest.mark.asyncio
async def test_resume_workflow_falls_back_when_summary_missing() -> None:
    workflow = ResumeWorkflow(agent=MissingSummaryAgent())

    result = await workflow.run(
        resume_text="Built FastAPI services.",
        jd_text="Requires FastAPI and LangGraph.",
    )

    assert result["match_score"] == 0
    assert result["strengths"] == ["FastAPI experience"]
    assert result["missing_skills"] == []
    assert result["resume_suggestions"] == ["Add workflow details"]
    assert result["project_rewrite_suggestions"] == []
    assert result["summary"] == ResumeWorkflow.DEFAULT_SUMMARY
