from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from radar.api.dependencies import get_session


router = APIRouter(tags=["health"])


@router.get("/health/live", summary="Process liveness")
def health_live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready", summary="Database readiness")
def health_ready(session: Session = Depends(get_session)) -> dict[str, str]:
    try:
        session.execute(text("SELECT 1")).scalar_one()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "ok"}


@router.get("/health", summary="Application and database health")
def health(session: Session = Depends(get_session)) -> dict[str, str]:
    return health_ready(session)
