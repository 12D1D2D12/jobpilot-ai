# JobPilot AI - Multi-Agent Job Hunting Automation Platform

JobPilot AI is a FastAPI AI backend for job hunting automation. It combines JD analysis, structured resume optimization, LangGraph workflow orchestration, SQLite history, memory context, internal tool calling, and observability logging.

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
- [x] Observability Logging

## Architecture

```text
API Route
↓
Service Layer
↓
LangGraph Workflow
↓
Agent / Tools
↓
Database
```

## API Endpoints

```text
GET  /api/v1/health
POST /api/v1/job/analyze
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

## Engineering Highlights

- Layered architecture with clear route, service, workflow, agent, tool, and database boundaries
- Pydantic validation for request and structured response schemas
- LLM fallback handling for unstable or incomplete model outputs
- Mock-based testing for agents, workflow, tools, and service boundaries
- SQLite persistence for resume analysis history
- Memory context built from recent analysis records
- Internal SkillGapTool for deterministic learning-plan generation
- Observability logging for workflow nodes, routing decisions, match scores, memory usage, and database saves
- GitHub-friendly commit history and modular project structure

## Roadmap

- Playwright browser automation
- Real job scraping
- Auto application tracking
- Frontend dashboard
- PostgreSQL migration
- Deployment with Docker
