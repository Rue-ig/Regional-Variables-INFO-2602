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
async def submissions_page(
    request: Request, 
    db: SessionDep, 
    user: AuthDep
):
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
        try:
            island_enum = Island(island)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid island: {island}")

        try:
            category_enum = EventCategory(category)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

        try:
            event_date = datetime.fromisoformat(date)
            event_end_date = datetime.fromisoformat(end_date) if end_date else None
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Please use the date picker.")

        event = Event(
            title=title.strip(),
            description=description.strip(),
            island=island_enum,
            category=category_enum,
            venue=venue.strip(),
            date=event_date,
            end_date=event_end_date,
            price=price,
            image_url=image_url.strip() if image_url else None,
            source_url=source_url.strip() if source_url else None,
            created_by=user.id,
            status=EventStatus.pending,
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        return RedirectResponse(url="/submissions", status_code=303)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Submission error: {e}")
        return RedirectResponse(
            url="/submissions?error=submission_failed", 
            status_code=303
        )

@router.post("/submissions/{event_id}/delete")
async def delete_submission(
    request: Request,
    event_id: int,
    db: SessionDep,
    user: AuthDep,
):
    event = db.get(Event, event_id)
    
    if not event or event.created_by != user.id:
        return RedirectResponse(url="/submissions?error=not_found", status_code=303)

    if event.status == EventStatus.published:
        return RedirectResponse(
            url="/submissions?error=cannot_delete_published", 
            status_code=303
        )

    db.delete(event)
    db.commit()

    return RedirectResponse(url="/submissions", status_code=303)
