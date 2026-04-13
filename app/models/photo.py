# PATH: app/models/photo.py
from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime

class PhotoBase(SQLModel):
    filepath: str
    caption: Optional[str] = None

class Photo(PhotoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    approved: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)