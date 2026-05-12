# JobPilot AI

JobPilot AI is a FastAPI-based AI Agent Engineering project for building job search automation workflows. The codebase is structured for real product development: API routes, service integrations, agent orchestration, database access, prompts, and tests are separated so the project can grow without turning into a single-file demo.

## Tech Stack

- Python 3.11+
- FastAPI with async request handlers
- Pydantic Settings for environment configuration
- SQLAlchemy async engine for PostgreSQL
- OpenAI API for model calls
- LangGraph for agent workflows
- Playwright for browser automation
- Pytest and HTTPX for async API tests

## Project Structure

```text
.
├── api/
│   ├── app.py
│   └── routes/
│       └── health.py
├── agents/
│   └── job_search_agent.py
├── database/
│   └── session.py
├── prompts/
│   └── system.md
├── services/
│   └── config.py
├── tests/
│   └── test_health.py
├── .env.example
├── main.py
├── README.md
└── requirements.txt
```

## Quick Start

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a local environment file:

```bash
cp .env.example .env
```

Run the API:

```bash
uvicorn main:app --reload
```

Open the health check endpoint:

```text
GET http://127.0.0.1:8000/api/v1/health
```

Analyze a job description:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/job/analyze \
  -H "Content-Type: application/json" \
  -d "{\"jd_text\":\"招聘 Python AI Engineer，负责 FastAPI、OpenAI Agent 和自动化工作流开发。\"}"
```

Run tests:

```bash
pytest
```

## Next Steps

- Add OpenAI-powered services under `services/`.
- Model agent workflows with LangGraph under `agents/`.
- Add async PostgreSQL models and migrations under `database/`.
- Add browser automation skills with Playwright for job board workflows.
- Expand prompts under `prompts/` as versioned agent instructions.
