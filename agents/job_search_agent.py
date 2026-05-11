from dataclasses import dataclass


@dataclass(slots=True)
class JobSearchAgent:
    """Placeholder for future LangGraph-powered job search workflows."""

    name: str = "job-search-agent"

    async def plan(self, user_goal: str) -> dict[str, str]:
        return {
            "agent": self.name,
            "goal": user_goal,
            "status": "planned",
        }
