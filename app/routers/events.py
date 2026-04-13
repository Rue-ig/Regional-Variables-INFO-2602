# PATH: app/routers/events.py
from fastapi import Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from app.dependencies.session import SessionDep
from app.dependencies.auth import AuthDep
from datetime import datetime
import json
from app.repositories.event import EventRepository
from app.services.event_service import EventService
from app.schemas.event import EventFilter
from app.models.event import Island, EventCategory
from . import router, templates


@router.get("/events", response_class=HTMLResponse)
async def events_index(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    island: str = "",
    category: str = "",
    keyword: str = "",
    date_from: str = "",
    date_to: str = "",
    min_price: str = "",
    max_price: str = "",
    page: int = 1,
):
    if user.role == "admin":
        return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

    filters = EventFilter(
        island=island or None,
        category=category or None,
        keyword=keyword or None,
        date_from=datetime.fromisoformat(date_from) if date_from else None,
        date_to=datetime.fromisoformat(date_to) if date_to else None,
        min_price=float(min_price) if min_price else None,
        max_price=float(max_price) if max_price else None,
    )

    service = EventService(EventRepository(db))
    events, total, total_pages = service.browse(filters=filters, page=page, per_page=100)

    return templates.TemplateResponse(
        request=request,
        name="User/events/index.html",
        context={
            "user": user,
            "events": events,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "islands": [i.value for i in Island],
            "categories": [c.value for c in EventCategory],
            "filters": {
                "island": island, "category": category, "keyword": keyword,
                "date_from": date_from, "date_to": date_to,
                "min_price": min_price, "max_price": max_price,
            },
        },
    )

@router.get("/events/map", response_class=HTMLResponse)
async def events_map(request: Request, user: AuthDep, db: SessionDep):
    if user.role == "admin":
        return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

    service = EventService(EventRepository(db))
    events = service.get_all_for_map()

    events_json = json.dumps([
        {
            "id": e.id, "title": e.title, "island": e.island.value,
            "venue": e.venue, "date": e.date.isoformat(),
            "price": e.price, "category": e.category.value,
        }
        for e in events
    ])
    
    return templates.TemplateResponse(
        request=request,
        name="User/events/map.html",
        context={"user": user, "events_json": events_json},
    )