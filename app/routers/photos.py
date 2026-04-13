# PATH: app/routers/photos.py
from fastapi import Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from app.dependencies import SessionDep, AuthDep
from app.repositories.content import PhotoRepository
from app.services.content_service import PhotoService
from app.utilities.flash import flash
from . import router
import os

@router.post("/events/{event_id}/photos")
async def upload_photo(
    request: Request,
    event_id: int,
    db: SessionDep,
    user: AuthDep,
    file: UploadFile = File(...),
    caption: str = Form(""),
):
    try:
        await PhotoService(PhotoRepository(db)).upload(
            event_id=event_id, user_id=user.id, file=file, caption=caption or None
        )
        
        flash(request, "Photo uploaded and awaiting approval.", "success")
        
    except Exception as e:
        flash(request, str(e), "error")
        
    return RedirectResponse(url=f"/events/{event_id}", status_code=303)

@router.post("/photos/{photo_id}/delete")
async def delete_photo(
    request: Request,
    photo_id: int,
    db: SessionDep,
    user: AuthDep
):
    repo = PhotoRepository(db)
    photo = repo.get_by_id(photo_id)
    
    if not photo:
        flash(request, "Photo not found.", "error")
        return RedirectResponse(url="/admin/content", status_code=303)

    if user.role == "admin" or photo.user_id == user.id:
        relative_path = photo.filepath.lstrip('/') 
        
        repo.delete(photo)
        
        try:
            if os.path.exists(relative_path):
                os.remove(relative_path)
                
        except Exception as e:
            print(f"File deletion error: {e}")

        flash(request, "Photo and file permanently removed.", "success")
        
    else:
        flash(request, "Unauthorized.", "error")

    return RedirectResponse(url=request.headers.get("referer", "/"), status_code=303)