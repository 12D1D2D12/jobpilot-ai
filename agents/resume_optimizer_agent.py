from dataclasses import dataclass

from services.config import get_settings
from services.openai_client import get_openai_client


@dataclass(slots=True)
class ResumeOptimizerAgent:
    """Agent for tailoring a resume against a target job description."""

    name: str = "resume-optimizer-agent"

    async def optimize_resume(self, resume_text: str, jd_text: str) -> str:
        settings = get_settings()
        client = get_openai_client()

        # Keep the prompt scoped to practical resume optimization output.
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are JobPilot AI, a senior resume optimization agent. "
                        "Compare the candidate resume with the job description. "
                        "Return the result in Chinese with sections for: "
                        "1. Resume Match Analysis 2. Experiences To Strengthen "
                        "3. Resume Bullet Rewrites 4. Priority Optimization Advice."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Optimize this resume for the target job description. "
                        "Write the final answer in Chinese.\n\n"
                        f"Resume:\n{resume_text}\n\n"
                        f"Job Description:\n{jd_text}"
                    ),
                },
            ],
            temperature=0.3,
        )

        return response.choices[0].message.content or ""
