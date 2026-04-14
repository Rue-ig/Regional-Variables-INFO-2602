# PATH: app/routers/pages.py
from fastapi import Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from app.dependencies.auth import UserDep, AdminDep
from app.dependencies.session import SessionDep
from app.utilities.flash import flash
from app.models.contact import ContactInquiry, FAQ
from sqlmodel import select
from . import router, templates

def _ctx(request, user, **kwargs):
    return {"request": request, "user": user, **kwargs}

@router.get("/about", response_class=HTMLResponse)
async def about(request: Request, user: UserDep = None):
    return templates.TemplateResponse(request, "pages/about.html", _ctx(request, user))

@router.get("/faq", response_class=HTMLResponse)
async def faq(request: Request, db: SessionDep, user: UserDep = None):
    faqs = db.exec(select(FAQ).order_by(FAQ.category, FAQ.order)).all()
    
    grouped_faqs = {}
    for item in faqs:
        if item.category not in grouped_faqs:
            grouped_faqs[item.category] = []
        grouped_faqs[item.category].append(item)
        
    return templates.TemplateResponse(
        request, 
        "pages/faq.html", 
        _ctx(request, user, grouped_faqs=grouped_faqs)
    )

@router.get("/contact", response_class=HTMLResponse)
async def contact(request: Request, user: UserDep = None):
    if user and getattr(user, "role", None) == "admin":
        return RedirectResponse(url="/admin/contact", status_code=303)
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
    return templates.TemplateResponse(request, "pages/contact.html", _ctx(request, user, submitted=True))

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

@router.get("/admin/faq/edit", response_class=HTMLResponse)
async def admin_faq_page(request: Request, db: SessionDep, user: AdminDep):
    faqs = db.exec(select(FAQ).order_by(FAQ.category, FAQ.order)).all()
    return templates.TemplateResponse(
        request, 
        "Admin/faq_edit.html",
        _ctx(request, user, faqs=faqs)
    )

@router.post("/faq/edit")
async def edit_faq_redirect(request: Request, user: AdminDep):
    return RedirectResponse(url="/admin/faq/edit", status_code=303)

@router.post("/admin/faq/add")
async def add_faq(
    request: Request,
    db: SessionDep,
    user: AdminDep,
    question: str = Form(...),
    answer: str = Form(...),
    category: str = Form(...),
    order: int = Form(0)
):
    new_faq = FAQ(question=question, answer=answer, category=category, order=order)
    db.add(new_faq)
    db.commit()
    flash(request, "New FAQ added!", "success")
    
    return RedirectResponse(url="/admin/faq/edit", status_code=303)
