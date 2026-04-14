# PATH: app/models/contact.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class ContactInquiry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str
    subject: str = "general"
    message: str
    replied: bool = False
    reply_body: Optional[str] = None
    replied_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
