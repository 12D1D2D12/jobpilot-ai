import json
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from agents.resume_optimizer_agent import ResumeOptimizerAgent
from memory.resume_memory import ResumeMemoryManager
from services.logger import get_logger


logger = get_logger(__name__)


class ResumeWorkflowError(RuntimeError):
    """Raised when a workflow node returns invalid structured data."""


class ResumeWorkflowState(TypedDict):
    user_id: str
    resume_text: str
    jd_text: str
    memory_context: str
    extracted_resume_skills: list[str]
    jd_required_skills: list[str]
    match_score: int
    strengths: list[str]
    missing_skills: list[str]
    resume_suggestions: list[str]
    project_rewrite_suggestions: list[str]
    summary: str
    learning_plan: list[str]
    application_recommendation: str


class ResumeWorkflow:
    DEFAULT_SUMMARY = "\u6682\u672a\u751f\u6210\u603b\u7ed3\uff0c\u8bf7\u6839\u636e\u7ed3\u6784\u5316\u5efa\u8bae\u7ee7\u7eed\u4f18\u5316\u7b80\u5386\u3002"

    def __init__(
        self,
        agent: ResumeOptimizerAgent | None = None,
        memory_manager: ResumeMemoryManager | None = None,
    ) -> None:
        self.agent = agent or ResumeOptimizerAgent()
        self.memory_manager = memory_manager or ResumeMemoryManager()
        self.compiled_graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(ResumeWorkflowState)

        graph.add_node("load_memory_context", self.load_memory_context)
        graph.add_node("extract_resume_skills", self.extract_resume_skills)
        graph.add_node("analyze_jd_requirements", self.analyze_jd_requirements)
        graph.add_node("calculate_match_score", self.calculate_match_score)
        graph.add_node("generate_learning_plan", self.generate_learning_plan)
        graph.add_node("recommend_application", self.recommend_application)
        graph.add_node("generate_resume_suggestions", self.generate_resume_suggestions)

        graph.add_edge(START, "load_memory_context")
        graph.add_edge("load_memory_context", "extract_resume_skills")
        graph.add_edge("extract_resume_skills", "analyze_jd_requirements")
        graph.add_edge("analyze_jd_requirements", "calculate_match_score")
        graph.add_conditional_edges(
            "calculate_match_score",
            self.route_after_match_score,
            {
                "generate_learning_plan": "generate_learning_plan",
                "recommend_application": "recommend_application",
            },
        )
        graph.add_edge("generate_learning_plan", "generate_resume_suggestions")
        graph.add_edge("recommend_application", "generate_resume_suggestions")
        graph.add_edge("generate_resume_suggestions", END)

        return graph.compile()

    def create_initial_state(
        self,
        resume_text: str,
        jd_text: str,
        user_id: str = "default_user",
    ) -> ResumeWorkflowState:
        return {
            "user_id": user_id,
            "resume_text": resume_text,
            "jd_text": jd_text,
            "memory_context": "",
            "extracted_resume_skills": [],
            "jd_required_skills": [],
            "match_score": 0,
            "strengths": [],
            "missing_skills": [],
            "resume_suggestions": [],
            "project_rewrite_suggestions": [],
            "summary": self.DEFAULT_SUMMARY,
            "learning_plan": [],
            "application_recommendation": "",
        }

    async def run(
        self,
        resume_text: str,
        jd_text: str,
        user_id: str = "default_user",
    ) -> dict[str, Any]:
        final_state = await self.compiled_graph.ainvoke(
            self.create_initial_state(
                resume_text=resume_text,
                jd_text=jd_text,
                user_id=user_id,
            )
        )
        return self.to_result(final_state)

    def to_result(self, state: ResumeWorkflowState | dict[str, Any]) -> dict[str, Any]:
        return {
            "match_score": state.get("match_score", 0),
            "strengths": state.get("strengths", []),
            "missing_skills": state.get("missing_skills", []),
            "resume_suggestions": state.get("resume_suggestions", []),
            "project_rewrite_suggestions": state.get(
                "project_rewrite_suggestions",
                [],
            ),
            "summary": state.get("summary", self.DEFAULT_SUMMARY),
        }

    async def load_memory_context(
        self,
        state: ResumeWorkflowState,
    ) -> dict[str, str]:
        logger.info("Workflow node start node=load_memory_context user_id=%s", state["user_id"])
        memory_context = self.memory_manager.get_memory_context(user_id=state["user_id"])
        logger.info(
            "Workflow memory loaded user_id=%s has_memory=%s memory_len=%s",
            state["user_id"],
            bool(memory_context),
            len(memory_context),
        )
        return {
            "memory_context": memory_context
        }

    async def extract_resume_skills(
        self,
        state: ResumeWorkflowState,
    ) -> dict[str, list[str]]:
        logger.info(
            "Workflow node start node=extract_resume_skills resume_len=%s resume_preview=%r",
            len(state["resume_text"]),
            state["resume_text"][:50],
        )
        payload = await self._call_json_node(
            system_prompt=(
                "Extract skills from the resume. Return only JSON with key "
                "\"extracted_resume_skills\" as an array of concise skill strings."
            ),
            user_prompt=f"Resume:\n{state['resume_text']}",
        )
        skills = self._optional_string_list(
            payload,
            "extracted_resume_skills",
        )
        logger.info("Workflow node complete node=extract_resume_skills skill_count=%s", len(skills))
        return {
            "extracted_resume_skills": skills
        }

    async def analyze_jd_requirements(
        self,
        state: ResumeWorkflowState,
    ) -> dict[str, list[str]]:
        logger.info(
            "Workflow node start node=analyze_jd_requirements jd_len=%s jd_preview=%r",
            len(state["jd_text"]),
            state["jd_text"][:50],
        )
        payload = await self._call_json_node(
            system_prompt=(
                "Extract required skills from the job description. Return only JSON "
                "with key \"jd_required_skills\" as an array of concise skill strings."
            ),
            user_prompt=f"Job Description:\n{state['jd_text']}",
        )
        required_skills = self._optional_string_list(payload, "jd_required_skills")
        logger.info(
            "Workflow node complete node=analyze_jd_requirements required_skill_count=%s",
            len(required_skills),
        )
        return {"jd_required_skills": required_skills}

    async def calculate_match_score(
        self,
        state: ResumeWorkflowState,
    ) -> dict[str, int]:
        logger.info("Workflow node start node=calculate_match_score")
        payload = await self._call_json_node(
            system_prompt=(
                "Calculate a resume-to-JD match score. Return only JSON with key "
                "\"match_score\" as an integer from 0 to 100."
            ),
            user_prompt=(
                f"Resume skills: {state['extracted_resume_skills']}\n"
                f"JD required skills: {state['jd_required_skills']}"
            ),
        )
        score = payload.get("match_score")
        normalized_score = score if isinstance(score, int) and 0 <= score <= 100 else 0
        logger.info("Workflow match_score calculated value=%s", normalized_score)
        return {
            "match_score": normalized_score
        }

    def route_after_match_score(self, state: ResumeWorkflowState) -> str:
        route = (
            "recommend_application"
            if state.get("match_score", 0) >= 75
            else "generate_learning_plan"
        )
        logger.info(
            "Workflow conditional route match_score=%s route=%s",
            state.get("match_score", 0),
            route,
        )
        return route

    async def generate_learning_plan(
        self,
        state: ResumeWorkflowState,
    ) -> dict[str, list[str]]:
        logger.info(
            "Workflow node start node=generate_learning_plan match_score=%s",
            state["match_score"],
        )
        payload = await self._call_json_node(
            system_prompt=(
                "Generate a focused learning plan in Chinese for a candidate whose "
                "resume match score is below 75. Return only JSON with key "
                "\"learning_plan\" as an array of actionable strings."
            ),
            user_prompt=(
                f"Resume skills: {state['extracted_resume_skills']}\n"
                f"JD required skills: {state['jd_required_skills']}\n"
                f"Match score: {state['match_score']}"
            ),
        )
        learning_plan = self._optional_string_list(payload, "learning_plan")
        logger.info(
            "Workflow node complete node=generate_learning_plan item_count=%s",
            len(learning_plan),
        )
        return {"learning_plan": learning_plan}

    async def recommend_application(
        self,
        state: ResumeWorkflowState,
    ) -> dict[str, str]:
        logger.info(
            "Workflow node start node=recommend_application match_score=%s",
            state["match_score"],
        )
        payload = await self._call_json_node(
            system_prompt=(
                "Generate an application recommendation in Chinese for a candidate "
                "whose resume match score is at least 75. Return only JSON with key "
                "\"application_recommendation\" as a string."
            ),
            user_prompt=(
                f"Resume skills: {state['extracted_resume_skills']}\n"
                f"JD required skills: {state['jd_required_skills']}\n"
                f"Match score: {state['match_score']}"
            ),
        )
        recommendation = self._optional_string_value(
            payload,
            "application_recommendation",
            "",
        )
        logger.info(
            "Workflow node complete node=recommend_application has_recommendation=%s",
            bool(recommendation),
        )
        return {"application_recommendation": recommendation}

    async def generate_resume_suggestions(
        self,
        state: ResumeWorkflowState,
    ) -> dict[str, Any]:
        logger.info(
            "Workflow node start node=generate_resume_suggestions match_score=%s has_memory=%s",
            state["match_score"],
            bool(state["memory_context"]),
        )
        payload = await self._call_json_node(
            system_prompt=(
                "Generate resume optimization output in Chinese. Return only JSON "
                "with keys: strengths, missing_skills, resume_suggestions, "
                "project_rewrite_suggestions, summary. All list fields must be "
                "arrays of strings."
            ),
            user_prompt=(
                f"Resume:\n{state['resume_text']}\n\n"
                f"Job Description:\n{state['jd_text']}\n\n"
                f"Resume skills: {state['extracted_resume_skills']}\n"
                f"JD required skills: {state['jd_required_skills']}\n"
                f"Match score: {state['match_score']}\n"
                f"Learning plan: {state['learning_plan']}\n"
                f"Application recommendation: {state['application_recommendation']}\n"
                f"Memory context:\n{state['memory_context']}"
            ),
        )
        summary = self._optional_string_value(
            payload,
            "summary",
            self.DEFAULT_SUMMARY,
        )
        summary = self._merge_branch_context_into_summary(summary, state)
        logger.info(
            "Workflow node complete node=generate_resume_suggestions summary_len=%s",
            len(summary),
        )
        return {
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
            "summary": summary,
        }

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

    def _optional_string_list(self, payload: dict[str, Any], key: str) -> list[str]:
        value = payload.get(key)
        if value is None:
            return []
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, str)]

    def _optional_string_value(
        self,
        payload: dict[str, Any],
        key: str,
        default: str,
    ) -> str:
        value = payload.get(key)
        return value if isinstance(value, str) and value.strip() else default

    def _merge_branch_context_into_summary(
        self,
        summary: str,
        state: ResumeWorkflowState,
    ) -> str:
        if state.get("application_recommendation"):
            return f"{summary}\n\nApplication recommendation: {state['application_recommendation']}"
        if state.get("learning_plan"):
            plan = "; ".join(state["learning_plan"])
            return f"{summary}\n\nLearning plan: {plan}"
        return summary
