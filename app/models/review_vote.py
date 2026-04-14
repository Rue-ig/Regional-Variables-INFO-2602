# PATH: app/models.review_vote.py
from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime

class ReviewVote(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    review_id: int = Field(foreign_key="review.id", index=True)
    vote: str = Field(...)
    created_at: datetime = Field(default_factory=datetime.utcnow)
