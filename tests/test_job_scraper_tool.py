from tools.job_scraper_tool import JobScraperTool
import pytest


class FakeFieldLocator:
    def __init__(self, value: str) -> None:
        self.value = value

    async def inner_text(self) -> str:
        return self.value


class FakeCardLocator:
    def __init__(self, job: dict) -> None:
        self.job = job

    def locator(self, selector: str) -> FakeFieldLocator:
        field = selector.split("'")[1]
        value = self.job[field]
        if isinstance(value, list):
            value = ", ".join(value)
        return FakeFieldLocator(value)


class FakeCardsLocator:
    def __init__(self, jobs: list[dict]) -> None:
        self.jobs = jobs

    async def count(self) -> int:
        return len(self.jobs)

    def nth(self, index: int) -> FakeCardLocator:
        return FakeCardLocator(self.jobs[index])


class FakePage:
    def __init__(self, jobs: list[dict]) -> None:
        self.jobs = jobs
        self.content = ""

    async def set_content(self, html: str) -> None:
        self.content = html

    def locator(self, selector: str) -> FakeCardsLocator:
        assert selector == ".job-card"
        return FakeCardsLocator(self.jobs)


class FakeBrowser:
    def __init__(self, jobs: list[dict]) -> None:
        self.jobs = jobs
        self.closed = False

    async def new_page(self) -> FakePage:
        return FakePage(self.jobs)

    async def close(self) -> None:
        self.closed = True


class FakeChromium:
    def __init__(self, jobs: list[dict]) -> None:
        self.jobs = jobs

    async def launch(self, headless: bool = True) -> FakeBrowser:
        assert headless is True
        return FakeBrowser(self.jobs)


class FakePlaywright:
    def __init__(self, jobs: list[dict]) -> None:
        self.chromium = FakeChromium(jobs)


class FakePlaywrightContext:
    def __init__(self, jobs: list[dict]) -> None:
        self.jobs = jobs

    async def __aenter__(self) -> FakePlaywright:
        return FakePlaywright(self.jobs)

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None


def fake_playwright_factory():
    return FakePlaywrightContext(
        [
            {
                "title": "Python Backend Engineer",
                "company": "TestCo",
                "location": "Remote",
                "skills": ["Python", "FastAPI"],
            },
            {
                "title": "Frontend Engineer",
                "company": "WebCo",
                "location": "Shanghai",
                "skills": ["React"],
            },
        ]
    )


@pytest.mark.asyncio
async def test_job_scraper_tool_uses_mock_playwright() -> None:
    tool = JobScraperTool(playwright_factory=fake_playwright_factory)

    jobs = await tool.scrape_jobs(keyword="python")

    assert len(jobs) == 1
    assert jobs[0]["title"] == "Python Backend Engineer"
    assert jobs[0]["skills"] == ["Python", "FastAPI"]
