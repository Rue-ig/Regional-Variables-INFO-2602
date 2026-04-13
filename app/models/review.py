# PATH: app/models/review.py
from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime

class ReviewBase(SQLModel):
    rating: int = Field(ge=1, le=5)
    body: str

class Review(ReviewBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    approved: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)