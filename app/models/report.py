from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ReportReason(str, Enum):
    SPAM = "Spam"
    INAPPROPRIATE = "Inappropriate"
    HARASSMENT = "Harassment"
    OFFENSIVE = "Offensive"
    OTHER = "Other"

class ReportStatus(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    DISMISSED = "dismissed"
    ACTION_TAKEN = "action_taken"

class Report(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    photo_id: Optional[int] = Field(default=None, foreign_key="photo.id", nullable=True)
    review_id: Optional[int] = Field(default=None, foreign_key="review.id", nullable=True)
    reason: ReportReason
    details: Optional[str] = None
    status: ReportStatus = Field(default=ReportStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    admin_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    photo: Optional["Photo"] = Relationship(back_populates="reports")
    review: Optional["Review"] = Relationship(back_populates="reports")
    user: Optional["User"] = Relationship()
