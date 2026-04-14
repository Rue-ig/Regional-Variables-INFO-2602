# PATH: app/routers/index.py
from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import select
from sqlalchemy import desc
from app.dependencies.auth import UserDep
from app.dependencies.session import SessionDep
from app.repositories.event import EventRepository
from app.services.event_service import EventService
from app.models.review import Review
from app.models.user import User
from app.models.event import Event
from . import router, templates

@router.get("/", response_class=HTMLResponse)
async def index_view(request: Request, db: SessionDep, user: UserDep = None):
    if user and user.role == "admin":
        return RedirectResponse(url=request.url_for('admin_home_view'), status_code=303)

    service = EventService(EventRepository(db))
    featured_events, _, _ = service.browse(page=1, per_page=6)

    highest_rated = db.exec(select(Event).order_by(desc(Event.rating)).limit(6)).all()

    raw_reviews = db.exec(
        select(Review)
        .where(Review.approved == True)
        .order_by(desc(Review.rating), desc(Review.created_at))
        .limit(6)
    ).all()

    user_ids  = list({r.user_id  for r in raw_reviews})
    event_ids = list({r.event_id for r in raw_reviews})

    users  = {u.id: u for u in db.exec(select(User) .where(User.id .in_(user_ids ))).all()}
    events = {e.id: e for e in db.exec(select(Event).where(Event.id.in_(event_ids))).all()}

    featured_reviews = []
    for r in raw_reviews:
        owner = users.get(r.user_id)
        ev    = events.get(r.event_id)
        featured_reviews.append({
            "id":          r.id,
            "rating":      r.rating,
            "body":        r.body,
            "created_at":  r.created_at,
            "event_id":    r.event_id,
            "username":    owner.username if owner else "Member",
            "event_title": ev.title       if ev    else None,
            "event_date":  ev.date        if ev    else None,
            "highest_rated": highest_rated      if ev    else None,
        })

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "request":         request,
            "user":            user,
            "featured_events": featured_events,
            "featured_reviews": featured_reviews,
        },
    )