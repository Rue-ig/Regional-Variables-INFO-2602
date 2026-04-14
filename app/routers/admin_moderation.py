from typing import Optional
from datetime import datetime
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import select
from sqlalchemy.orm import selectinload
from app.dependencies.session import SessionDep
from app.dependencies.auth import AdminDep
from app.models.report import Report, ReportStatus
from app.models.photo import Photo
from app.models.review import Review
from . import router, templates

@router.get("/admin/reports", response_class=HTMLResponse)
async def admin_reports_view(request: Request, db: SessionDep, admin: AdminDep):
    statement = (
        select(Report)
        .options(selectinload(Report.review), selectinload(Report.photo))
        .order_by(Report.created_at.desc())
    )
    reports = db.exec(statement).all()
    
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

@router.get("/admin/pending")
async def get_pending_reports(
    request: Request,
    db: SessionDep,
    admin: AdminDep
):
    reports = db.exec(
        select(Report).where(Report.status == ReportStatus.PENDING)
    ).all()
    
    return {"reports": reports}

@router.put("/admin/{report_id}/review")
async def review_report(
    request: Request,
    report_id: int,
    status: ReportStatus,
    db: SessionDep,
    admin: AdminDep,
    admin_notes: Optional[str] = None
):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report.status = status
    report.admin_notes = admin_notes
    report.reviewed_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": f"Report {status.value}", "report_id": report_id}
