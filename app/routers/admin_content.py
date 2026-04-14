# PATH: app/routers/admin_content.py
from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from app.dependencies.session import SessionDep
from app.dependencies.auth import AdminDep
from app.repositories.content import ReviewRepository, PhotoRepository
from app.repositories.event import EventRepository
from app.services.content_service import ReviewService, PhotoService
from app.services.event_service import EventService
from app.utilities.flash import flash
from . import router, templates

@router.get("/admin/content", response_class=HTMLResponse)
async def admin_content(request: Request, db: SessionDep, admin: AdminDep):
    pending_reviews = ReviewService(ReviewRepository(db)).get_pending()
    pending_photos  = PhotoService(PhotoRepository(db)).get_pending()
    pending_events  = EventService(EventRepository(db)).get_pending()
    
    return templates.TemplateResponse(
        request=request,
        name="Admin/events/content.html",
        context={
            "user":            admin,
            "pending_reviews": pending_reviews,
            "pending_photos":  pending_photos,
            "pending_events":  pending_events,
        },
    )

@router.post("/admin/reviews/{review_id}/approve")
async def approve_review(request: Request, review_id: int, db: SessionDep, admin: AdminDep):
    ReviewService(ReviewRepository(db)).approve(review_id)
    flash(request, "Review approved.", "success")
    
    return RedirectResponse(url="/admin/content", status_code=303)

@router.post("/admin/reviews/{review_id}/delete")
async def delete_review(request: Request, review_id: int, db: SessionDep, admin: AdminDep):
    ReviewService(ReviewRepository(db)).delete(review_id)
    flash(request, "Review deleted.", "info")
    
    return RedirectResponse(url="/admin/content", status_code=303)

@router.post("/admin/photos/{photo_id}/approve")
async def approve_photo(request: Request, photo_id: int, db: SessionDep, admin: AdminDep):
    PhotoService(PhotoRepository(db)).approve(photo_id)
    flash(request, "Photo approved.", "success")
    
    return RedirectResponse(url="/admin/content", status_code=303)

@router.post("/admin/photos/{photo_id}/delete")
async def delete_photo(request: Request, photo_id: int, db: SessionDep, admin: AdminDep):
    PhotoService(PhotoRepository(db)).delete(photo_id)
    flash(request, "Photo deleted.", "info")
    
    return RedirectResponse(url="/admin/content", status_code=303)

@router.post("/admin/events/{event_id}/publish")
async def publish_event(request: Request, event_id: int, db: SessionDep, admin: AdminDep):
    EventService(EventRepository(db)).publish(event_id)
    flash(request, "Event published.", "success")
    
    return RedirectResponse(url="/admin/content", status_code=303)

@router.post("/admin/events/{event_id}/delete")
async def delete_pending_event(request: Request, event_id: int, db: SessionDep, admin: AdminDep):
    EventService(EventRepository(db)).delete(event_id)
    flash(request, "Event deleted.", "info")
    
    return RedirectResponse(url="/admin/content", status_code=303)
