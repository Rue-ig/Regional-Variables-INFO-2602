# PATH: app/repositories/event.py
from sqlmodel import Session, select, func
from sqlalchemy.orm import selectinload
from app.models.event import Event, EventStatus
from app.schemas.event import EventCreate, EventUpdate, EventFilter
from typing import Optional
from datetime import datetime, timedelta, timezone

class EventRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, event_id: int) -> Optional[Event]:
        statement = (
            select(Event)
            .where(Event.id == event_id)
            .options(
                selectinload(Event.reviews), 
                selectinload(Event.photos)
            )
        )
        
        return self.session.exec(statement).first()
    
    def get_by_user(self, user_id: int) -> list[Event]:
        query = select(Event).where(Event.created_by == user_id).order_by(Event.created_at.desc())
        return self.session.exec(query).all()

    def _apply_filters(self, query, filters: Optional[EventFilter]):
        if not filters:
            return query
            
        if filters.island:
            query = query.where(Event.island == filters.island)
            
        if filters.category:
            query = query.where(Event.category == filters.category)
            
        if filters.date_from:
            query = query.where(Event.date >= filters.date_from)
            
        if filters.date_to:
            query = query.where(Event.date <= filters.date_to)
            
        if filters.min_price is not None:
            query = query.where(Event.price >= filters.min_price)
            
        if filters.max_price is not None:
            query = query.where(Event.price <= filters.max_price)
        if filters.keyword:
            kw = f"%{filters.keyword}%"
            query = query.where(
                Event.title.ilike(kw) | 
                Event.description.ilike(kw) | 
                Event.venue.ilike(kw)
            )
            
        return query

    def get_all_published(self, filters: Optional[EventFilter] = None, offset: int = 0, limit: int = 20) -> list[Event]:
        query = select(Event).where(Event.status == EventStatus.published)
        query = self._apply_filters(query, filters)
        query = query.order_by(Event.date).offset(offset).limit(limit)
        
        return self.session.exec(query).all()

    def count_published(self, filters: Optional[EventFilter] = None) -> int:
        query = select(func.count(Event.id)).where(Event.status == EventStatus.published)
        query = self._apply_filters(query, filters)
        
        return self.session.exec(query).one()

    def get_all_admin(self, offset: int = 0, limit: int = 50) -> list[Event]:
        query = select(Event).order_by(Event.created_at.desc()).offset(offset).limit(limit)
        return self.session.exec(query).all()

    def get_pending(self) -> list[Event]:
        query = select(Event).where(Event.status == EventStatus.pending).order_by(Event.created_at.desc())
        return self.session.exec(query).all()

    def create(self, data: EventCreate, user_id: Optional[int] = None) -> Event:
        event = Event(**data.model_dump(), created_by=user_id)
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        
        return event

    def update(self, event: Event, data: EventUpdate) -> Event:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(event, key, value)
        event.updated_at = datetime.now(timezone.utc)
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        
        return event

    def delete(self, event: Event) -> None:
        self.session.delete(event)
        self.session.commit()

    def set_status(self, event: Event, status: EventStatus) -> Event:
        event.status = status
        event.updated_at = datetime.now(timezone.utc)
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        
        return event
        
    def count_all(self) -> int:
        return self.session.exec(select(func.count(Event.id))).one()
    
    def count_weekly_approved(self) -> int:
        since = datetime.now(timezone.utc) - timedelta(days=7)
        
        return self.session.exec(
            select(func.count(Event.id)).where(
                Event.status == EventStatus.published,
                Event.updated_at >= since
            )
        ).one()
        
    def upsert_from_scrape(self, data: EventCreate) -> Event:
        existing = self.session.exec(
            select(Event).where(
                Event.title == data.title,
                Event.date == data.date,
                Event.island == data.island,
            )
        ).first()
        
        return existing if existing else self.create(data)
