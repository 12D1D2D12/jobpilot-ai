import json
from dataclasses import dataclass, field
from typing import Any

from agents.resume_optimizer_agent import ResumeOptimizerAgent


class ResumeWorkflowError(RuntimeError):
    """Raised when a workflow node returns invalid structured data."""


@dataclass(slots=True)
class ResumeWorkflowState:
    resume_text: str
    jd_text: str
    extracted_resume_skills: list[str] = field(default_factory=list)
    jd_required_skills: list[str] = field(default_factory=list)
    match_score: int = 0
    suggestions: dict[str, Any] = field(default_factory=dict)


class ResumeWorkflow:
    DEFAULT_SUMMARY = "暂未生成总结，请根据结构化建议继续优化简历。"

    def __init__(self, agent: ResumeOptimizerAgent | None = None) -> None:
        self.agent = agent or ResumeOptimizerAgent()

    async def run(self, resume_text: str, jd_text: str) -> dict[str, Any]:
        state = ResumeWorkflowState(resume_text=resume_text, jd_text=jd_text)

        state = await self.extract_resume_skills(state)
        state = await self.analyze_jd_requirements(state)
        state = await self.calculate_match_score(state)
        state = await self.generate_resume_suggestions(state)

        return {
            "match_score": state.match_score,
            "strengths": state.suggestions.get("strengths", []),
            "missing_skills": state.suggestions.get("missing_skills", []),
            "resume_suggestions": state.suggestions.get("resume_suggestions", []),
            "project_rewrite_suggestions": state.suggestions.get(
                "project_rewrite_suggestions",
                [],
            ),
            "summary": state.suggestions.get("summary", ""),
        }

    async def extract_resume_skills(
        self,
        state: ResumeWorkflowState,
    ) -> ResumeWorkflowState:
        payload = await self._call_json_node(
            system_prompt=(
                "Extract skills from the resume. Return only JSON with key "
                "\"extracted_resume_skills\" as an array of concise skill strings."
            ),
            user_prompt=f"Resume:\n{state.resume_text}",
        )
        state.extracted_resume_skills = self._string_list(
            payload,
            "extracted_resume_skills",
        )
        return state

    async def analyze_jd_requirements(
        self,
        state: ResumeWorkflowState,
    ) -> ResumeWorkflowState:
        payload = await self._call_json_node(
            system_prompt=(
                "Extract required skills from the job description. Return only JSON "
                "with key \"jd_required_skills\" as an array of concise skill strings."
            ),
            user_prompt=f"Job Description:\n{state.jd_text}",
        )
        state.jd_required_skills = self._string_list(payload, "jd_required_skills")
        return state

    async def calculate_match_score(
        self,
        state: ResumeWorkflowState,
    ) -> ResumeWorkflowState:
        payload = await self._call_json_node(
            system_prompt=(
                "Calculate a resume-to-JD match score. Return only JSON with key "
                "\"match_score\" as an integer from 0 to 100."
            ),
            user_prompt=(
                f"Resume skills: {state.extracted_resume_skills}\n"
                f"JD required skills: {state.jd_required_skills}"
            ),
        )
        score = payload.get("match_score")
        state.match_score = score if isinstance(score, int) and 0 <= score <= 100 else 0
        return state

    async def generate_resume_suggestions(
        self,
        state: ResumeWorkflowState,
    ) -> ResumeWorkflowState:
        payload = await self._call_json_node(
            system_prompt=(
                "Generate resume optimization output in Chinese. Return only JSON "
                "with keys: strengths, missing_skills, resume_suggestions, "
                "project_rewrite_suggestions, summary. All list fields must be "
                "arrays of strings."
            ),
            user_prompt=(
                f"Resume:\n{state.resume_text}\n\n"
                f"Job Description:\n{state.jd_text}\n\n"
                f"Resume skills: {state.extracted_resume_skills}\n"
                f"JD required skills: {state.jd_required_skills}\n"
                f"Match score: {state.match_score}"
            ),
        )
        state.suggestions = {
            "strengths": self._optional_string_list(payload, "strengths"),
            "missing_skills": self._optional_string_list(payload, "missing_skills"),
            "resume_suggestions": self._optional_string_list(
                payload,
                "resume_suggestions",
            ),
            "project_rewrite_suggestions": self._optional_string_list(
                payload,
                "project_rewrite_suggestions",
            ),
            "summary": self._optional_string_value(
                payload,
                "summary",
                self.DEFAULT_SUMMARY,
            ),
        }
        return state

    async def _call_json_node(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        raw_result = await self.agent.run_json_task(
            system_prompt=(
                f"{system_prompt} Do not return Markdown. Do not use code fences. "
                "Do not add explanatory text."
            ),
            user_prompt=user_prompt,
        )

        try:
            payload = json.loads(raw_result)
        except json.JSONDecodeError as exc:
            raise ResumeWorkflowError("Workflow node returned invalid JSON.") from exc

        if not isinstance(payload, dict):
            raise ResumeWorkflowError("Workflow node JSON must be an object.")

        return payload

    def _string_list(self, payload: dict[str, Any], key: str) -> list[str]:
        value = payload.get(key)
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            raise ResumeWorkflowError(f"Workflow node returned invalid {key}.")
        return value

    def _optional_string_list(self, payload: dict[str, Any], key: str) -> list[str]:
        value = payload.get(key)
        if value is None:
            return []
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, str)]

    def _string_value(self, payload: dict[str, Any], key: str) -> str:
        value = payload.get(key)
        if not isinstance(value, str):
            raise ResumeWorkflowError(f"Workflow node returned invalid {key}.")
        return value

    def _optional_string_value(
        self,
        payload: dict[str, Any],
        key: str,
        default: str,
    ) -> str:
        value = payload.get(key)
        return value if isinstance(value, str) and value.strip() else default
