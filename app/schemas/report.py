from sqlmodel import SQLModel
from typing import Optional
from enum import Enum
from datetime import datetime

class ReportReason(str, Enum):
    SPAM = "Spam"
    INAPPROPRIATE = "Inappropriate"
    HARASSMENT = "Harassment"
    OFFENSIVE = "Offensive"
    OTHER = "Other"

class ReportCreate(SQLModel):
    reason: ReportReason
    details: Optional[str] = None
    photo_id: Optional[int] = None
    review_id: Optional[int] = None

class ReportResponse(SQLModel):
    id: int
    user_id: int
    photo_id: Optional[int]
    review_id: Optional[int]
    reason: ReportReason
    details: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True