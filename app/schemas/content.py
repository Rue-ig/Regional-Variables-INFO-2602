# PATH: app/schemas/content.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReviewCreate(BaseModel):
    rating: int
    body: str

class ReviewResponse(BaseModel):
    id: int
    event_id: int
    user_id: int
    rating: int
    body: str
    approved: bool
    created_at: datetime

    class Config:
        from_attributes = True

class PhotoResponse(BaseModel):
    id: int
    event_id: int
    user_id: int
    filepath: str
    caption: Optional[str]
    approved: bool
    created_at: datetime

    class Config:
        from_attributes = True

class BookmarkResponse(BaseModel):
    id: int
    event_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True