# JobPilot AI

JobPilot AI is a FastAPI-based AI Agent Engineering project for job search workflows. It includes JD analysis, resume optimization, OpenAI-compatible model integration, and SQLite persistence for resume analysis records.

## Tech Stack

- Python 3.11+
- FastAPI with async request handlers
- Pydantic Settings for environment configuration
- OpenAI-compatible SDK integration
- SQLAlchemy with SQLite persistence
- Pytest and HTTPX for API tests
- LangGraph and Playwright are reserved for later agent workflow and browser automation features

## Project Structure

```text
.
├── api/
│   ├── app.py
│   └── routes/
│       ├── health.py
│       ├── job.py
│       └── resume.py
├── agents/
│   ├── job_search_agent.py
│   └── resume_optimizer_agent.py
├── database/
│   ├── init_db.py
│   ├── models.py
│   └── session.py
├── prompts/
├── services/
│   ├── config.py
│   └── openai_client.py
├── tests/
├── main.py
├── README.md
└── requirements.txt
```

## Quick Start

Create and activate a virtual environment:

```bash
python -m venv venv
```

On Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the API:

```bash
uvicorn main:app --reload
```

The app creates `jobpilot.db` automatically on startup.

## APIs

Health check:

```text
GET http://127.0.0.1:8000/api/v1/health
```

Analyze a job description:

```text
POST http://127.0.0.1:8000/api/v1/job/analyze
```

Optimize a resume for a target JD:

```text
POST http://127.0.0.1:8000/api/v1/resume/optimize
```

Request body:

```json
{
  "resume_text": "Candidate resume text...",
  "jd_text": "Target job description text..."
}
```

Structured response:

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

Get recent resume analysis history:

```text
GET http://127.0.0.1:8000/api/v1/resume/history
```

This returns the latest 20 saved resume analysis records from SQLite.

## Testing

Run all tests:

```bash
pytest
```

Run resume persistence tests:

```bash
pytest tests/test_resume_optimize.py
```
