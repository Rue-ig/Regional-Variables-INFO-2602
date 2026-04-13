from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import select
from app.dependencies.session import SessionDep
from app.dependencies.auth import AdminDep
from app.models.report import Report
from app.models.photo import Photo
from app.models.review import Review
from . import router, templates

@router.get("/admin/reports", response_class=HTMLResponse)
async def admin_reports_view(request: Request, db: SessionDep, admin: AdminDep):
    reports = db.exec(select(Report).order_by(Report.created_at.desc())).all()
    
    return templates.TemplateResponse(
        "Admin/reports.html",
        {
            "request": request,
            "user": admin,
            "reports": reports
        }
    )
    
@router.post("/admin/reports/{report_id}/dismiss")
async def dismiss_report(report_id: int, db: SessionDep, admin: AdminDep):
    report = db.get(Report, report_id)
    if report:
        db.delete(report)
        db.commit()
    return RedirectResponse("/admin/reports", status_code=303)

@router.post("/admin/reports/{report_id}/delete-content")
async def delete_reported_content(report_id: int, db: SessionDep, admin: AdminDep):
    report = db.get(Report, report_id)
    if report:
        if report.photo_id:
            content = db.get(Photo, report.photo_id)
        else:
            content = db.get(Review, report.review_id)
        
        if content:
            db.delete(content)
        db.delete(report) 
        db.commit()
    return RedirectResponse("/admin/reports", status_code=303)