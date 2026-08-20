from __future__ import annotations

from math import ceil
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from radar.api.dependencies import get_session
from radar.api.schemas.jobs import Attainability, JobDetail, JobListItem, JobsPage, Salary
from radar.database.models.job import JobDB
from radar.database.repositories.jobs import JobRepository, JobSearchFilters


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobsPage, summary="List jobs")
def list_jobs(
    q: str | None = Query(default=None, description="Search title, company, and description"),
    source: str | None = None,
    company: str | None = None,
    remote: bool | None = None,
    employment_type: str | None = None,
    seniority: str | None = None,
    min_score: int | None = Query(default=None, ge=0, le=100),
    max_score: int | None = Query(default=None, ge=0, le=100),
    relevance_band: str | None = None,
    active: bool | None = True,
    location: str | None = None,
    technology: str | None = Query(default=None, description="Single technology filter; exact match"),
    attainability: Literal["HIGH", "MEDIUM", "LOW"] | None = Query(
        default=None,
        description="Professional attainability level",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
) -> JobsPage:
    if min_score is not None and max_score is not None and min_score > max_score:
        raise HTTPException(status_code=422, detail="min_score cannot be greater than max_score")
    result = JobRepository(session).search(
        JobSearchFilters(
            q=q,
            source=source,
            company=company,
            remote=remote,
            employment_type=employment_type,
            seniority=seniority,
            min_score=min_score,
            max_score=max_score,
            relevance_band=relevance_band,
            active=active,
            location=location,
            technology=technology,
            attainability=attainability,
        ),
        page=page,
        page_size=page_size,
    )
    return JobsPage(
        items=[_job_list_item(job) for job in result.items],
        page=page,
        page_size=page_size,
        total=result.total,
        pages=ceil(result.total / page_size) if result.total else 0,
    )


@router.get("/{job_id}", response_model=JobDetail, summary="Get job detail")
def get_job(job_id: int, session: Session = Depends(get_session)) -> JobDetail:
    job = JobRepository(session).get_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return _job_detail(job)


def _job_list_item(job: JobDB) -> JobListItem:
    return JobListItem(
        id=job.id,
        title=job.title,
        company=job.company,
        source=job.source.name,
        url=job.url,
        location=job.location,
        remote=job.remote_type == "remote",
        remote_type=job.remote_type,
        employment_type=job.employment_type,
        seniority=job.seniority,
        technologies=list(job.technologies or []),
        published_at=job.published_at,
        first_seen_at=job.first_seen_at,
        last_seen_at=job.last_seen_at,
        relevance_score=job.relevance_score,
        relevance_band=job.relevance_band,
        attainability=_attainability(job.relevance_reasons),
    )


def _attainability(reasons: dict | None) -> Attainability | None:
    value = reasons.get("attainability") if isinstance(reasons, dict) else None
    if not isinstance(value, dict) or value.get("level") not in {"HIGH", "MEDIUM", "LOW"}:
        return None
    return Attainability(
        level=value["level"],
        positive=value.get("positive") if isinstance(value.get("positive"), list) else [],
        warnings=value.get("warnings") if isinstance(value.get("warnings"), list) else [],
        negative=value.get("negative") if isinstance(value.get("negative"), list) else [],
    )


def _job_detail(job: JobDB) -> JobDetail:
    item = _job_list_item(job)
    base = item.model_dump() if hasattr(item, "model_dump") else item.dict()
    return JobDetail(
        **base,
        description=job.description,
        salary=Salary(min=job.salary_min, max=job.salary_max, currency=job.salary_currency),
        relevance_reasons=job.relevance_reasons,
    )
