import asyncio
from typing import Any

import httpx


BASE_URL = "http://127.0.0.1:8000"


async def main() -> None:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        await run_step("[1] Health Check", call_health_check(client))
        await run_step("[2] JD Analyzer", call_jd_analyzer(client))
        await run_step("[3] Resume Optimizer", call_resume_optimizer(client))
        await run_step("[4] Resume History", call_resume_history(client))
        await run_step("[5] Job Scraper", call_job_scraper(client))


async def run_step(title: str, request_coro) -> None:
    print(f"\n{title}")
    print("-" * len(title))

    try:
        response = await request_coro
    except httpx.ConnectError:
        print("API server is not running. Start it with: uvicorn main:app --reload")
        return
    except httpx.HTTPError as exc:
        print(f"Request failed: {exc}")
        return

    print_response(response)


async def call_health_check(client: httpx.AsyncClient) -> httpx.Response:
    return await client.get("/api/v1/health")


async def call_jd_analyzer(client: httpx.AsyncClient) -> httpx.Response:
    return await client.post(
        "/api/v1/job/analyze",
        json={
            "jd_text": (
                "We are hiring a Python AI backend engineer with FastAPI, "
                "OpenAI SDK, LangGraph workflow, Redis, and Docker experience."
            )
        },
    )


async def call_resume_optimizer(client: httpx.AsyncClient) -> httpx.Response:
    return await client.post(
        "/api/v1/resume/optimize",
        json={
            "resume_text": (
                "Python backend developer with FastAPI API development, "
                "LLM application experience, and several internal automation tools."
            ),
            "jd_text": (
                "Looking for an AI backend engineer familiar with FastAPI, "
                "LangGraph, Redis, Docker, and production LLM workflows."
            ),
        },
    )


async def call_resume_history(client: httpx.AsyncClient) -> httpx.Response:
    return await client.get("/api/v1/resume/history")


async def call_job_scraper(client: httpx.AsyncClient) -> httpx.Response:
    return await client.get("/api/v1/jobs/search", params={"keyword": "python"})


def print_response(response: httpx.Response) -> None:
    print(f"Status: {response.status_code}")

    try:
        payload: Any = response.json()
    except ValueError:
        print(response.text)
        return

    if response.status_code >= 400:
        print("Error:")
        print(payload)
        return

    print(payload)


if __name__ == "__main__":
    asyncio.run(main())
