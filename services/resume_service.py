from datetime import datetime

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import ResumeAnalysisRecord
from memory.resume_memory import ResumeMemoryManager
from services.openai_client import OpenAIClientError
from workflow.resume_workflow import ResumeWorkflow, ResumeWorkflowError


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
        workflow: ResumeWorkflow | None = None,
    ) -> None:
        self.db = db
        self.memory_manager = ResumeMemoryManager(db=db)
        self.workflow = workflow or ResumeWorkflow(memory_manager=self.memory_manager)

    async def optimize_resume(
        self,
        resume_text: str,
        jd_text: str,
        user_id: str = "default_user",
    ) -> ResumeOptimizeResult:
        result = await self._run_resume_workflow(
            resume_text=resume_text,
            jd_text=jd_text,
            user_id=user_id,
        )
        self._save_analysis_record(
            resume_text=resume_text,
            jd_text=jd_text,
            result=result,
        )
        self._save_memory_summary(user_id=user_id, result=result)
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

    async def _run_resume_workflow(
        self,
        resume_text: str,
        jd_text: str,
        user_id: str,
    ) -> ResumeOptimizeResult:
        try:
            final_state = await self.workflow.compiled_graph.ainvoke(
                self.workflow.create_initial_state(
                    resume_text=resume_text,
                    jd_text=jd_text,
                    user_id=user_id,
                )
            )
            payload = self.workflow.to_result(final_state)
        except OpenAIClientError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        except ResumeWorkflowError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

        try:
            return ResumeOptimizeResult.model_validate(payload)
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Resume workflow result does not match the expected schema.",
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

    def _save_memory_summary(
        self,
        user_id: str,
        result: ResumeOptimizeResult,
    ) -> None:
        memory_manager = getattr(self.workflow, "memory_manager", self.memory_manager)
        memory_manager.save_analysis_summary(
            user_id=user_id,
            summary=result.summary,
            match_score=result.match_score,
            missing_skills=result.missing_skills,
        )
