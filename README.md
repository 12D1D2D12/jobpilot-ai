# JobPilot AI - Multi-Agent Job Hunting Automation Platform

JobPilot AI is a FastAPI AI backend for job hunting automation. It combines JD analysis, structured resume optimization, LangGraph workflow orchestration, SQLite history, memory context, internal tool calling, Playwright browser automation, and observability logging.

The project is designed as an AI Agent Engineering backend rather than a simple demo: API routes, service layer, workflow orchestration, agents, tools, memory, and database persistence are separated for maintainability.

## Features

- [x] JD Analyzer Agent
- [x] Resume Optimizer Agent
- [x] Structured JSON Output
- [x] SQLite Persistence
- [x] LangGraph Workflow
- [x] Conditional Routing
- [x] Memory Context
- [x] SkillGapTool Tool Calling
- [x] Browser Agent with Playwright Tool Calling
- [x] Observability Logging

## Architecture

```text
API Route
  |
  v
Service Layer
  |
  v
LangGraph Workflow
  |
  v
Agent / Tools
  |
  v
Database
```

## API Endpoints

```text
GET  /api/v1/health
POST /api/v1/job/analyze
GET  /api/v1/jobs/search?keyword=python
POST /api/v1/resume/optimize
GET  /api/v1/resume/history
```

## Quick Start

Create a virtual environment:

```bash
python -m venv venv
```

Activate it:

```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

If `GET /api/v1/jobs/search` returns a Playwright browser error, run:

```bash
python -m playwright install chromium
```

Configure environment variables:

```bash
cp .env.example .env
```

Set your OpenAI-compatible API key in `.env`.

Start the API:

```bash
uvicorn main:app --reload
```

Open Swagger docs:

```text
http://127.0.0.1:8000/docs
```

## Demo Script

After starting the API locally, run:

```bash
python scripts/demo.py
```

The script demonstrates:

- Health check
- JD Analyzer
- Resume Optimizer
- Resume History
- Playwright Job Scraper

## Example Request

`POST /api/v1/resume/optimize`

```json
{
  "resume_text": "Experienced Python backend developer with FastAPI API experience and AI application projects.",
  "jd_text": "We are looking for an AI backend engineer familiar with FastAPI, LangGraph, Redis, Docker, and LLM application development."
}
```

Example response shape:

```json
{
  "match_score": 78,
  "strengths": ["..."],
  "missing_skills": ["..."],
  "resume_suggestions": ["..."],
  "project_rewrite_suggestions": ["..."],
  "summary": "..."
}
```

## Browser Agent

The project includes a first-stage Playwright browser automation tool:

```text
GET /api/v1/jobs/search?keyword=python
```

`JobScraperTool` opens a browser page, loads a public demo job board HTML page, extracts job cards, filters them by keyword, and returns structured job data:

```json
[
  {
    "title": "Python AI Backend Engineer",
    "company": "AgentWorks",
    "location": "Remote",
    "skills": ["Python", "FastAPI", "OpenAI", "LangGraph"]
  }
]
```

This is intentionally not a real login-based scraper yet. It demonstrates the browser automation architecture safely before adding real job scraping.

## Engineering Highlights

- Layered architecture with clear route, service, workflow, agent, tool, and database boundaries
- Pydantic validation for request and structured response schemas
- LLM fallback handling for unstable or incomplete model outputs
- Mock-based testing for agents, workflow, tools, and service boundaries
- SQLite persistence for resume analysis history
- Memory context built from recent analysis records
- Internal SkillGapTool for deterministic learning-plan generation
- Playwright JobScraperTool for browser automation experiments
- Observability logging for workflow nodes, routing decisions, match scores, memory usage, and database saves
- GitHub-friendly commit history and modular project structure

## Roadmap

- Real job scraping
- Auto application tracking
- Frontend dashboard
- PostgreSQL migration
- Deployment with Docker
