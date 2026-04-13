# app/services/report_service.py
from sqlmodel import Session
from app.models.report import Report

class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def file_report(self, user_id: int, reason: str, details: str = None, photo_id: int = None, review_id: int = None):
        report = Report(
            user_id=user_id,
            reason=reason,
            details=details,
            photo_id=photo_id,
            review_id=review_id
        )
        
        self.db.add(report)
        self.db.commit()
        
        return report