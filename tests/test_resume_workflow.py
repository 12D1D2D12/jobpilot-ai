import pytest

from workflow.resume_workflow import ResumeWorkflow


class FakeMemoryManager:
    def __init__(self) -> None:
        self.requested_user_ids: list[str] = []

    def get_memory_context(self, user_id: str) -> str:
        self.requested_user_ids.append(user_id)
        return "Previous memory: user already added Docker; Redis remains missing."


class FakeResumeAgent:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def run_json_task(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append(system_prompt)
        if "Generate resume optimization output" in system_prompt:
            assert "Docker" in user_prompt
            assert "Redis" in user_prompt
        if "extracted_resume_skills" in system_prompt:
            return '{"extracted_resume_skills": ["FastAPI", "OpenAI"]}'
        if "jd_required_skills" in system_prompt:
            return '{"jd_required_skills": ["FastAPI", "LangGraph", "OpenAI"]}'
        if "match_score" in system_prompt:
            return '{"match_score": 82}'
        if "application_recommendation" in system_prompt:
            return '{"application_recommendation": "Recommended to apply."}'
        if "learning_plan" in system_prompt:
            return '{"learning_plan": ["Learn LangGraph", "Build an agent project"]}'
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
    agent = FakeResumeAgent()
    memory_manager = FakeMemoryManager()
    workflow = ResumeWorkflow(agent=agent, memory_manager=memory_manager)

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
        "Strong match, with room to strengthen LangGraph experience.\n\n"
        "Application recommendation: Recommended to apply."
    )
    assert any("application_recommendation" in call for call in agent.calls)
    assert not any("learning_plan" in call for call in agent.calls)
    assert memory_manager.requested_user_ids == ["default_user"]


class MissingSummaryAgent:
    async def run_json_task(self, system_prompt: str, user_prompt: str) -> str:
        if "extracted_resume_skills" in system_prompt:
            return '{"extracted_resume_skills": ["FastAPI"]}'
        if "jd_required_skills" in system_prompt:
            return '{"jd_required_skills": ["FastAPI", "LangGraph"]}'
        if "match_score" in system_prompt:
            return '{"match_score": "high"}'
        if "learning_plan" in system_prompt:
            return '{"learning_plan": ["Learn LangGraph basics", "Build workflow project"]}'
        if "application_recommendation" in system_prompt:
            return '{"application_recommendation": "Apply now."}'
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
    assert result["summary"] == (
        f"{ResumeWorkflow.DEFAULT_SUMMARY}\n\n"
        "Learning plan: Learn LangGraph basics; Build workflow project"
    )


class LowScoreRoutingAgent:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def run_json_task(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append(system_prompt)
        if "extracted_resume_skills" in system_prompt:
            return '{"extracted_resume_skills": ["Python"]}'
        if "jd_required_skills" in system_prompt:
            return '{"jd_required_skills": ["Python", "FastAPI", "LangGraph"]}'
        if "match_score" in system_prompt:
            return '{"match_score": 64}'
        if "learning_plan" in system_prompt:
            return '{"learning_plan": ["Build FastAPI project", "Learn LangGraph StateGraph"]}'
        return (
            "{"
            '"strengths": ["Python foundation matches"],'
            '"missing_skills": ["FastAPI", "LangGraph"],'
            '"resume_suggestions": ["Add backend API project"],'
            '"project_rewrite_suggestions": [],'
            '"summary": "Current match is low; build core project experience first."'
            "}"
        )


@pytest.mark.asyncio
async def test_resume_workflow_low_score_routes_to_learning_plan() -> None:
    agent = LowScoreRoutingAgent()
    workflow = ResumeWorkflow(agent=agent)

    result = await workflow.run(
        resume_text="Python project experience.",
        jd_text="Requires Python, FastAPI, and LangGraph.",
    )

    assert result["match_score"] == 64
    assert "Learning plan" in result["summary"]
    assert any("learning_plan" in call for call in agent.calls)
    assert not any("application_recommendation" in call for call in agent.calls)


class HighScoreRoutingAgent:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def run_json_task(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append(system_prompt)
        if "extracted_resume_skills" in system_prompt:
            return '{"extracted_resume_skills": ["Python", "FastAPI", "OpenAI"]}'
        if "jd_required_skills" in system_prompt:
            return '{"jd_required_skills": ["Python", "FastAPI", "OpenAI"]}'
        if "match_score" in system_prompt:
            return '{"match_score": 91}'
        if "application_recommendation" in system_prompt:
            return '{"application_recommendation": "Strongly recommended to apply."}'
        return (
            "{"
            '"strengths": ["Core skills strongly match"],'
            '"missing_skills": [],'
            '"resume_suggestions": ["Highlight measurable outcomes"],'
            '"project_rewrite_suggestions": ["Emphasize AI service delivery"],'
            '"summary": "High match; prepare to apply."'
            "}"
        )


@pytest.mark.asyncio
async def test_resume_workflow_high_score_routes_to_application_recommendation() -> None:
    agent = HighScoreRoutingAgent()
    workflow = ResumeWorkflow(agent=agent)

    result = await workflow.run(
        resume_text="Python, FastAPI, and OpenAI project experience.",
        jd_text="Requires Python, FastAPI, and OpenAI.",
    )

    assert result["match_score"] == 91
    assert "Application recommendation" in result["summary"]
    assert any("application_recommendation" in call for call in agent.calls)
    assert not any("learning_plan" in call for call in agent.calls)
