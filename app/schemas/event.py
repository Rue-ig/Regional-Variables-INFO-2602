# PATH: app/schemas/event.py
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime
from app.models.event import Island, EventCategory, EventStatus

class EventCreate(BaseModel):
    title: str
    description: str = ""
    island: Island
    venue: str
    date: datetime
    end_date: Optional[datetime] = None
    price: Optional[float] = None
    category: EventCategory = EventCategory.Other
    source_url: Optional[str] = None
    image_url: Optional[str] = None
    status: EventStatus = EventStatus.draft

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    island: Optional[Island] = None
    venue: Optional[str] = None
    date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    price: Optional[float] = None
    category: Optional[EventCategory] = None
    source_url: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[EventStatus] = None

class EventResponse(BaseModel):
    id: int
    title: str
    description: str
    island: Island
    venue: str
    date: datetime
    end_date: Optional[datetime]
    price: Optional[float]
    category: EventCategory
    source_url: Optional[str]
    image_url: Optional[str]
    status: EventStatus
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EventFilter(BaseModel):
    island: Optional[Island] = None
    category: Optional[EventCategory] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    keyword: Optional[str] = None
    price_range: Optional[Literal["free", "paid", ""]] = None
