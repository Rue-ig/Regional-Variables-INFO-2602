# PATH: app/routers/pages.py
from fastapi import Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from app.dependencies.auth import UserDep
from app.utilities.flash import flash
from . import router, templates

def _ctx(request, user, **kwargs):
    return {"request": request, "user": user, **kwargs}

@router.get("/about", response_class=HTMLResponse)
async def about(request: Request, user: UserDep = None):
    return templates.TemplateResponse(request, "about.html", _ctx(request, user))

@router.get("/faq", response_class=HTMLResponse)
async def faq(request: Request, user: UserDep = None):
    return templates.TemplateResponse(request, "faq.html", _ctx(request, user))

@router.get("/contact", response_class=HTMLResponse)
async def contact(request: Request, user: UserDep = None):
    return templates.TemplateResponse(request, "contact.html", _ctx(request, user))

@router.post("/contact")
async def contact_submit(
    request: Request,
    user: UserDep = None,
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...),
):
    flash(request, "Message received — we'll be in touch soon!", "success")
    return templates.TemplateResponse(
        request, 
        "contact.html", 
        _ctx(request, user, submitted=True)
    )

@router.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request, user: UserDep = None):
    return templates.TemplateResponse(request, "privacy.html", _ctx(request, user))

@router.get("/terms", response_class=HTMLResponse)
async def terms(request: Request, user: UserDep = None):
    return templates.TemplateResponse(request, "terms.html", _ctx(request, user))

@router.get("/cookies", response_class=HTMLResponse)
async def cookies(request: Request, user: UserDep = None):
    return templates.TemplateResponse(request, "cookies.html", _ctx(request, user))

@router.get("/disclaimer", response_class=HTMLResponse)
async def disclaimer(request: Request, user: UserDep = None):
    return templates.TemplateResponse(request, "disclaimer.html", _ctx(request, user))

@router.post("/faq/edit")
async def edit_faq(request: Request, user: UserDep, faq_data: str = Form(...)):
    if user.role != 'admin':
        flash(request, "Unauthorized", "error")
        return RedirectResponse(url="/faq", status_code=303)
    
    flash(request, "FAQ updated successfully!", "success")
    return RedirectResponse(url="/faq", status_code=303)
