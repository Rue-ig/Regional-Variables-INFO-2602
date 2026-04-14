# PATH: app/routers/user_home.py
from fastapi import Request, Form, status
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
async def edit_profile(user: AuthDep, db: SessionDep, username: str = Form(...)):
    if username == user.username:
        return RedirectResponse(url="/app", status_code=303)
    
    existing_user = db.exec(select(User).where(User.username == username)).first()
    
    if existing_user:
        return RedirectResponse(url="/app?msg=Error:+Username+taken", status_code=303)
    
    user.username = username
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
