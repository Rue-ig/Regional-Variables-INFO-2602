from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from typing import Optional
from app.database import get_session
from app.models.report import Report, ReportReason, ReportStatus
from app.models.review import Review
from app.schemas.report import ReportCreate
from datetime import datetime

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("/photo/{photo_id}")
async def report_photo(
    request: Request,
    photo_id: int,
    reason: ReportReason,
    details: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Report a photo"""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Must be logged in")
    
    # Check if already reported
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
    """Report a review"""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Must be logged in")
    
    # Check if review exists
    review = session.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Don't allow reporting your own review
    if review.user_id == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot report your own review")
    
    # Check if already reported
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

@router.get("/my-reports")
async def get_my_reports(
    request: Request,
    session: Session = Depends(get_session)
):
    """Get all reports made by current user"""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not logged in")
    
    reports = session.exec(
        select(Report).where(Report.user_id == user["id"])
    ).all()
    
    return {"reports": reports}

# Admin endpoints
@router.get("/admin/pending")
async def get_pending_reports(
    request: Request,
    session: Session = Depends(get_session)
):
    """Admin: Get all pending reports"""
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
    """Admin: Review and update report status"""
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