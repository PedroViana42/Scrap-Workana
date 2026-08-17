from pydantic import BaseModel


class SourceItem(BaseModel):
    name: str
    display_name: str
    content_type: str
    enabled: bool
    status: str
    collector: str | None
    priority: int
