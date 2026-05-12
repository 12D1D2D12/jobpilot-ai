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

        # Keep the model contract strict so the API can parse it safely.
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are JobPilot AI, a senior resume optimization agent. "
                        "Compare the candidate resume with the job description. "
                        "Return only valid JSON. Do not return Markdown. "
                        "Do not wrap the JSON in code fences. "
                        "Do not add explanations before or after the JSON. "
                        "All string values must be written in Chinese. "
                        "The JSON schema must be: "
                        "{"
                        "\"match_score\": integer from 0 to 100, "
                        "\"strengths\": array of strings, "
                        "\"missing_skills\": array of strings, "
                        "\"resume_suggestions\": array of strings, "
                        "\"project_rewrite_suggestions\": array of strings, "
                        "\"summary\": string"
                        "}."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Optimize this resume for the target job description. "
                        "Return only the JSON object described by the system prompt.\n\n"
                        f"Resume:\n{resume_text}\n\n"
                        f"Job Description:\n{jd_text}"
                    ),
                },
            ],
            temperature=0.3,
        )

        return response.choices[0].message.content or ""
