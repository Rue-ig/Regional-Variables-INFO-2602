# PATH: app/models/event.py
from sqlmodel import Field, SQLModel, Relationship
from typing import List, Optional
from datetime import datetime
from enum import Enum
from app.models.album import AlbumEventLink

class Island(str, Enum):
    Trinidad = "Trinidad"
    Tobago = "Tobago"
    Barbados = "Barbados"
    Jamaica = "Jamaica"
    Antigua = "Antigua"
    St_Lucia = "St. Lucia"
    Grenada = "Grenada"
    St_Vincent = "St. Vincent"
    Dominica = "Dominica"
    St_Kitts = "St. Kitts"
    Bahamas = "Bahamas"
    Cayman_Islands = "Cayman Islands"
    Martinique = "Martinique"
    Guadeloupe = "Guadeloupe"
    Curacao = "Curaçao"
    Aruba = "Aruba"
    Puerto_Rico = "Puerto Rico"
    Haiti = "Haiti"
    Dominican_Republic = "Dominican Republic"
    Other = "Other"

class EventCategory(str, Enum):
    Music = "Music"
    Food_Drink = "Food & Drink"
    Sports = "Sports"
    Culture_Arts = "Culture & Arts"
    Nightlife = "Nightlife"
    Festival = "Festival"
    Carnival = "Carnival"
    Business = "Business"
    Other = "Other"

class EventStatus(str, Enum):
    draft = "draft"
    pending = "pending"
    published = "published"

class EventBase(SQLModel):
    title: str = Field(index=True)
    description: str
    island: Island
    venue: str
    date: datetime
    end_date: Optional[datetime] = None
    price: Optional[float] = None
    category: EventCategory = EventCategory.Other
    source_url: Optional[str] = None
    image_url: Optional[str] = None
    status: EventStatus = EventStatus.draft

class Event(EventBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_by: Optional[int] = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    albums: List["Album"] = Relationship(back_populates="events", link_model=AlbumEventLink)
    reviews: List["Review"] = Relationship(back_populates="event")
    photos: List["Photo"] = Relationship(back_populates="event")