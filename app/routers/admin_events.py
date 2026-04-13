# PATH: app/routers/admin_events.py
from fastapi import Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
from datetime import datetime
from app.dependencies.session import SessionDep
from app.dependencies.auth import AdminDep
from app.repositories.event import EventRepository
from app.services.event_service import EventService
from app.schemas.event import EventCreate, EventUpdate
from app.models.event import Island, EventCategory, EventStatus
from app.utilities.flash import flash
from sqlalchemy import func, distinct, cast, Date
from datetime import datetime, timedelta, timezone
from app.models.visitors import Visit
from . import router, templates

def _event_form_context():
    return {
        "islands": list(Island),
        "categories": list(EventCategory),
        "statuses": list(EventStatus),
    }

@router.get("/admin/events", response_class=HTMLResponse)
async def admin_events_list(request: Request, db: SessionDep, admin: AdminDep):
    service = EventService(EventRepository(db))
    
    total_visitors = db.query(func.count(distinct(Visit.session_id))).scalar() or 0
    
    chart_labels = []
    chart_data = []
    
    for i in range(6, -1, -1):
        date_target = datetime.now(timezone.utc).date() - timedelta(days=i)
        
        daily_unique = db.query(func.count(distinct(Visit.session_id))).filter(
            cast(Visit.timestamp, Date) == date_target
        ).scalar()
        
        chart_labels.append(date_target.strftime("%a"))
        chart_data.append(daily_unique or 0)

    stats = {
        "total_events": service.get_total_count(),
        "total_visitors": total_visitors,
        "approved_this_week": service.get_weekly_approved(),
        "total_reports": 0,
        "pending_photos": 0,
        "pending_reviews": 0
    }
    
    return templates.TemplateResponse(
        request=request,
        name="Admin/events/events.html",
        context={
            "user": admin, 
            "events": service.get_admin_list(), 
            "stats": stats,
            "chart_labels": chart_labels,
            "chart_data": chart_data
        }
    )

@router.get("/admin/events/new", response_class=HTMLResponse)
async def admin_event_new(request: Request, db: SessionDep, admin: AdminDep):
    return templates.TemplateResponse(
        request=request,
        name="Admin/events/event_form.html",
        context={"user": admin,"event": None, **_event_form_context()},
    )

@router.post("/admin/events/new")
async def admin_event_create(
    request: Request,
    db: SessionDep,
    admin: AdminDep,
    title: str = Form(...),
    description: str = Form(...),
    island: str = Form(...),
    venue: str = Form(...),
    date: str = Form(...),
    end_date: str = Form(None),
    price: str = Form(None),
    category: str = Form(...),
    source_url: str = Form(None),
    image_url: str = Form(None),
    status: str = Form("draft"),
):
    try:
        clean_price = float(price) if (price and price.strip()) else 0.0

        data = EventCreate(
            title=title,
            description=description,
            island=island, 
            venue=venue,
            date=datetime.fromisoformat(date),
            end_date=datetime.fromisoformat(end_date) if end_date else None,
            price=clean_price,
            category=category,
            source_url=source_url if source_url else None,
            image_url=image_url if image_url else None,
            status=status,
        )

        service = EventService(EventRepository(db))
        service.create(data, user_id=admin.id)
        
        flash(request, f"Successfully created '{title}'", "success")
        
        return RedirectResponse(url="/admin/events", status_code=303)

    except ValueError as e:
        flash(request, f"Data Error: {str(e)}", "danger")
        
        return templates.TemplateResponse(
            "Admin/events/event_form.html", 
            {"request": request, "user": admin, "event": None, **_event_form_context()}
        )
        
    except Exception as e:
        flash(request, f"An unexpected error occurred: {str(e)}", "danger")
        
        return RedirectResponse(url="/admin/events/new", status_code=303)

@router.get("/admin/events/{event_id}/edit", response_class=HTMLResponse)
async def admin_event_edit(request: Request, event_id: int, db: SessionDep, admin: AdminDep):
    event = EventService(EventRepository(db)).get_event_or_404(event_id)
    return templates.TemplateResponse(
        request=request,
        name="Admin/events/event_form.html",
        context={"user": admin, "event": event, **_event_form_context()},
    )

@router.post("/admin/events/{event_id}/edit")
async def admin_event_update(
    request: Request,
    event_id: int,
    db: SessionDep,
    admin: AdminDep,
    title: str = Form(...),
    description: str = Form(...),
    island: str = Form(...),
    venue: str = Form(...),
    date: str = Form(...),
    end_date: str = Form(""),
    price: str = Form(""),
    category: str = Form(...),
    source_url: str = Form(""),
    image_url: str = Form(""),
    status: str = Form("draft"),
):
    data = EventUpdate(
        title=title, description=description, island=island, venue=venue,
        date=datetime.fromisoformat(date),
        end_date=datetime.fromisoformat(end_date) if end_date else None,
        price=float(price) if price else None,
        category=category, source_url=source_url or None,
        image_url=image_url or None, status=status,
    )
    EventService(EventRepository(db)).update(event_id, data)
    flash(request, "Event updated.", "success")
    
    return RedirectResponse(url="/admin/events", status_code=303)

@router.post("/admin/events/{event_id}/delete")
async def admin_event_delete(request: Request, event_id: int, db: SessionDep, admin: AdminDep):
    EventService(EventRepository(db)).delete(event_id)
    flash(request, "Event deleted.", "info")
    
    return RedirectResponse(url="/admin/events", status_code=303)

@router.post("/admin/events/{event_id}/publish")
async def admin_event_publish(request: Request, event_id: int, db: SessionDep, admin: AdminDep):
    EventService(EventRepository(db)).publish(event_id)
    flash(request, "Event published.", "success")
    
    return RedirectResponse(url="/admin/events", status_code=303)

@router.post("/admin/events/{event_id}/unpublish")
async def admin_event_unpublish(request: Request, event_id: int, db: SessionDep, admin: AdminDep):
    EventService(EventRepository(db)).unpublish(event_id)
    flash(request, "Event unpublished.", "info")
    
    return RedirectResponse(url="/admin/events", status_code=303)