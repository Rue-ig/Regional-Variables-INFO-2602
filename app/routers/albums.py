# PATH: app/routers/albums.py
from fastapi import Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from app.dependencies import SessionDep, AuthDep
from app.models.album import Album, AlbumEventLink
from app.models.event import Event
from app.utilities.flash import flash
from sqlmodel import select
from . import router, templates

@router.post("/albums/create")
async def create_album(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    name: str = Form(...),
    description: str = Form(""),
):
    album = Album(
        name=name.strip(),
        description=description.strip() or None,
        user_id=user.id,
    )
    db.add(album)
    db.commit()
    flash(request, f'Album "{name}" created!', "success")
  
    return RedirectResponse(url=request.headers.get("referer", "/bookmarks"), status_code=303)

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
        flash(request, "Album not found.", "error")
      
    existing = db.exec(
        select(AlbumEventLink).where(
            AlbumEventLink.album_id == album_id,
            AlbumEventLink.event_id == event_id,
        )
    ).first()

    if not existing:
        db.add(AlbumEventLink(album_id=album_id, event_id=event_id))
        db.commit()
        flash(request, f'Event added to "{album.name}".', "success")
      
    else:
        flash(request, "Event is already in that album.", "info")

    return RedirectResponse(url=request.headers.get("referer", f"/events/{event_id}"), status_code=303)

@router.get("/albums/{album_id}", response_class=HTMLResponse)
async def view_album(
    request: Request,
    album_id: int,
    db: SessionDep,
    user: AuthDep,
):
    album = db.get(Album, album_id)
    if not album or album.user_id != user.id:
        flash(request, "Album not found.", "error")
      
        return RedirectResponse(url="/bookmarks", status_code=303)

    links = db.exec(
        select(AlbumEventLink).where(AlbumEventLink.album_id == album_id)
    ).all()
    event_ids = [l.event_id for l in links]
    events = db.exec(select(Event).where(Event.id.in_(event_ids))).all() if event_ids else []

    return templates.TemplateResponse(
        request=request,
        name="User/albums/album_detail.html",
        context={
            "request": request,
            "user": user,
            "album": album,
            "events": events,
        },
    )

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
        flash(request, "Not authorized.", "error")
      
        return RedirectResponse(url="/bookmarks", status_code=303)

    link = db.exec(
        select(AlbumEventLink).where(
            AlbumEventLink.album_id == album_id,
            AlbumEventLink.event_id == event_id,
        )
    ).first()

    if link:
        db.delete(link)
        db.commit()
      
        flash(request, "Event removed from album.", "success")

    return RedirectResponse(url=f"/albums/{album_id}", status_code=303)
