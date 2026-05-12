from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from tools.job_scraper_tool import JobScraperTool, JobScraperToolError


router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobSearchResult(BaseModel):
    title: str
    company: str
    location: str
    skills: list[str]


@router.get("/search", response_model=list[JobSearchResult])
async def search_jobs(
    keyword: str = Query(..., min_length=1, description="Job search keyword."),
) -> list[JobSearchResult]:
    tool = JobScraperTool()
    try:
        jobs = await tool.scrape_jobs(keyword=keyword)
    except JobScraperToolError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return [JobSearchResult.model_validate(job) for job in jobs]
