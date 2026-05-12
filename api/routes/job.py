from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from agents.job_search_agent import JobSearchAgent
from services.openai_client import OpenAIClientError


router = APIRouter(prefix="/job", tags=["job"])


class JobAnalyzeRequest(BaseModel):
    jd_text: str = Field(..., min_length=20, description="Job description text.")


class JobAnalyzeResponse(BaseModel):
    result: str


@router.post("/analyze", response_model=JobAnalyzeResponse)
async def analyze_job_description(request: JobAnalyzeRequest) -> JobAnalyzeResponse:
    agent = JobSearchAgent()

    try:
        result = await agent.analyze_jd(request.jd_text)
    except OpenAIClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return JobAnalyzeResponse(result=result)
