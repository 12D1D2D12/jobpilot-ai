# JobPilot AI

JobPilot AI is a FastAPI-based AI Agent Engineering project for job search workflows. It includes JD analysis, LangGraph resume optimization, conditional routing, memory context, internal tool calling, SQLite persistence, and observability logging for debugging agent workflows.

## Tech Stack

- Python 3.11+
- FastAPI with async request handlers
- OpenAI-compatible SDK integration
- LangGraph StateGraph for resume workflow orchestration
- Internal tools for deterministic agent support tasks
- SQLAlchemy with SQLite persistence
- Python standard logging for observability
- Pytest and HTTPX for API tests

## Project Structure

```text
.
├── agents/
├── api/
│   └── routes/
├── database/
├── memory/
├── prompts/
├── services/
├── tests/
├── tools/
├── workflow/
├── main.py
├── README.md
└── requirements.txt
```

## Quick Start

```bash
python -m venv venv
pip install -r requirements.txt
uvicorn main:app --reload
```

The app creates `jobpilot.db` automatically on startup.

## APIs

```text
GET  /api/v1/health
POST /api/v1/job/analyze
POST /api/v1/resume/optimize
GET  /api/v1/resume/history
```

Resume optimization response:

```json
{
  "match_score": 86,
  "strengths": ["..."],
  "missing_skills": ["..."],
  "resume_suggestions": ["..."],
  "project_rewrite_suggestions": ["..."],
  "summary": "..."
}
```

## Observability

JobPilot AI uses Python standard `logging` through `services/logger.py`.

Logs include:

- Resume optimization start and input text lengths
- Workflow completion and match score
- SQLite save success
- Resume history query count
- LangGraph node start and completion
- Conditional routing decision
- Whether memory context exists

Logs intentionally do not include API keys or full resume/JD text. Only text lengths and short previews are recorded.

## Tool Calling

The resume workflow includes an internal `SkillGapTool`.

When the match score is below 75, LangGraph routes to the learning-plan branch. That branch identifies missing skills, calls `SkillGapTool.generate_learning_plan()`, and merges the generated plan into the final summary without changing the public API schema.

Supported deterministic skill plans include Redis, Docker, LangGraph, and FastAPI. Unknown skills receive a generic hands-on learning plan.

## Testing

```bash
pytest
```

Resume workflow tests use mocks and do not call the real model.
