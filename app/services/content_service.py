# PATH: app/services/content_service.py
import os
import uuid
from fastapi import HTTPException, UploadFile, status
from app.repositories.content import ReviewRepository, PhotoRepository, BookmarkRepository
from app.models.review import Review
from app.models.photo import Photo
from app.models.bookmark import Bookmark
from typing import Optional

UPLOAD_DIR = "app/static/uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

class ReviewService:
    def __init__(self, repo: ReviewRepository, vote_repo: Optional[ReviewVoteRepository] = None):
        self.repo = repo
        self.vote_repo = vote_repo

    def submit(self, event_id: int, user_id: int, rating: int, body: str) -> Review:
        if self.repo.get_by_user_and_event(user_id, event_id):
            raise HTTPException(status_code=400, detail="You have already reviewed this event")
            
        if not (1 <= rating <= 5):
            raise HTTPException(status_code=422, detail="Rating must be 1–5")
            
        return self.repo.create(event_id, user_id, rating, body)

    def toggle_vote(self, review_id: int, user_id: int, vote_type: str) -> dict:
        review = self.repo.get_by_id(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        existing = self.vote_repo.get_vote(user_id, review_id)
        current_state = vote_type

        if existing:
            if existing.vote == vote_type:
                if vote_type == "up":
                    review.upvotes -= 1
                    
                else:
                    review.downvotes -= 1
                    
                self.vote_repo.delete(existing)
                current_state = None

            else:
                if vote_type == "up":
                    review.upvotes += 1
                    review.downvotes -= 1
                    
                else:
                    review.downvotes += 1
                    review.upvotes -= 1
                    
                existing.vote = vote_type
                self.vote_repo.add(existing)
        else:
            new_vote = ReviewVote(user_id=user_id, review_id=review_id, vote=vote_type)
            if vote_type == "up":
                review.upvotes += 1
                
            else:
                review.downvotes += 1
                
            self.vote_repo.add(new_vote)

        review.upvotes = max(0, review.upvotes)
        review.downvotes = max(0, review.downvotes)
        
        self.repo.session.add(review)
        self.repo.session.commit()
        self.repo.session.refresh(review)

        return {
            "upvotes": review.upvotes,
            "downvotes": review.downvotes,
            "user_vote": current_state
        }

class PhotoService:
    def __init__(self, repo: PhotoRepository):
        self.repo = repo

    def get_for_event(self, event_id: int) -> list[Photo]:
        return self.repo.get_for_event(event_id)

    async def upload(self, event_id: int, user_id: int, file: UploadFile, caption: Optional[str] = None) -> Photo:
        ext = os.path.splitext(file.filename or "")[1].lower()
        
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Only JPG, PNG, and WebP images are allowed")
        
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        content = await file.read()
        
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File must be under 5MB")
        
        with open(filepath, "wb") as f:
            f.write(content)
        web_path = f"/static/uploads/{filename}"
        
        return self.repo.create(event_id=event_id, user_id=user_id, filepath=web_path, caption=caption)

    def approve(self, photo_id: int) -> Photo:
        photo = self.repo.get_by_id(photo_id)
        
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")
        
        return self.repo.approve(photo)

    def delete(self, photo_id: int) -> None:
        photo = self.repo.get_by_id(photo_id)
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")
        
        disk_path = "app" + photo.filepath
        
        if os.path.exists(disk_path):
            os.remove(disk_path)
            
        self.repo.delete(photo)

    def get_pending(self) -> list[Photo]:
        return self.repo.get_pending()

class BookmarkService:
    def __init__(self, repo: BookmarkRepository):
        self.repo = repo

    def get_for_user(self, user_id: int) -> list[Bookmark]:
        return self.repo.get_for_user(user_id)

    def get_bookmarked_ids(self, user_id: int) -> set[int]:
        return self.repo.get_event_ids_for_user(user_id)

    def toggle(self, user_id: int, event_id: int) -> dict:
        existing = self.repo.get(user_id, event_id)
        
        if existing:
            self.repo.delete(existing)
            return {"bookmarked": False}
        
        self.repo.create(user_id=user_id, event_id=event_id)
        
        return {"bookmarked": True}
