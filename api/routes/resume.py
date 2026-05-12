import json
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, ValidationError

from agents.resume_optimizer_agent import ResumeOptimizerAgent
from services.openai_client import OpenAIClientError


router = APIRouter(prefix="/resume", tags=["resume"])


class ResumeOptimizeRequest(BaseModel):
    resume_text: str = Field(..., min_length=20, description="Candidate resume text.")
    jd_text: str = Field(..., min_length=20, description="Target job description text.")


class ResumeOptimizeResponse(BaseModel):
    match_score: int = Field(..., ge=0, le=100)
    strengths: list[str]
    missing_skills: list[str]
    resume_suggestions: list[str]
    project_rewrite_suggestions: list[str]
    summary: str


def parse_resume_optimizer_result(raw_result: str) -> ResumeOptimizeResponse:
    try:
        payload: Any = json.loads(raw_result)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Resume optimizer returned invalid JSON.",
        ) from exc

    try:
        return ResumeOptimizeResponse.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Resume optimizer JSON does not match the expected schema.",
        ) from exc


@router.post("/optimize", response_model=ResumeOptimizeResponse)
async def optimize_resume(request: ResumeOptimizeRequest) -> ResumeOptimizeResponse:
    agent = ResumeOptimizerAgent()

    try:
        raw_result = await agent.optimize_resume(
            resume_text=request.resume_text,
            jd_text=request.jd_text,
        )
    except OpenAIClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return parse_resume_optimizer_result(raw_result)
