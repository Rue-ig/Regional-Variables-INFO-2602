# PATH: app/models/photo.py
from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from datetime import datetime

class PhotoBase(SQLModel):
    filepath: str
    caption: Optional[str] = None

class Photo(PhotoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    approved: bool = True
    hearts: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: "User" = Relationship(back_populates="photos")
    event: "Event" = Relationship(back_populates="photos")
    
    reports: List["Report"] = Relationship(
        back_populates="photo", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    @property
    def url(self) -> str:
        return f"/static/uploads/{self.filepath}"
