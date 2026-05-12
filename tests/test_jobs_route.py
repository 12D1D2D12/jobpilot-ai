from httpx import ASGITransport, AsyncClient
import pytest

from api.app import create_app
from tools.job_scraper_tool import JobScraperTool, JobScraperToolError


@pytest.mark.asyncio
async def test_jobs_search_route_uses_scraper_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_scrape_jobs(self: JobScraperTool, keyword: str) -> list[dict]:
        assert keyword == "python"
        return [
            {
                "title": "Python AI Engineer",
                "company": "AgentWorks",
                "location": "Remote",
                "skills": ["Python", "FastAPI", "LangGraph"],
            }
        ]

    monkeypatch.setattr(JobScraperTool, "scrape_jobs", fake_scrape_jobs)

    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/jobs/search", params={"keyword": "python"})

    assert response.status_code == 200
    assert response.json()[0]["title"] == "Python AI Engineer"


@pytest.mark.asyncio
async def test_jobs_search_route_returns_clear_playwright_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_scrape_jobs(self: JobScraperTool, keyword: str) -> list[dict]:
        raise JobScraperToolError(
            "Playwright Chromium is not installed. Run: python -m playwright install chromium"
        )

    monkeypatch.setattr(JobScraperTool, "scrape_jobs", fake_scrape_jobs)

    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/jobs/search", params={"keyword": "python"})

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Playwright Chromium is not installed. Run: python -m playwright install chromium"
    )
