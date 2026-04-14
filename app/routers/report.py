from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from typing import Optional
from app.database import get_session
from app.models.report import Report, ReportReason, ReportStatus
from app.models.review import Review
from app.schemas.report import ReportCreate
from datetime import datetime
from . import router, templates

report_router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("/photo/{photo_id}")
async def report_photo(
    request: Request,
    photo_id: int,
    reason: ReportReason,
    details: Optional[str] = None,
    session: Session = Depends(get_session)
):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Must be logged in")
    
    existing = session.exec(
        select(Report).where(
            Report.photo_id == photo_id,
            Report.user_id == user["id"]
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already reported this photo")
    
    report = Report(
        user_id=user["id"],
        photo_id=photo_id,
        reason=reason,
        details=details
    )
    
    session.add(report)
    session.commit()
    
    return {"message": "Photo reported successfully", "report_id": report.id}

@router.post("/review/{review_id}")
async def report_review(
    request: Request,
    review_id: int,
    reason: ReportReason,
    details: Optional[str] = None,
    session: Session = Depends(get_session)
):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Must be logged in")
    
    review = session.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    if review.user_id == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot report your own review")
    
    existing = session.exec(
        select(Report).where(
            Report.review_id == review_id,
            Report.user_id == user["id"]
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already reported this review")
    
    report = Report(
        user_id=user["id"],
        review_id=review_id,
        reason=reason,
        details=details
    )
    
    session.add(report)
    session.commit()
    
    return {"message": "Review reported successfully", "report_id": report.id}

@router.post("/review/{review_id}/form")
async def report_review_form(
    request: Request,
    review_id: int,
    reason: ReportReason = Form(...),
    details: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login?error=Please login to report", status_code=303)
    
    review = session.get(Review, review_id)
    if not review:
        return RedirectResponse(
            url=f"/events?error=Review not found", 
            status_code=303
        )
    
    if review.user_id == user["id"]:
        return RedirectResponse(
            url=f"/events/{review.event_id}?error=You cannot report your own review", 
            status_code=303
        )
    
    existing = session.exec(
        select(Report).where(
            Report.review_id == review_id,
            Report.user_id == user["id"]
        )
    ).first()
    
    if existing:
        return RedirectResponse(
            url=f"/events/{review.event_id}?error=You have already reported this review", 
            status_code=303
        )
    
    report = Report(
        user_id=user["id"],
        review_id=review_id,
        reason=reason,
        details=details
    )
    
    session.add(report)
    session.commit()
    
    return RedirectResponse(
        url=f"/events/{review.event_id}?message=Review+reported+successfully", 
        status_code=303
    )

@router.get("/my-reports")
async def get_my_reports(
    request: Request,
    session: Session = Depends(get_session)
):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not logged in")
    
    reports = session.exec(
        select(Report).where(Report.user_id == user["id"])
    ).all()
    
    return {"reports": reports}

@router.get("/admin/pending")
async def get_pending_reports(
    request: Request,
    session: Session = Depends(get_session)
):
    user = request.session.get("user")
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    reports = session.exec(
        select(Report).where(Report.status == ReportStatus.PENDING)
    ).all()
    
    return {"reports": reports}

@router.put("/admin/{report_id}/review")
async def review_report(
    request: Request,
    report_id: int,
    status: ReportStatus,
    admin_notes: Optional[str] = None,
    session: Session = Depends(get_session)
):
    user = request.session.get("user")
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    report = session.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report.status = status
    report.admin_notes = admin_notes
    report.reviewed_at = datetime.utcnow()
    
    session.commit()
    
    return {"message": f"Report {status.value}", "report_id": report_id}