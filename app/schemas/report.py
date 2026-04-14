# PATH: app/schemas/report.py
from sqlmodel import SQLModel
from typing import Optional
from datetime import datetime
from pydantic import model_validator
from app.models.report import ReportReason

class ReportCreate(SQLModel):
    reason: ReportReason
    details: Optional[str] = None
    photo_id: Optional[int] = None
    review_id: Optional[int] = None

    @model_validator(mode="after")
    def check_target_exists(self) -> "ReportCreate":
        if not self.photo_id and not self.review_id:
            raise ValueError("A report must target either a photo_id or a review_id.")
            
        if self.photo_id and self.review_id:
            raise ValueError("A report cannot target both a photo_id and a review_id simultaneously.")
            
        return self

class ReportResponse(SQLModel):
    id: int
    user_id: int
    photo_id: Optional[int] = None
    review_id: Optional[int] = None
    reason: ReportReason
    details: Optional[str] = None
    status: str
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }
