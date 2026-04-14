# PATH: app/routers/reviews.py
from fastapi import Request, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from app.dependencies import SessionDep, AuthDep
from app.repositories.content import ReviewRepository, ReviewVoteRepository
from app.services.content_service import ReviewService
from app.utilities.flash import flash
from . import router

@router.post("/events/{event_id}/reviews")
async def submit_review(
    request: Request,
    event_id: int,
    db: SessionDep,
    user: AuthDep,
    rating: int = Form(...),
    body: str = Form(...),
):
    try:
        ReviewService(ReviewRepository(db)).submit(event_id, user.id, rating, body)
        flash(request, "Review submitted!", "success")
        
    except HTTPException as e:
        flash(request, e.detail, "error")
        
    except Exception:
        flash(request, "An error occurred while submitting your review.", "error")

    return RedirectResponse(url=f"/events/{event_id}", status_code=303)

@router.post("/reviews/{review_id}/delete")
async def delete_review(
    request: Request,
    review_id: int,
    db: SessionDep,
    user: AuthDep,
):
    service = ReviewService(ReviewRepository(db))
    review = service.repo.get_by_id(review_id)

    if not review:
        flash(request, "Review not found.", "error")
        return RedirectResponse(url="/admin/content", status_code=303)

    if user.role == "admin" or review.user_id == user.id:
        service.delete(review_id)
        flash(request, "Review removed.", "success")
        
    else:
        flash(request, "Access denied.", "error")

    return RedirectResponse(url=request.headers.get("referer", "/"), status_code=303)

@router.post("/reviews/{review_id}/vote")
async def vote_review(
    review_id: int,
    db: SessionDep,
    user: AuthDep,
    vote: str = Form(...),
):
    if vote not in ("up", "down"):
        return JSONResponse({"error": "Invalid vote"}, status_code=400)

    service = ReviewService(ReviewRepository(db), ReviewVoteRepository(db))
    try:
        result = service.toggle_vote(review_id, user.id, vote)
        return JSONResponse(result)
        
    except HTTPException as e:
        return JSONResponse({"error": e.detail}, status_code=e.status_code)
