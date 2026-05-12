from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.session import get_db
from services.resume_service import (
    ResumeAnalysisHistoryItem,
    ResumeOptimizeResult,
    ResumeService,
)


router = APIRouter(prefix="/resume", tags=["resume"])


class ResumeOptimizeRequest(BaseModel):
    resume_text: str = Field(..., min_length=20, description="Candidate resume text.")
    jd_text: str = Field(..., min_length=20, description="Target job description text.")


def get_resume_service(db: Session = Depends(get_db)) -> ResumeService:
    return ResumeService(db=db)


@router.post("/optimize", response_model=ResumeOptimizeResult)
async def optimize_resume(
    request: ResumeOptimizeRequest,
    service: ResumeService = Depends(get_resume_service),
) -> ResumeOptimizeResult:
    return await service.optimize_resume(
        resume_text=request.resume_text,
        jd_text=request.jd_text,
    )


@router.get("/history", response_model=list[ResumeAnalysisHistoryItem])
async def get_resume_history(
    service: ResumeService = Depends(get_resume_service),
) -> list[ResumeAnalysisHistoryItem]:
    return await service.get_history(limit=20)
