# PATH: app/routers/admin_import.py
import os
import tempfile
from fastapi import Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from app.dependencies import SessionDep, AdminDep
from app.models.event import Event
from app.services.scraper_service import ScraperService
from app.utilities.flash import flash
from datetime import datetime
from . import router, templates

@router.get("/admin/import", response_class=HTMLResponse)
async def admin_import_page(request: Request, admin: AdminDep):
    return templates.TemplateResponse(request=request, name="Admin/events/import.html", context={"user": admin})

@router.post("/admin/create-event")
async def admin_create_event(
    request: Request,
    db: SessionDep,
    admin: AdminDep,
    title: str = Form(...),
    island: str = Form(...),
    date: str = Form(...),
    category: str = Form(None),
    price: float = Form(0.0),
    auto_publish: str = Form("off")
):
    try:
        new_event = Event(
            title=title,
            island=island,
            date=datetime.strptime(date, '%Y-%m-%d'),
            category=category or "Other",
            price=price,
            status="published" if auto_publish == "on" else "pending"
        )
        db.add(new_event)
        db.commit()
        flash(request, f"Event '{title}' created successfully!", "success")
    except Exception as e:
        db.rollback()
        flash(request, f"Error creating event: {str(e)}", "error")
    
    return RedirectResponse(url="/admin/import", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/admin/import/csv")
async def admin_import_csv(
    request: Request,
    db: SessionDep,
    admin: AdminDep,
    file: UploadFile = File(...),
    auto_publish: str = Form("off"),
):
    if not file.filename or not file.filename.endswith(".csv"):
        flash(request, "Please upload a .csv file.", "error")
        return RedirectResponse(url="/admin/import", status_code=303)

    content = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="wb") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = ScraperService(db).import_from_csv(
            tmp_path, auto_publish=(auto_publish == "on")
        )
    finally:
        os.unlink(tmp_path)

    summary = f"Import complete: {result['created']} created, {result['skipped']} skipped."
    if result["errors"]:
        summary += f" {len(result['errors'])} error(s)."
        flash(request, summary, "warning")
    else:
        flash(request, summary, "success")

    return templates.TemplateResponse(
        request=request,
        name="Admin/events/import.html",
        context={"user": admin, "result": result},
    )