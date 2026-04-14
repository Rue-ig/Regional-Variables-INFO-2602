# PATH: app/routers/submissions.py
from fastapi import Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from app.dependencies import SessionDep, AuthDep
from app.models.event import Event, Island, EventCategory, EventStatus
from sqlmodel import select
from . import router, templates
from datetime import datetime
from typing import Optional

def _island_values():
    return [i.value for i in Island]

def _category_values():
    return [c.value for c in EventCategory]

@router.get("/submissions", response_class=HTMLResponse)
async def submissions_page(request: Request, db: SessionDep, user: AuthDep):
    events = db.exec(
        select(Event)
        .where(Event.created_by == user.id)
        .order_by(Event.created_at.desc())
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="User/events/submissions.html",
        context={
            "events": events,
            "user": user,
            "islands": _island_values(),
            "categories": _category_values(),
        },
    )

@router.post("/submissions")
async def create_submission(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    title: str = Form(...),
    description: str = Form(...),
    island: str = Form(...),
    category: str = Form(...),
    venue: str = Form(...),
    date: str = Form(...),
    end_date: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    image_url: Optional[str] = Form(None),
    source_url: Optional[str] = Form(None),
):
    try:
        event = Event(
            title=title.strip(),
            description=description.strip(),
            island=Island(island),
            category=EventCategory(category),
            venue=venue.strip(),
            date=datetime.fromisoformat(date),
            end_date=datetime.fromisoformat(end_date) if end_date else None,
            price=price,
            image_url=image_url.strip() if image_url else None,
            source_url=source_url.strip() if source_url else None,
            created_by=user.id,
            status=EventStatus.pending,
        )
        db.add(event)
        db.commit()
        return RedirectResponse(url="/submissions", status_code=303)
        
    except Exception as e:
        print(f"Submission error: {e}")
        return RedirectResponse(url="/submissions?error=submission_failed", status_code=303)

@router.get("/submissions/{event_id}/edit", response_class=HTMLResponse)
async def edit_submission_view(request: Request, event_id: int, db: SessionDep, user: AuthDep):
    """Shows the edit form populated with current event data."""
    event = db.get(Event, event_id)
    
    if not event or event.created_by != user.id:
        return RedirectResponse(url="/submissions?error=not_found", status_code=303)
    
    return templates.TemplateResponse(
        request=request,
        name="User/events/edit_submission.html",
        context={
            "event": event,
            "user": user,
            "islands": _island_values(),
            "categories": _category_values(),
        },
    )

@router.post("/submissions/{event_id}/update")
async def update_submission(
    request: Request,
    event_id: int,
    db: SessionDep,
    user: AuthDep,
    title: str = Form(...),
    description: str = Form(...),
    island: str = Form(...),
    category: str = Form(...),
    venue: str = Form(...),
    date: str = Form(...),
    end_date: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    image_url: Optional[str] = Form(None),
    source_url: Optional[str] = Form(None),
):
    event = db.get(Event, event_id)
    if not event or event.created_by != user.id:
        return RedirectResponse(url="/submissions?error=not_found", status_code=303)

    try:
        event.title = title.strip()
        event.description = description.strip()
        event.island = Island(island)
        event.category = EventCategory(category)
        event.venue = venue.strip()
        event.date = datetime.fromisoformat(date)
        event.end_date = datetime.fromisoformat(end_date) if end_date else None
        event.price = price
        event.image_url = image_url.strip() if image_url else None
        event.source_url = source_url.strip() if source_url else None
        event.updated_at = datetime.utcnow()
        
        db.add(event)
        db.commit()
        return RedirectResponse(url="/submissions?message=updated", status_code=303)
        
    except Exception as e:
        print(f"Update error: {e}")
        return RedirectResponse(url=f"/submissions/{event_id}/edit?error=update_failed", status_code=303)

@router.post("/submissions/{event_id}/delete")
async def delete_submission(request: Request, event_id: int, db: SessionDep, user: AuthDep):
    event = db.get(Event, event_id)
    if not event or event.created_by != user.id:
        return RedirectResponse(url="/submissions?error=not_found", status_code=303)

    if event.status == EventStatus.published:
        return RedirectResponse(url="/submissions?error=cannot_delete_published", status_code=303)

    db.delete(event)
    db.commit()
    
    return RedirectResponse(url="/submissions", status_code=303)
