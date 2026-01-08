from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..models.user import User, UserRole
from ..models.complaint import (
    Complaint, ComplaintStatus, ComplaintCategory, ComplaintPriority,
    Attachment, Comment, Feedback
)

from ..schemas.complaint import (
    ComplaintCreate, ComplaintResponse, ComplaintUpdate,
    CommentCreate, CommentResponse, FeedbackCreate, FeedbackResponse
)
from ..utils.security import get_current_active_user
from ..utils.helpers import generate_complaint_id
from ..services.ml_service import ml_service
from ..services.audit_service import audit_service
from ..services.notification_service import notification_service
import os
import shutil

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])

@router.post("/", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
def create_complaint(
    complaint: ComplaintCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new complaint"""
    
    # Generate complaint ID
    complaint_id = generate_complaint_id()
    
    # Analyze sentiment
    try:
        sentiment_label, sentiment_score = ml_service.analyze_sentiment(complaint.description)
    except Exception as e:
        print(f"Sentiment analysis error: {e}")
        sentiment_score = 0.0
    
    # Use provided category or classify
    category = complaint.category
    if not category:
        try:
            category_str, confidence = ml_service.classify_complaint(complaint.description)
            category = ComplaintCategory[category_str.upper()]
        except Exception as e:
            print(f"Classification error: {e}")
            category = ComplaintCategory.OTHER
    
    # Determine priority
    try:
        priority_str = ml_service.determine_priority(sentiment_score, complaint.description)
        priority = ComplaintPriority[priority_str.upper()]
    except Exception as e:
        print(f"Priority determination error: {e}")
        priority = ComplaintPriority.MEDIUM
    
    # Create complaint
    db_complaint = Complaint(
        complaint_id=complaint_id,
        citizen_id=current_user.id,
        title=complaint.title,
        description=complaint.description,
        category=category,
        ward=complaint.ward,
        location=complaint.location,
        is_anonymous=complaint.is_anonymous,
        sentiment_score=sentiment_score,
        priority=priority,
        status=ComplaintStatus.SUBMITTED
    )
    
    db.add(db_complaint)
    db.commit()
    db.refresh(db_complaint)
    
    # Create audit log
    try:
        audit_service.create_audit_log(
            db=db,
            complaint_id=db_complaint.id,
            user_id=current_user.id,
            action_type="CREATED",
            previous_state=None,
            new_state=ComplaintStatus.SUBMITTED.value,
            details={"title": complaint.title, "category": category.value},
            ip_address=request.client.host
        )
    except Exception as e:
        print(f"Audit log error: {e}")
    
    # Send confirmation email
    if not complaint.is_anonymous:
        try:
            notification_service.send_complaint_confirmation(
                current_user.email,
                complaint_id,
                complaint.title
            )
        except Exception as e:
            print(f"Email notification error: {e}")
    
    return db_complaint


@router.get("/", response_model=List[ComplaintResponse])
def list_complaints(
    skip: int = 0,
    limit: int = 100,
    status: Optional[ComplaintStatus] = None,
    category: Optional[ComplaintCategory] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List complaints with filters"""
    query = db.query(Complaint)
    
    # Role-based filtering
    if current_user.role == UserRole.CITIZEN:
        query = query.filter(Complaint.citizen_id == current_user.id)
    elif current_user.role == UserRole.OFFICER:
        query = query.filter(Complaint.assigned_to == current_user.id)
    
    # Apply filters
    if status:
        query = query.filter(Complaint.status == status)
    if category:
        query = query.filter(Complaint.category == category)
    
    complaints = query.order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()
    return complaints

@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get complaint details"""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    # Check permissions
    if current_user.role == UserRole.CITIZEN and complaint.citizen_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return complaint

@router.put("/{complaint_id}", response_model=ComplaintResponse)
def update_complaint(
    complaint_id: int,
    complaint_update: ComplaintUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update complaint (officer/admin only)"""
    if current_user.role not in [UserRole.OFFICER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    # Update fields
    previous_status = complaint.status.value if complaint.status else None
    
    if complaint_update.status:
        complaint.status = complaint_update.status
        if complaint_update.status == ComplaintStatus.RESOLVED:
            complaint.resolved_at = datetime.utcnow()
    
    if complaint_update.assigned_to:
        complaint.assigned_to = complaint_update.assigned_to
    
    if complaint_update.category:
        complaint.category = complaint_update.category
    
    db.commit()
    db.refresh(complaint)
    
    # Create audit log
    audit_service.create_audit_log(
        db=db,
        complaint_id=complaint.id,
        user_id=current_user.id,
        action_type="UPDATED",
        previous_state=previous_status,
        new_state=complaint.status.value,
        details={"updated_by": current_user.email},
        ip_address=request.client.host
    )
    
    # Send notification
    if complaint_update.status and complaint.citizen:
        notification_service.send_status_update(
            complaint.citizen.email,
            complaint.complaint_id,
            previous_status,
            complaint.status.value
        )
    
    return complaint

@router.post("/{complaint_id}/comments", response_model=CommentResponse)
def add_comment(
    complaint_id: int,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add comment to complaint"""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    db_comment = Comment(
        complaint_id=complaint_id,
        user_id=current_user.id,
        comment_text=comment.comment_text,
        is_internal=comment.is_internal
    )
    
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    
    return db_comment

@router.post("/{complaint_id}/feedback", response_model=FeedbackResponse)
def submit_feedback(
    complaint_id: int,
    feedback: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Submit feedback for resolved complaint"""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    if complaint.citizen_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if complaint.status not in [ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED]:
        raise HTTPException(status_code=400, detail="Can only provide feedback for resolved complaints")
    
    # Check if feedback already exists
    existing_feedback = db.query(Feedback).filter(Feedback.complaint_id == complaint_id).first()
    if existing_feedback:
        raise HTTPException(status_code=400, detail="Feedback already submitted")
    
    db_feedback = Feedback(
        complaint_id=complaint_id,
        citizen_id=current_user.id,
        rating=feedback.rating,
        feedback_text=feedback.feedback_text,
        was_resolved=feedback.was_resolved
    )
    
    db.add(db_feedback)
    
    # Update complaint status to closed
    complaint.status = ComplaintStatus.CLOSED
    
    db.commit()
    db.refresh(db_feedback)
    
    return db_feedback
