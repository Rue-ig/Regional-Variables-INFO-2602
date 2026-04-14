# PATH: app/routers/event_detail.py
from fastapi import Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from app.dependencies import SessionDep, UserDep
from app.repositories.event import EventRepository
from app.repositories.content import ReviewRepository, PhotoRepository, BookmarkRepository
from app.services.event_service import EventService
from app.services.content_service import ReviewService, PhotoService, BookmarkService
from app.models.album import Album, AlbumEventLink
from app.models.event_status import UserEventStatus
from app.models.review_vote import ReviewVote
from sqlalchemy.orm import selectinload
from sqlmodel import select
from . import router, templates

@router.get("/events/{event_id}", response_class=HTMLResponse)
async def event_detail(request: Request, event_id: int, db: SessionDep, user: UserDep):
    event = EventService(EventRepository(db)).get_published_or_404(event_id)
    review_svc = ReviewService(ReviewRepository(db))
    photo_svc = PhotoService(PhotoRepository(db))
    bookmark_svc = BookmarkService(BookmarkRepository(db))

    reviews = review_svc.get_for_event(event_id)
    avg_rating = review_svc.get_average_rating(event_id)
    photos = photo_svc.get_for_event(event_id)

    is_bookmarked = False
    already_reviewed = False
    user_albums = []
    user_status = None
    user_review_votes: dict[int, str] = {}

    if user:
        is_bookmarked = event_id in bookmark_svc.get_bookmarked_ids(user.id)
        already_reviewed = (
            ReviewRepository(db).get_by_user_and_event(user.id, event_id) is not None
        )
        
        user_albums = db.exec(
            select(Album)
            .where(Album.user_id == user.id)
            .options(selectinload(Album.events))
        ).all()

        status_row = db.exec(
            select(UserEventStatus).where(
                UserEventStatus.user_id == user.id,
                UserEventStatus.event_id == event_id,
            )
        ).first()
        user_status = status_row.status if status_row else None

        review_ids = [r.id for r in reviews]
        if review_ids:
            vote_rows = db.exec(
                select(ReviewVote).where(
                    ReviewVote.user_id == user.id,
                    ReviewVote.review_id.in_(review_ids),
                )
            ).all()
            user_review_votes = {v.review_id: v.vote for v in vote_rows}

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
            "user_albums": user_albums,
            "user_status": user_status,
            "user_review_votes": user_review_votes,
        },
    )

@router.post("/reviews/{review_id}/vote")
async def vote_review(
    request: Request,
    review_id: int,
    db: SessionDep,
    user: UserDep,
    vote: str = Form(...)
):
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    existing_vote = db.exec(
        select(ReviewVote).where(
            ReviewVote.user_id == user.id,
            ReviewVote.review_id == review_id
        )
    ).first()

    if existing_vote:
        if existing_vote.vote == vote:
            db.delete(existing_vote)
            
        else:
            existing_vote.vote = vote
            db.add(existing_vote)
    else:
        db.add(ReviewVote(user_id=user.id, review_id=review_id, vote=vote))

    db.commit()
    
    review_record = db.get(Review, review_id)
    if review_record:
        return RedirectResponse(url=f"/events/{review_record.event_id}", status_code=303)
        
    return RedirectResponse(url="/events", status_code=303)
