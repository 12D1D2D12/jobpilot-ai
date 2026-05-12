from collections.abc import Callable
from typing import Any

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import async_playwright

from services.logger import get_logger


logger = get_logger(__name__)


class JobScraperToolError(RuntimeError):
    """Raised when browser automation cannot be completed."""


class JobScraperTool:
    _DEMO_JOBS = [
        {
            "title": "Python AI Backend Engineer",
            "company": "AgentWorks",
            "location": "Remote",
            "skills": ["Python", "FastAPI", "OpenAI", "LangGraph"],
        },
        {
            "title": "Backend Platform Engineer",
            "company": "CloudPilot",
            "location": "Shanghai",
            "skills": ["Python", "Redis", "Docker", "PostgreSQL"],
        },
        {
            "title": "AI Automation Engineer",
            "company": "BrowserOps",
            "location": "Beijing",
            "skills": ["Playwright", "FastAPI", "Python", "Agents"],
        },
    ]

    def __init__(self, playwright_factory: Callable[[], Any] = async_playwright) -> None:
        self.playwright_factory = playwright_factory

    async def scrape_jobs(self, keyword: str) -> list[dict]:
        browser = None
        normalized_keyword = keyword.strip().lower()

        try:
            async with self.playwright_factory() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                logger.info("Job scraper browser started keyword=%r", keyword[:50])

                try:
                    page = await browser.new_page()
                    await page.set_content(self._render_demo_jobs_html())
                    logger.info("Job scraper page opened source=demo_html")

                    jobs = await self._extract_jobs_from_page(page)
                    logger.info("Job scraper jobs extracted count=%s", len(jobs))

                    filtered_jobs = [
                        job
                        for job in jobs
                        if self._matches_keyword(job=job, keyword=normalized_keyword)
                    ]
                    logger.info(
                        "Job scrape completed keyword=%r result_count=%s",
                        keyword[:50],
                        len(filtered_jobs),
                    )

                    return filtered_jobs
                finally:
                    if browser is not None:
                        await browser.close()
        except PlaywrightError as exc:
            message = str(exc)
            if "Executable doesn't exist" in message or "playwright install" in message:
                raise JobScraperToolError(
                    "Playwright Chromium is not installed. Run: python -m playwright install chromium"
                ) from exc
            raise JobScraperToolError(f"Playwright browser automation failed: {message}") from exc

        return []

    async def _extract_jobs_from_page(self, page: Any) -> list[dict]:
        cards = page.locator(".job-card")
        count = await cards.count()
        jobs: list[dict] = []

        for index in range(count):
            card = cards.nth(index)
            title = await card.locator("[data-field='title']").inner_text()
            company = await card.locator("[data-field='company']").inner_text()
            location = await card.locator("[data-field='location']").inner_text()
            skills_text = await card.locator("[data-field='skills']").inner_text()

            jobs.append(
                {
                    "title": title.strip(),
                    "company": company.strip(),
                    "location": location.strip(),
                    "skills": [
                        skill.strip()
                        for skill in skills_text.split(",")
                        if skill.strip()
                    ],
                }
            )

        return jobs

    def _matches_keyword(self, job: dict, keyword: str) -> bool:
        if not keyword:
            return True

        searchable_text = " ".join(
            [
                job.get("title", ""),
                job.get("company", ""),
                job.get("location", ""),
                " ".join(job.get("skills", [])),
            ]
        ).lower()
        return keyword in searchable_text

    def _render_demo_jobs_html(self) -> str:
        cards = []
        for job in self._DEMO_JOBS:
            cards.append(
                f"""
                <article class="job-card">
                    <h2 data-field="title">{job["title"]}</h2>
                    <p data-field="company">{job["company"]}</p>
                    <p data-field="location">{job["location"]}</p>
                    <p data-field="skills">{", ".join(job["skills"])}</p>
                </article>
                """
            )

        return f"<html><body>{''.join(cards)}</body></html>"
