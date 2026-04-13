from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from typing import Optional

class Visit(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    path: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))