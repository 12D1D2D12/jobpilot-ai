import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from agents.resume_optimizer_agent import ResumeOptimizerAgent
from database.models import ResumeAnalysisRecord
from database.session import get_db
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


class ResumeAnalysisHistoryItem(ResumeOptimizeResponse):
    id: int
    resume_text: str
    jd_text: str
    created_at: datetime


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
async def optimize_resume(
    request: ResumeOptimizeRequest,
    db: Session = Depends(get_db),
) -> ResumeOptimizeResponse:
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

    result = parse_resume_optimizer_result(raw_result)

    record = ResumeAnalysisRecord(
        resume_text=request.resume_text,
        jd_text=request.jd_text,
        match_score=result.match_score,
        strengths=result.strengths,
        missing_skills=result.missing_skills,
        resume_suggestions=result.resume_suggestions,
        project_rewrite_suggestions=result.project_rewrite_suggestions,
        summary=result.summary,
    )
    db.add(record)
    db.commit()

    return result


@router.get("/history", response_model=list[ResumeAnalysisHistoryItem])
async def get_resume_history(db: Session = Depends(get_db)) -> list[ResumeAnalysisHistoryItem]:
    records = db.scalars(
        select(ResumeAnalysisRecord)
        .order_by(
            ResumeAnalysisRecord.created_at.desc(),
            ResumeAnalysisRecord.id.desc(),
        )
        .limit(20)
    ).all()

    return [
        ResumeAnalysisHistoryItem(
            id=record.id,
            resume_text=record.resume_text,
            jd_text=record.jd_text,
            match_score=record.match_score,
            strengths=record.strengths,
            missing_skills=record.missing_skills,
            resume_suggestions=record.resume_suggestions,
            project_rewrite_suggestions=record.project_rewrite_suggestions,
            summary=record.summary,
            created_at=record.created_at,
        )
        for record in records
    ]
