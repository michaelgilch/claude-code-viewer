from datetime import datetime
from pydantic import BaseModel

class Message(BaseModel):
    type: str
    timestamp: datetime | None = None
    session_id: str | None = None
    cwd: str | None = None
    slug: str | None = None
    role: str | None = None
