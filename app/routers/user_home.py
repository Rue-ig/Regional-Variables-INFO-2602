# PATH: app/routers/user_home.py
from fastapi import UploadFile, File, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import select
from app.dependencies.session import SessionDep
from app.dependencies.auth import AuthDep, UserDep
from app.models.user import User
from app.models.photo import Photo
from app.models.review import Review
from app.models.bookmark import Bookmark
from app.models.event import Event 
from app.utilities.security import encrypt_password
import os, uuid
from . import router, templates

@router.get("/home", response_class=HTMLResponse)
async def user_home_view(request: Request, db: SessionDep, user: UserDep):
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    featured_events = db.exec(select(Event).limit(8)).all()
    
    raw_reviews = db.exec(select(Review).limit(3)).all()
    featured_reviews = []
    for r in raw_reviews:
        u = db.get(User, r.user_id)
        featured_reviews.append({
            "rating": r.rating,
            "body": r.body,
            "username": u.username if u else "Anonymous",
        })
        
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "request": request,
            "user": user,
            "featured_events": featured_events,
            "featured_reviews": featured_reviews
        }
    )

@router.get("/app", response_class=HTMLResponse)
async def user_dashboard_view(request: Request, user: AuthDep, db: SessionDep):
    if user.role == "admin":
        return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

    my_photos = db.exec(select(Photo).where(Photo.user_id == user.id)).all()
    my_reviews = db.exec(select(Review).where(Review.user_id == user.id)).all()
    my_bookmarks = db.exec(select(Bookmark).where(Bookmark.user_id == user.id)).all()

    return templates.TemplateResponse(
        request=request, 
        name="app.html",
        context={
            "request": request,
            "user": user,
            "photos": my_photos,
            "reviews": my_reviews,
            "bookmarks": my_bookmarks
        }
    )

@router.post("/app/edit-profile")
async def edit_profile(
    user: AuthDep, 
    db: SessionDep, 
    username: str = Form(...),
    profile_pic: UploadFile = File(None)
):
    if username != user.username:
        existing_user = db.exec(select(User).where(User.username == username)).first()
        if not existing_user:
            user.username = username

    if profile_pic and profile_pic.filename:
        ext = os.path.splitext(profile_pic.filename)[1].lower()
        if ext in {".jpg", ".jpeg", ".png", ".webp"}:
            os.makedirs("app/static/uploads/avatars", exist_ok=True)
            filename = f"{uuid.uuid4().hex}{ext}"
            path = f"app/static/uploads/avatars/{filename}"
            
            content = await profile_pic.read()
            with open(path, "wb") as f:
                f.write(content)
            
            user.avatar_url = f"/static/uploads/avatars/{filename}"

    db.add(user)
    db.commit()
    
    return RedirectResponse(url="/app?msg=Profile+updated", status_code=303)

@router.post("/app/edit-email")
async def edit_email(user: AuthDep, db: SessionDep, email: str = Form(...)):
    if email == user.email:
        return RedirectResponse(url="/app", status_code=303)
    
    existing_user = db.exec(select(User).where(User.email == email)).first()
    
    if existing_user:
        return RedirectResponse(url="/app?msg=Error:+Email+in+use", status_code=303)
    
    user.email = email
    db.add(user)
    db.commit()
    
    return RedirectResponse(url="/app?msg=Email+updated", status_code=303)

@router.post("/app/change-password")
async def change_password(user: AuthDep, db: SessionDep, new_password: str = Form(...)):
    user.hashed_password = encrypt_password(new_password)
    db.add(user)
    db.commit()
    
    return RedirectResponse(url="/app?msg=Password+changed", status_code=303)

@router.post("/app/upload-avatar")
async def upload_avatar(user: AuthDep, db: SessionDep, file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        return RedirectResponse(url="/app?msg=Error:+Invalid+file+type", status_code=303)
        
    os.makedirs("app/static/uploads/avatars", exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    path = f"app/static/uploads/avatars/{filename}"
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        return RedirectResponse(url="/app?msg=Error:+File+too+large+(max+2MB)", status_code=303)
        
    with open(path, "wb") as f:
        f.write(content)
        
    if user.avatar_url and "uploads/avatars" in user.avatar_url:
        old = "app" + user.avatar_url
        if os.path.exists(old):
            os.remove(old)
            
    user.avatar_url = f"/static/uploads/avatars/{filename}"
    db.add(user)
    db.commit()
    
    return RedirectResponse(url="/app?msg=Avatar+updated", status_code=303)

@router.post("/app/remove-avatar")
async def remove_avatar(user: AuthDep, db: SessionDep):
    if user.avatar_url and "uploads/avatars" in user.avatar_url:
        old = "app" + user.avatar_url
        if os.path.exists(old):
            os.remove(old)
            
    user.avatar_url = None
    db.add(user)
    db.commit()
    
    return RedirectResponse(url="/app?msg=Avatar+removed", status_code=303)
