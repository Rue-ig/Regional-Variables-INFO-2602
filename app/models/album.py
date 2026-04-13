from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

class AlbumEventLink(SQLModel, table=True):
    album_id: int = Field(foreign_key="album.id", primary_key=True)
    event_id: int = Field(foreign_key="event.id", primary_key=True)

class Album(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    events: List["Event"] = Relationship(back_populates="albums", link_model=AlbumEventLink)