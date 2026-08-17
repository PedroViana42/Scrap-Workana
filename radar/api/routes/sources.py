from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from radar.api.dependencies import get_session
from radar.api.schemas.sources import SourceItem
from radar.database.repositories.sources import SourceRepository


router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceItem], summary="List Radar sources")
def list_sources(session: Session = Depends(get_session)) -> list[SourceItem]:
    return [
        SourceItem(
            name=source.name,
            display_name=source.display_name,
            content_type=source.content_type,
            enabled=source.enabled,
            status=source.status,
            collector=source.collector,
            priority=source.priority,
        )
        for source in SourceRepository(session).list_all()
    ]
