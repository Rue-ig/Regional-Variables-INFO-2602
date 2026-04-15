from fastapi import Request, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from app.dependencies.session import SessionDep
from app.dependencies.auth import AuthDep
from datetime import datetime
import json
from app.repositories.event import EventRepository
from app.services.event_service import EventService
from app.schemas.event import EventFilter
from app.models.event import Island, EventCategory, Event
from app.schemas.event import EventCreate
from app.models.album import Album, AlbumEventLink
from app.models.review import Review
from app.models.photo import Photo
from sqlmodel import select
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
    price_range: str = "",
    page: int = 1,
):
    if user.role == "admin":
        return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

    resolved_min = float(min_price) if min_price else None
    resolved_max = float(max_price) if max_price else None

    if price_range == "free":
        resolved_min, resolved_max = None, 0.0
        
    elif price_range == "paid":
        resolved_min = 0.01

    filters = EventFilter(
        island=island or None,
        category=category or None,
        keyword=keyword or None,
        date_from=datetime.fromisoformat(date_from) if date_from else None,
        date_to=datetime.fromisoformat(date_to) if date_to else None,
        min_price=resolved_min,
        max_price=resolved_max,
        price_range=price_range or None,
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
                "price_range": price_range,
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
            "id": e.id, 
            "title": e.title, 
            "island": e.island.value,
            "venue": e.venue, 
            "date": e.date.isoformat(),
            "price": e.price, 
            "category": e.category.value,
        }
        for e in events
    ])
    
    return templates.TemplateResponse(
        request=request,
        name="User/events/map.html",
        context={"user": user, "events_json": events_json},
    )

@router.get("/events/{event_id}", response_class=HTMLResponse)
async def event_detail(
    request: Request,
    event_id: int,
    db: SessionDep,
    user: AuthDep,
):
    event = db.get(Event, event_id)
    if not event:
        return RedirectResponse(url="/events", status_code=303)
    
    photos = db.exec(select(Photo).where(Photo.event_id == event_id)).all()
    
    reviews = db.exec(select(Review).where(Review.event_id == event_id)).all()
    
    avg_rating = None
    if reviews:
        total = sum(r.rating for r in reviews)
        avg_rating = round(total / len(reviews), 1)
    
    albums = db.exec(select(Album).where(Album.user_id == user.id)).all()
    albums_with_event = set()
    
    if user:
        albums = db.exec(
            select(Album).where(Album.user_id == user.id).order_by(Album.created_at.desc())
        ).all()
        
        for album in albums:
            link = db.exec(
                select(AlbumEventLink).where(
                    AlbumEventLink.album_id == album.id,
                    AlbumEventLink.event_id == event.id
                )
            ).first()
            if link:
                albums_with_event.add(album.id)
    
    already_reviewed = False
    if user and reviews:
        existing_review = db.exec(
            select(Review).where(
                Review.event_id == event_id,
                Review.user_id == user.id
            )
        ).first()
        already_reviewed = existing_review is not None
    
    is_bookmarked = False
    user_status = None
    
    return templates.TemplateResponse(
        request=request,
        name="User/events/detail.html",
        context={
            "request": request,
            "user": user,
            "event": event,
            "photos": photos,
            "reviews": reviews,
            "avg_rating": avg_rating,
            "already_reviewed": already_reviewed,
            "is_bookmarked": is_bookmarked,
            "user_status": user_status,
            "albums": albums,
            "albums_with_event": albums_with_event,
        },
    )

@router.post("/submissions", response_class=HTMLResponse)
async def user_event_create(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    title: str = Form(...),
    description: str = Form(...),
    island: str = Form(...),
    venue: str = Form(...),
    event_date: str = Form(...),
    event_time: str = Form(...),
    end_date_only: str = Form(""),
    end_time_only: str = Form(""),
    price: str = Form(""),
    category: str = Form(...),
    source_url: str = Form(""),
    image_url: str = Form(""),
    status: str = "pending"
):
    try:
        start_dt = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return RedirectResponse(url="/user/events/submissions?error=invalid_date", status_code=303)

    end_dt = None
    if end_date_only and end_time_only:
        try:
            end_dt = datetime.strptime(f"{end_date_only} {end_time_only}", "%Y-%m-%d %H:%M")
        except ValueError:
            pass

    data = EventCreate(
        title=title,
        description=description,
        island=island,
        venue=venue,
        date=start_dt,
        end_date=end_dt,
        price=float(price) if price else None,
        category=category,
        source_url=source_url or None,
        image_url=image_url or None,
        status=status,
    )
    
    EventService(EventRepository(db)).create(data, user_id=user.id)
    return RedirectResponse(url="/user/events/submissions", status_code=303)
    
@router.get("/user/events/submissions", response_class=HTMLResponse)
async def user_event_submissions(request: Request, db: SessionDep, user: AuthDep):
    events = EventService(EventRepository(db)).repo.get_by_user(user.id)
    return templates.TemplateResponse(
        request=request,
        name="User/events/submissions.html",
        context={
            "user": user,
            "events": events,
            "islands": [i.value for i in Island],
            "categories": [c.value for c in EventCategory]
        }
    )
