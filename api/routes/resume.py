from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from agents.resume_optimizer_agent import ResumeOptimizerAgent
from services.openai_client import OpenAIClientError


router = APIRouter(prefix="/resume", tags=["resume"])


class ResumeOptimizeRequest(BaseModel):
    resume_text: str = Field(..., min_length=20, description="Candidate resume text.")
    jd_text: str = Field(..., min_length=20, description="Target job description text.")


class ResumeOptimizeResponse(BaseModel):
    result: str


@router.post("/optimize", response_model=ResumeOptimizeResponse)
async def optimize_resume(request: ResumeOptimizeRequest) -> ResumeOptimizeResponse:
    agent = ResumeOptimizerAgent()

    try:
        result = await agent.optimize_resume(
            resume_text=request.resume_text,
            jd_text=request.jd_text,
        )
    except OpenAIClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return ResumeOptimizeResponse(result=result)
