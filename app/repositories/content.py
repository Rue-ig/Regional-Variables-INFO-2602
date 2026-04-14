# PATH: app/repositories/content.py
from sqlmodel import Session, select
from app.models.review import Review
from app.models.review_vote import ReviewVote
from app.models.photo import Photo
from app.models.bookmark import Bookmark
from typing import Optional

class ReviewRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, review_id: int) -> Optional[Review]:
        return self.session.get(Review, review_id)

    def get_for_event(self, event_id: int, approved_only: bool = True) -> list[Review]:
        query = select(Review).where(Review.event_id == event_id)
        if approved_only:
            query = query.where(Review.approved == True)
            
        return self.session.exec(query.order_by(Review.created_at.desc())).all()

    def get_by_user_and_event(self, user_id: int, event_id: int) -> Optional[Review]:
        return self.session.exec(
            select(Review).where(Review.user_id == user_id, Review.event_id == event_id)
        ).first()

    def create(self, event_id: int, user_id: int, rating: int, body: str) -> Review:
        review = Review(event_id=event_id, user_id=user_id, rating=rating, body=body)
        self.session.add(review)
        self.session.commit()
        self.session.refresh(review)
        
        return review

    def delete(self, review: Review) -> None:
        self.session.delete(review)
        self.session.commit()

    def average_rating(self, event_id: int) -> Optional[float]:
        reviews = self.get_for_event(event_id, approved_only=True)
        if not reviews:
            return None
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    def get_pending(self) -> list[Review]:
        return self.session.exec(
            select(Review).where(Review.approved == False).order_by(Review.created_at.desc())
        ).all()

    def approve(self, review: Review) -> Review:
        """Mark a review as approved."""
        review.approved = True
        self.session.add(review)
        self.session.commit()
        self.session.refresh(review)
        
        return review
            
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

class ReviewVoteRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_vote(self, user_id: int, review_id: int) -> Optional[ReviewVote]:
        return self.session.exec(
            select(ReviewVote)
            .where(ReviewVote.user_id == user_id, ReviewVote.review_id == review_id)
        ).first()

    def add(self, vote: ReviewVote):
        self.session.add(vote)

    def delete(self, vote: ReviewVote):
        self.session.delete(vote)

class PhotoRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, photo_id: int) -> Optional[Photo]:
        return self.session.get(Photo, photo_id)

    def get_for_event(self, event_id: int, approved_only: bool = True) -> list[Photo]:
        query = select(Photo).where(Photo.event_id == event_id)
        if approved_only:
            query = query.where(Photo.approved == True)
        return self.session.exec(query.order_by(Photo.created_at.desc())).all()

    def get_pending(self) -> list[Photo]:
        return self.session.exec(
            select(Photo).where(Photo.approved == False).order_by(Photo.created_at.desc())
        ).all()

    def create(self, event_id: int, user_id: int, filepath: str, caption: Optional[str] = None) -> Photo:
        photo = Photo(event_id=event_id, user_id=user_id, filepath=filepath, caption=caption)
        self.session.add(photo)
        self.session.commit()
        self.session.refresh(photo)
        return photo

    def approve(self, photo: Photo) -> Photo:
        photo.approved = True
        self.session.add(photo)
        self.session.commit()
        self.session.refresh(photo)
        return photo

    def delete(self, photo: Photo) -> None:
        self.session.delete(photo)
        self.session.commit()

class BookmarkRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_for_user(self, user_id: int) -> list[Bookmark]:
        return self.session.exec(
            select(Bookmark).where(Bookmark.user_id == user_id).order_by(Bookmark.created_at.desc())
        ).all()

    def get(self, user_id: int, event_id: int) -> Optional[Bookmark]:
        return self.session.exec(
            select(Bookmark).where(Bookmark.user_id == user_id, Bookmark.event_id == event_id)
        ).first()

    def create(self, user_id: int, event_id: int) -> Bookmark:
        bookmark = Bookmark(user_id=user_id, event_id=event_id)
        self.session.add(bookmark)
        self.session.commit()
        self.session.refresh(bookmark)
        return bookmark

    def delete(self, bookmark: Bookmark) -> None:
        self.session.delete(bookmark)
        self.session.commit()

    def get_event_ids_for_user(self, user_id: int) -> set[int]:
        bookmarks = self.get_for_user(user_id)
        return {b.event_id for b in bookmarks}
