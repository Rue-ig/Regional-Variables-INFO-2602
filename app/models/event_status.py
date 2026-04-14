# PATH: app/models/event_status.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class UserEventStatus(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    event_id: int = Field(foreign_key="event.id")
    status: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
