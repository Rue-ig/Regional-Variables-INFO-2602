# PATH: app/services/event_service.py
from app.repositories.event import EventRepository
from app.schemas.event import EventCreate, EventUpdate, EventFilter
from app.models.event import Event, EventStatus
from typing import Optional
from fastapi import HTTPException, status

class EventService:
    def __init__(self, repo: EventRepository):
        self.repo = repo

    def get_event_or_404(self, event_id: int) -> Event:
        event = self.repo.get_by_id(event_id)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        
        return event

    def get_published_or_404(self, event_id: int) -> Event:
        event = self.get_event_or_404(event_id)
        
        if event.status != EventStatus.published:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        
        return event

    def browse(self, filters: Optional[EventFilter] = None, page: int = 1, per_page: int = 20):
        offset = (page - 1) * per_page
        events = self.repo.get_all_published(filters=filters, offset=offset, limit=per_page)
        total = self.repo.count_published(filters=filters)
        total_pages = (total + per_page - 1) // per_page
        
        return events, total, total_pages

    def get_all_for_map(self) -> list[Event]:
        return self.repo.get_all_published(limit=500)

    def create(self, data: EventCreate, user_id: Optional[int] = None) -> Event:
        return self.repo.create(data, user_id=user_id)

    def update(self, event_id: int, data: EventUpdate) -> Event:
        event = self.get_event_or_404(event_id)
        
        return self.repo.update(event, data)

    def delete(self, event_id: int) -> None:
        event = self.get_event_or_404(event_id)
        self.repo.delete(event)

    def publish(self, event_id: int) -> Event:
        event = self.get_event_or_404(event_id)
        
        return self.repo.set_status(event, EventStatus.published)

    def unpublish(self, event_id: int) -> Event:
        event = self.get_event_or_404(event_id)
        
        return self.repo.set_status(event, EventStatus.draft)

    def get_admin_list(self, page: int = 1, per_page: int = 50) -> list[Event]:
        offset = (page - 1) * per_page
        return self.repo.get_all_admin(offset=offset, limit=per_page)

    def get_total_count(self) -> int:
        return self.repo.count_all()
    
    def get_weekly_approved(self) -> int:
        return self.repo.count_weekly_approved()

    def get_pending(self) -> list[Event]:
        return self.repo.get_pending()
