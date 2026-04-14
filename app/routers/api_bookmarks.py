# PATH: app/routers/api_bookmarks.py
from fastapi import Request
from fastapi.responses import JSONResponse
from app.dependencies import SessionDep, AuthDep
from app.repositories.content import BookmarkRepository
from app.services.content_service import BookmarkService
from . import api_router

@api_router.post("/bookmarks/toggle/{event_id}")
async def toggle_bookmark(event_id: int, db: SessionDep, user: AuthDep):
    svc = BookmarkService(BookmarkRepository(db))
    bookmarked = svc.toggle(user.id, event_id)
    return JSONResponse({"bookmarked": bookmarked})
