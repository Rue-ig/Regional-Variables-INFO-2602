# PATH: app/routers/reviews.py
from fastapi import Request, Form
from fastapi.responses import RedirectResponse
from app.dependencies import SessionDep, AuthDep
from app.repositories.content import ReviewRepository
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
        flash(request, "Review submitted and awaiting approval.", "success")
        
    except Exception as e:
        flash(request, str(e), "error")
        
    return RedirectResponse(url=f"/events/{event_id}", status_code=303)

@router.post("/reviews/{review_id}/delete")
async def delete_review(
    request: Request,
    review_id: int,
    db: SessionDep,
    user: AuthDep
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

    referer = request.headers.get("referer", "/")
    
    return RedirectResponse(url=referer, status_code=303)