# PATH: app/routers/pages.py
from fastapi import Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from app.dependencies.auth import UserDep, AdminDep
from app.dependencies.session import SessionDep
from app.utilities.flash import flash
from app.models.contact import ContactInquiry
from sqlmodel import select
from . import router, templates

def _ctx(request, user, **kwargs):
    return {"request": request, "user": user, **kwargs}

@router.get("/about", response_class=HTMLResponse)
async def about(request: Request, user: UserDep = None):
    return templates.TemplateResponse(request, "pages/about.html", _ctx(request, user))

@router.get("/faq", response_class=HTMLResponse)
async def faq(request: Request, user: UserDep = None):
    return templates.TemplateResponse(request, "pages/faq.html", _ctx(request, user))

@router.get("/contact", response_class=HTMLResponse)
async def contact(request: Request, user: UserDep = None):
    if user and getattr(user, "role", None) == "admin":
        return RedirectResponse(url="/admin/contact", status_code=303)
        
    return templates.TemplateResponse(request, "pages/contact.html", _ctx(request, user))

@router.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request, user: UserDep = None):
    return templates.TemplateResponse(request, "pages/privacy.html", _ctx(request, user))

@router.get("/terms", response_class=HTMLResponse)
async def terms(request: Request, user: UserDep = None):
    return templates.TemplateResponse(request, "pages/terms.html", _ctx(request, user))

@router.get("/cookies", response_class=HTMLResponse)
async def cookies(request: Request, user: UserDep = None):
    return templates.TemplateResponse(request, "pages/cookies.html", _ctx(request, user))

@router.get("/disclaimer", response_class=HTMLResponse)
async def disclaimer(request: Request, user: UserDep = None):
    return templates.TemplateResponse(request, "pages/disclaimer.html", _ctx(request, user))

@router.post("/contact")
async def contact_submit(
    request: Request,
    db: SessionDep,
    user: UserDep = None,
    name: str = Form(...),
    email: str = Form(...),
    subject: str = Form("general"),
    message: str = Form(...),
):
    inquiry = ContactInquiry(name=name, email=email, subject=subject, message=message)
    db.add(inquiry)
    db.commit()
    flash(request, "Message received — we'll be in touch soon!", "success")
    
    return templates.TemplateResponse(
        request, "pages/contact.html",
        _ctx(request, user, submitted=True)
    )

@router.post("/faq/edit")
async def edit_faq(
    request: Request,
    user: AdminDep,
    db: SessionDep,
    faq_data: str = Form(...),
):
    flash(request, "FAQ editing mode initiated.", "info")
    
    return RedirectResponse(url="/admin/faq/edit", status_code=303)
