from typing import Optional
from datetime import datetime
from fastapi import Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import select
from sqlalchemy.orm import selectinload
from app.dependencies.session import SessionDep
from app.dependencies.auth import AdminDep, AuthDep
from app.models.report import Report, ReportStatus, ReportReason
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
        content = db.get(Photo, report.photo_id) if report.photo_id else db.get(Review, report.review_id)
        if content:
            db.delete(content)
        db.delete(report) 
        db.commit()
        
    return RedirectResponse("/admin/reports", status_code=303)

@router.get("/admin/pending")
async def get_pending_reports(db: SessionDep, admin: AdminDep):
    reports = db.exec(select(Report).where(Report.status == ReportStatus.PENDING)).all()
    return {"reports": reports}

@router.put("/admin/{report_id}/review")
async def review_report(
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

@router.post("/photo/{photo_id}/report")
async def report_photo(
    photo_id: int, reason: ReportReason, user: AuthDep, db: SessionDep, details: Optional[str] = None
):
    existing = db.exec(select(Report).where(Report.photo_id == photo_id, Report.user_id == user.id)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already reported this photo")
    
    report = Report(user_id=user.id, photo_id=photo_id, reason=reason, details=details)
    db.add(report)
    db.commit()
    
    return {"message": "Photo reported successfully", "report_id": report.id}

@router.post("/review/{review_id}/report")
async def report_review(
    review_id: int, reason: ReportReason, user: AuthDep, db: SessionDep, details: Optional[str] = None
):
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
        
    if review.user_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot report your own review")
    
    existing = db.exec(select(Report).where(Report.review_id == review_id, Report.user_id == user.id)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already reported this review")
    
    report = Report(user_id=user.id, review_id=review_id, reason=reason, details=details)
    db.add(report)
    db.commit()
    
    return {"message": "Review reported successfully", "report_id": report.id}

@router.post("/review/{review_id}/form")
async def report_review_form(
    review_id: int, user: AuthDep, db: SessionDep, 
    reason: ReportReason = Form(...), details: Optional[str] = Form(None)
):
    review = db.get(Review, review_id)
    if not review:
        return RedirectResponse(url="/events?error=Review+not+found", status_code=303)
    
    if review.user_id == user.id:
        return RedirectResponse(url=f"/events/{review.event_id}?error=Cannot+report+self", status_code=303)
    
    existing = db.exec(select(Report).where(Report.review_id == review_id, Report.user_id == user.id)).first()
    if existing:
        return RedirectResponse(url=f"/events/{review.event_id}?error=Already+reported", status_code=303)
    
    report = Report(user_id=user.id, review_id=review_id, reason=reason, details=details)
    db.add(report)
    db.commit()
    
    return RedirectResponse(url=f"/events/{review.event_id}?message=Reported", status_code=303)

@router.get("/my-reports")
async def get_my_reports(user: AuthDep, db: SessionDep):
    reports = db.exec(select(Report).where(Report.user_id == user.id)).all()
    return {"reports": reports}
