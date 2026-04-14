# PATH: app/models.review_vote.py
from sqlmodel import Field, SQLModel, UniqueConstraint
from typing import Optional
from datetime import datetime

class ReviewVote(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "review_id", name="unique_user_review_vote"),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    review_id: int = Field(foreign_key="review.id", index=True)
    vote: str = Field(...)
    created_at: datetime = Field(default_factory=datetime.utcnow)
