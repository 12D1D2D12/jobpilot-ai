from dataclasses import dataclass

from services.config import get_settings
from services.openai_client import get_openai_client


@dataclass(slots=True)
class ResumeOptimizerAgent:
    """Low-level model caller used by resume workflow nodes."""

    name: str = "resume-optimizer-agent"

    async def run_json_task(self, system_prompt: str, user_prompt: str) -> str:
        settings = get_settings()
        client = get_openai_client()

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )

        return response.choices[0].message.content or ""

    async def optimize_resume(self, resume_text: str, jd_text: str) -> str:
        return await self.run_json_task(
            system_prompt=(
                "You are JobPilot AI. Return only valid JSON with keys: "
                "match_score, strengths, missing_skills, resume_suggestions, "
                "project_rewrite_suggestions, summary. Do not return Markdown."
            ),
            user_prompt=(
                "Optimize this resume for the target job description. "
                "Write string values in Chinese.\n\n"
                f"Resume:\n{resume_text}\n\n"
                f"Job Description:\n{jd_text}"
            ),
        )
