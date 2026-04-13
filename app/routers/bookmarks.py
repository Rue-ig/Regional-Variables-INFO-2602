# PATH: app/routers/bookmarks.py
from fastapi import Request
from fastapi.responses import HTMLResponse
from app.dependencies import SessionDep, AuthDep
from app.repositories.content import BookmarkRepository
from app.models.event import Event
from app.models.bookmark import Bookmark
from app.models.photo import Photo
from app.models.review import Review
from app.models.album import Album
from sqlmodel import select
from . import router, templates

@router.get("/bookmarks", response_class=HTMLResponse)
async def bookmarks_page(request: Request, db: SessionDep, user: AuthDep):
    event_statement = (
        select(Event)
        .join(Bookmark)
        .where(Bookmark.user_id == user.id)
    )
    events = db.exec(event_statement).all()

    user_photos = db.exec(select(Photo).where(Photo.user_id == user.id)).all()
    user_reviews = db.exec(select(Review).where(Review.user_id == user.id)).all()
    user_albums = db.exec(select(Album).where(Album.user_id == user.id)).all()

    return templates.TemplateResponse(
        request=request,
        name="User/events/bookmarks.html",
        context={
            "events": events,
            "user": user,
            "total_photos": len(user_photos),
            "total_reviews": len(user_reviews),
            "total_albums": len(user_albums),
            "recent_photos": user_photos[:5]
        },
    )