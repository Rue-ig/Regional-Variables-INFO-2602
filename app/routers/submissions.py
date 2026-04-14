# PATH: app/routers/submissions.py
from fastapi import Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from app.dependencies import SessionDep, AuthDep
from app.models.event import Event, Island, EventCategory
from sqlmodel import select
from . import router, templates

def _island_values():
    """Return display strings for all islands."""
    return [i.value for i in IslandEnum]

def _category_values():
    """Return display strings for all categories."""
    return [c.value for c in CategoryEnum]

@router.get("/submissions", response_class=HTMLResponse)
async def submissions_page(request: Request, db: SessionDep, user: AuthDep):
    events = db.exec(
        select(Event).where(Event.submitted_by == user.id).order_by(Event.created_at.desc())
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
    end_date: str = Form(None),
    price: float = Form(None),
    image_url: str = Form(None),
    source_url: str = Form(None),
):
    from datetime import datetime

    event = Event(
        title=title,
        description=description,
        island=island,
        category=category,
        venue=venue,
        date=datetime.fromisoformat(date),
        end_date=datetime.fromisoformat(end_date) if end_date else None,
        price=price,
        image_url=image_url or None,
        source_url=source_url or None,
        submitted_by=user.id,
        status="pending",
    )
    db.add(event)
    db.commit()

    return RedirectResponse(url="/submissions", status_code=303)

@router.post("/submissions/{event_id}/delete")
async def delete_submission(
    request: Request,
    event_id: int,
    db: SessionDep,
    user: AuthDep,
):
    event = db.get(Event, event_id)
    if not event or event.submitted_by != user.id:
        return JSONResponse({"detail": "Not found"}, status_code=404)

    if event.status == "published":
        return RedirectResponse(url="/submissions?error=cannot_delete_published", status_code=303)

    db.delete(event)
    db.commit()
    return RedirectResponse(url="/submissions", status_code=303)
