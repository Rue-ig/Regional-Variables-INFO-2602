# PATH: app/routers/reviews.py
from fastapi import Request, Form
from fastapi.responses import RedirectResponse, JSONResponse
from app.dependencies import SessionDep, AuthDep
from app.repositories.content import ReviewRepository
from app.services.content_service import ReviewService
from app.utilities.flash import flash
from app.models.review import Review
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
    except Exception as e:
        flash(request, str(e), "error")

    return RedirectResponse(url=f"/events/{event_id}", status_code=303)

@router.post("/reviews/{review_id}/delete")
async def delete_review(
    request: Request,
    review_id: int,
    db: SessionDep,
    user: AuthDep,
):
    repo = ReviewRepository(db)
    review = repo.get_by_id(review_id)

    if not review:
        flash(request, "Review not found.", "error")
        return RedirectResponse(url="/admin/content", status_code=303)

    if user.role == "admin" or review.user_id == user.id:
        repo.delete(review)
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
    review = db.get(Review, review_id)
    if not review:
        return JSONResponse({"error": "Not found"}, status_code=404)

    if vote == "up":
        review.upvotes = (review.upvotes or 0) + 1
        
    elif vote == "down":
        review.downvotes = (review.downvotes or 0) + 1
        
    else:
        return JSONResponse({"error": "Invalid vote"}, status_code=400)

    db.add(review)
    db.commit()
    db.refresh(review)

    return JSONResponse({
        "upvotes": review.upvotes,
        "downvotes": review.downvotes,
    })
