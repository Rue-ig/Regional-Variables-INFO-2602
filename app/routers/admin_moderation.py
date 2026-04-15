# PATH: app/routers/admin_moderation.py
from fastapi import HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from sqlmodel import select
from typing import Optional
from app.models.report import Report, ReportReason, ReportStatus
from app.models.review import Review
from datetime import datetime
from app.dependencies import SessionDep, AuthDep
from . import router, templates

@router.post("/photo/{photo_id}")
async def report_photo(
    request: Request,
    photo_id: int,
    reason: ReportReason,
    user: AuthDep,
    db: SessionDep,
    details: Optional[str] = None,
):
    existing = db.exec(
        select(Report).where(
            Report.photo_id == photo_id,
            Report.user_id == user.id,
        )
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already reported this photo")

    db.add(Report(user_id=user.id, photo_id=photo_id, reason=reason, details=details))
    db.commit()

    return {"message": "Photo reported successfully"}

@router.post("/review/{review_id}")
async def report_review(
    request: Request,
    review_id: int,
    reason: ReportReason,
    user: AuthDep,
    db: SessionDep,
    details: Optional[str] = None,
):
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot report your own review")

    existing = db.exec(
        select(Report).where(
            Report.review_id == review_id,
            Report.user_id == user.id,
        )
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already reported this review")

    db.add(Report(user_id=user.id, review_id=review_id, reason=reason, details=details))
    db.commit()

    return {"message": "Review reported successfully"}

@router.post("/review/{review_id}/form")
async def report_review_form(
    request: Request,
    review_id: int,
    user: AuthDep,
    db: SessionDep,
    reason: ReportReason = Form(...),
    details: Optional[str] = Form(None),
):
    review = db.get(Review, review_id)
    if not review:
        return RedirectResponse(url="/events?error=Review+not+found", status_code=303)

    if review.user_id == user.id:
        return RedirectResponse(
            url=f"/events/{review.event_id}?error=You+cannot+report+your+own+review",
            status_code=303,
        )

    existing = db.exec(
        select(Report).where(
            Report.review_id == review_id,
            Report.user_id == user.id,
        )
    ).first()

    if existing:
        return RedirectResponse(
            url=f"/events/{review.event_id}?error=You+have+already+reported+this+review",
            status_code=303,
        )

    db.add(Report(user_id=user.id, review_id=review_id, reason=reason, details=details))
    db.commit()

    return RedirectResponse(
        url=f"/events/{review.event_id}?message=Review+reported+successfully",
        status_code=303,
    )

@router.get("/my-reports")
async def get_my_reports(request: Request, user: AuthDep, db: SessionDep):
    reports = db.exec(select(Report).where(Report.user_id == user.id)).all()
    return {"reports": reports}


@router.get("/admin/pending")
async def get_pending_reports(request: Request, user: AuthDep, db: SessionDep):
    if not getattr(user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")

    reports = db.exec(
        select(Report).where(Report.status == ReportStatus.PENDING)
    ).all()
    return {"reports": reports}

@router.put("/admin/{report_id}/review")
async def review_report(
    request: Request,
    report_id: int,
    status: ReportStatus,
    user: AuthDep,
    db: SessionDep,
    admin_notes: Optional[str] = None,
):
    if not getattr(user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")

    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = status
    report.admin_notes = admin_notes
    report.reviewed_at = datetime.utcnow()
    db.commit()

    return {"message": f"Report {status.value}", "report_id": report_id}
