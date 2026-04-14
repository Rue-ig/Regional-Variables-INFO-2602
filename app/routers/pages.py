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
    return templates.TemplateResponse(request, "pages/contact.html", _ctx(request, user))

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

@router.get("/admin/contact", response_class=HTMLResponse)
async def admin_contact_list(request: Request, db: SessionDep, user: AdminDep):
    inquiries = db.exec(
        select(ContactInquiry).order_by(ContactInquiry.created_at.desc())
    ).all()
    
    return templates.TemplateResponse(
        request, "Admin/contact.html",
        {"request": request, "user": user, "inquiries": inquiries}
    )

@router.post("/admin/contact/{inquiry_id}/reply")
async def admin_contact_reply(
    request: Request,
    inquiry_id: int,
    db: SessionDep,
    user: AdminDep,
    reply_body: str = Form(...),
):
    from datetime import datetime
    inquiry = db.get(ContactInquiry, inquiry_id)
    if inquiry:
        inquiry.replied = True
        inquiry.reply_body = reply_body
        inquiry.replied_at = datetime.utcnow()
        db.add(inquiry)
        db.commit()
        flash(request, "Reply saved.", "success")
        
    return RedirectResponse(url="/admin/contact", status_code=303)

@router.post("/admin/contact/{inquiry_id}/delete")
async def admin_contact_delete(
    request: Request,
    inquiry_id: int,
    db: SessionDep,
    user: AdminDep,
):
    inquiry = db.get(ContactInquiry, inquiry_id)
    if inquiry:
        db.delete(inquiry)
        db.commit()
        
    return RedirectResponse(url="/admin/contact", status_code=303)
