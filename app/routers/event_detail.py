# PATH: app/routers/event_detail.py
from fastapi import Request
from fastapi.responses import HTMLResponse
from app.dependencies import SessionDep, UserDep
from app.repositories.event import EventRepository
from app.repositories.content import ReviewRepository, PhotoRepository, BookmarkRepository
from app.services.event_service import EventService
from app.services.content_service import ReviewService, PhotoService, BookmarkService
from . import router, templates


@router.get("/events/{event_id}", response_class=HTMLResponse)
async def event_detail(
    request: Request,
    event_id: int,
    db: SessionDep,
    user: UserDep
):
    event = EventService(EventRepository(db)).get_published_or_404(event_id)
    review_svc = ReviewService(ReviewRepository(db))
    photo_svc = PhotoService(PhotoRepository(db))
    bookmark_svc = BookmarkService(BookmarkRepository(db))

    reviews = review_svc.get_for_event(event_id)
    avg_rating = review_svc.get_average_rating(event_id)
    photos = photo_svc.get_for_event(event_id)

    is_bookmarked = False
    already_reviewed = False
    
    if user:
        is_bookmarked = event_id in bookmark_svc.get_bookmarked_ids(user.id)
        already_reviewed = ReviewRepository(db).get_by_user_and_event(user.id, event_id) is not None

    return templates.TemplateResponse(
        request=request,
        name="User/events/detail.html",
        context={
            "event": event,
            "reviews": reviews,
            "avg_rating": avg_rating,
            "photos": photos,
            "is_bookmarked": is_bookmarked,
            "already_reviewed": already_reviewed,
            "user": user,
        },
    )