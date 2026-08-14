from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from radar.api.dependencies import get_session
from radar.api.schemas.stats import StatsResponse
from radar.database.repositories.stats import StatsRepository


router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsResponse, summary="Get dashboard stats")
def get_stats(session: Session = Depends(get_session)) -> StatsResponse:
    return StatsResponse(**StatsRepository(session).summary())
