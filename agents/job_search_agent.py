from dataclasses import dataclass

from services.config import get_settings
from services.openai_client import get_openai_client


@dataclass(slots=True)
class JobSearchAgent:
    """Agent entry point for job search analysis workflows."""

    name: str = "job-search-agent"

    async def plan(self, user_goal: str) -> dict[str, str]:
        return {
            "agent": self.name,
            "goal": user_goal,
            "status": "planned",
        }

    async def analyze_jd(self, jd_text: str) -> str:
        settings = get_settings()
        client = get_openai_client()

        # Keep the prompt compact so the endpoint stays focused on JD analysis.
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are JobPilot AI, a senior AI career assistant. "
                        "Analyze job descriptions for job seekers. "
                        "Return concise output in Chinese with three sections: "
                        "1. Job Summary 2. Core Skills 3. Learning Advice."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Analyze this job description:\n\n{jd_text}",
                },
            ],
            temperature=0.3,
        )

        return response.choices[0].message.content or ""
