# PATH: app/routers/bookmarks.py
from fastapi import Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from app.dependencies import SessionDep, AuthDep
from app.models.event import Event
from app.models.bookmark import Bookmark
from app.models.photo import Photo
from app.models.review import Review
from app.models.album import Album, AlbumEventLink
from app.models.event_status import UserEventStatus
from app.models.report import Report
from sqlmodel import select
from . import router, templates
import random

@router.get("/bookmarks", response_class=HTMLResponse)
async def bookmarks_page(request: Request, db: SessionDep, user: AuthDep):
    events = db.exec(
        select(Event).join(Bookmark).where(Bookmark.user_id == user.id)
    ).all()
    user_photos = db.exec(select(Photo).where(Photo.user_id == user.id)).all()
    user_reviews = db.exec(select(Review).where(Review.user_id == user.id)).all()
    user_albums = db.exec(select(Album).where(Album.user_id == user.id)).all()
    user_statuses = db.exec(
        select(UserEventStatus).where(UserEventStatus.user_id == user.id)
    ).all()
    status_map = {s.event_id: s.status for s in user_statuses}

    for r in user_reviews:
        r._event_title = r.event.title if r.event else "Unknown Event"

    return templates.TemplateResponse(
        request=request,
        name="User/events/bookmarks.html",
        context={
            "events": events,
            "user": user,
            "user_photos": user_photos,
            "user_reviews": user_reviews,
            "user_albums": user_albums,
            "total_photos": len(user_photos),
            "total_reviews": len(user_reviews),
            "total_albums": len(user_albums),
            "status_map": status_map,
        },
    )


@router.post("/bookmarks/status/{event_id}")
async def set_event_status(
    request: Request,
    event_id: int,
    db: SessionDep,
    user: AuthDep,
    status: str = Form(...),
):
    existing = db.exec(
        select(UserEventStatus)
        .where(UserEventStatus.user_id == user.id, UserEventStatus.event_id == event_id)
    ).first()
    if existing:
        if existing.status == status:
            db.delete(existing)
        else:
            existing.status = status
            db.add(existing)
    else:
        db.add(UserEventStatus(user_id=user.id, event_id=event_id, status=status))
    db.commit()

    referer = request.headers.get("referer", "/bookmarks")
    return RedirectResponse(url=referer, status_code=303)


@router.post("/albums/create")
async def create_album(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    name: str = Form(...),
    description: str = Form(""),
):
    album = Album(name=name, description=description, user_id=user.id)
    db.add(album)
    db.commit()
    db.refresh(album)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JSONResponse({"album_id": album.id, "name": album.name})

    return RedirectResponse(url="/bookmarks", status_code=303)

@router.post("/albums/{album_id}/add-event/{event_id}")
async def add_event_to_album(
    request: Request,
    album_id: int,
    event_id: int,
    db: SessionDep,
    user: AuthDep,
):
    album = db.get(Album, album_id)
    if not album or album.user_id != user.id:
        return JSONResponse({"detail": "Album not found"}, status_code=404)

    existing = db.exec(
        select(AlbumEventLink)
        .where(AlbumEventLink.album_id == album_id, AlbumEventLink.event_id == event_id)
    ).first()
    if not existing:
        db.add(AlbumEventLink(album_id=album_id, event_id=event_id))
        db.commit()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JSONResponse({"ok": True})

    return RedirectResponse(url="/bookmarks", status_code=303)

@router.post("/albums/{album_id}/remove-event/{event_id}")
async def remove_event_from_album(
    request: Request,
    album_id: int,
    event_id: int,
    db: SessionDep,
    user: AuthDep,
):
    album = db.get(Album, album_id)
    if not album or album.user_id != user.id:
        return JSONResponse({"detail": "Album not found"}, status_code=404)

    link = db.exec(
        select(AlbumEventLink)
        .where(AlbumEventLink.album_id == album_id, AlbumEventLink.event_id == event_id)
    ).first()
    if link:
        db.delete(link)
        db.commit()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JSONResponse({"ok": True})

    return RedirectResponse(url=f"/albums/{album_id}", status_code=303)

@router.post("/albums/{album_id}/delete")
async def delete_album(
    request: Request,
    album_id: int,
    db: SessionDep,
    user: AuthDep,
):
    album = db.get(Album, album_id)
    if not album or album.user_id != user.id:
        return JSONResponse({"detail": "Album not found"}, status_code=404)

    links = db.exec(
        select(AlbumEventLink).where(AlbumEventLink.album_id == album_id)
    ).all()
    for link in links:
        db.delete(link)

    db.delete(album)
    db.commit()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JSONResponse({"ok": True})

    referer = request.headers.get("referer", "/bookmarks")
    return RedirectResponse(url=referer, status_code=303)

@router.post("/reports/{item_type}/{item_id}")
async def submit_report(
    request: Request,
    item_type: str,
    item_id: int,
    db: SessionDep,
    user: AuthDep,
):
    if item_type not in ("review", "photo", "event"):
        return JSONResponse({"detail": "Invalid report type"}, status_code=400)

    body = await request.json()
    reason = body.get("reason", "").strip()
    details = body.get("details", "").strip()

    if not reason:
        return JSONResponse({"detail": "Reason is required"}, status_code=422)

    report = Report(
        user_id=user.id,
        reason=reason,
        details=details,
    )
    
    if item_type == "photo":
        report.photo_id = item_id
        
    elif item_type == "review":
        report.review_id = item_id
        
    db.add(report)
    db.commit()

    return JSONResponse({"ok": True})
