from datetime import datetime
from pydantic import BaseModel

class Message(BaseModel):
    type: str
    timestamp: datetime | None = None
