import json
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from agents.resume_optimizer_agent import ResumeOptimizerAgent
from database.models import ResumeAnalysisRecord
from services.openai_client import OpenAIClientError


class ResumeOptimizeResult(BaseModel):
    match_score: int = Field(..., ge=0, le=100)
    strengths: list[str]
    missing_skills: list[str]
    resume_suggestions: list[str]
    project_rewrite_suggestions: list[str]
    summary: str


class ResumeAnalysisHistoryItem(ResumeOptimizeResult):
    id: int
    resume_text: str
    jd_text: str
    created_at: datetime


class ResumeService:
    def __init__(
        self,
        db: Session,
        agent: ResumeOptimizerAgent | None = None,
    ) -> None:
        self.db = db
        self.agent = agent or ResumeOptimizerAgent()

    async def optimize_resume(
        self,
        resume_text: str,
        jd_text: str,
    ) -> ResumeOptimizeResult:
        try:
            raw_result = await self.agent.optimize_resume(
                resume_text=resume_text,
                jd_text=jd_text,
            )
        except OpenAIClientError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc

        result = self._parse_optimizer_result(raw_result)
        self._save_analysis_record(
            resume_text=resume_text,
            jd_text=jd_text,
            result=result,
        )
        return result

    async def get_history(self, limit: int = 20) -> list[ResumeAnalysisHistoryItem]:
        records = self.db.scalars(
            select(ResumeAnalysisRecord)
            .order_by(
                ResumeAnalysisRecord.created_at.desc(),
                ResumeAnalysisRecord.id.desc(),
            )
            .limit(limit)
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

    def _parse_optimizer_result(self, raw_result: str) -> ResumeOptimizeResult:
        try:
            payload: Any = json.loads(raw_result)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Resume optimizer returned invalid JSON.",
            ) from exc

        try:
            return ResumeOptimizeResult.model_validate(payload)
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Resume optimizer JSON does not match the expected schema.",
            ) from exc

    def _save_analysis_record(
        self,
        resume_text: str,
        jd_text: str,
        result: ResumeOptimizeResult,
    ) -> None:
        record = ResumeAnalysisRecord(
            resume_text=resume_text,
            jd_text=jd_text,
            match_score=result.match_score,
            strengths=result.strengths,
            missing_skills=result.missing_skills,
            resume_suggestions=result.resume_suggestions,
            project_rewrite_suggestions=result.project_rewrite_suggestions,
            summary=result.summary,
        )
        self.db.add(record)
        self.db.commit()
