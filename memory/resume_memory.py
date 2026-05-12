from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import ResumeAnalysisRecord


class ResumeMemoryManager:
    _user_summaries: dict[str, list[str]] = defaultdict(list)

    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    def save_analysis_summary(
        self,
        user_id: str,
        summary: str,
        match_score: int,
        missing_skills: list[str],
    ) -> None:
        memory_item = (
            f"user={user_id}; score={match_score}; "
            f"missing_skills={', '.join(missing_skills) or 'none'}; "
            f"summary={summary}"
        )
        self._user_summaries[user_id].append(memory_item)
        self._user_summaries[user_id] = self._user_summaries[user_id][-20:]

    def get_recent_analysis_history(self, limit: int = 5) -> list[ResumeAnalysisRecord]:
        if self.db is None:
            return []

        return list(
            self.db.scalars(
                select(ResumeAnalysisRecord)
                .order_by(
                    ResumeAnalysisRecord.created_at.desc(),
                    ResumeAnalysisRecord.id.desc(),
                )
                .limit(limit)
            ).all()
        )

    def get_memory_context(self, user_id: str, limit: int = 5) -> str:
        user_memory = self._user_summaries.get(user_id, [])[-limit:]
        history = self.get_recent_analysis_history(limit=limit)

        context_parts: list[str] = []
        if user_memory:
            context_parts.append("User memory summaries:")
            context_parts.extend(f"- {item}" for item in user_memory)

        if history:
            context_parts.append("Recent resume analysis history:")
            for record in history:
                missing = ", ".join(record.missing_skills) or "none"
                context_parts.append(
                    f"- score={record.match_score}; missing_skills={missing}; "
                    f"summary={record.summary}"
                )

        if not context_parts:
            return "No previous resume analysis memory is available."

        return "\n".join(context_parts)
