from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from ..models.complaint import ComplaintStatus, ComplaintPriority, ComplaintCategory

class ComplaintBase(BaseModel):
    title: str
    description: str
    category: Optional[ComplaintCategory] = None
    ward: str
    location: Optional[str] = None
    is_anonymous: bool = False

class ComplaintCreate(ComplaintBase):
    pass

class ComplaintResponse(ComplaintBase):
    id: int
    complaint_id: str
    citizen_id: int
    priority: ComplaintPriority
    sentiment_score: float
    status: ComplaintStatus
    assigned_to: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ComplaintUpdate(BaseModel):
    status: Optional[ComplaintStatus] = None
    assigned_to: Optional[int] = None
    category: Optional[ComplaintCategory] = None

class CommentCreate(BaseModel):
    comment_text: str
    is_internal: bool = False

class CommentResponse(BaseModel):
    id: int
    complaint_id: int
    user_id: int
    comment_text: str
    is_internal: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class FeedbackCreate(BaseModel):
    rating: int  # 1-5
    feedback_text: Optional[str] = None
    was_resolved: bool

class FeedbackResponse(FeedbackCreate):
    id: int
    complaint_id: int
    citizen_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ComplaintCreate(BaseModel):
    title: str
    description: str
    category: Optional[ComplaintCategory] = None  # Make it optional
    ward: str
    location: Optional[str] = None
    is_anonymous: bool = False
