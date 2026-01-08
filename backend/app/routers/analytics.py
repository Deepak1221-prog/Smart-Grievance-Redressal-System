from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from ..database import get_db
from ..models.complaint import Complaint, ComplaintStatus, ComplaintCategory, Feedback
from ..models.user import User, UserRole
from ..utils.security import get_current_active_user
from typing import Dict, List
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/overview")
def get_overview_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get overview analytics"""
    
    # Total complaints
    total_complaints = db.query(func.count(Complaint.id)).scalar()
    
    # Resolved complaints
    resolved_complaints = db.query(func.count(Complaint.id)).filter(
        Complaint.status.in_([ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED])
    ).scalar()
    
    # Resolution rate
    resolution_rate = (resolved_complaints / total_complaints * 100) if total_complaints > 0 else 0
    
    # Average resolution time
    avg_resolution_time = db.query(
        func.avg(
            func.extract('epoch', Complaint.resolved_at - Complaint.created_at) / 86400
        )
    ).filter(
        Complaint.resolved_at.isnot(None)
    ).scalar()
    
    # Complaints by status
    status_counts = db.query(
        Complaint.status,
        func.count(Complaint.id)
    ).group_by(Complaint.status).all()
    
    status_distribution = {status.value: count for status, count in status_counts}
    
    # Current month vs previous month
    now = datetime.utcnow()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    
    current_month_complaints = db.query(func.count(Complaint.id)).filter(
        Complaint.created_at >= current_month_start
    ).scalar()
    
    previous_month_complaints = db.query(func.count(Complaint.id)).filter(
        Complaint.created_at >= previous_month_start,
        Complaint.created_at < current_month_start
    ).scalar()
    
    return {
        "total_complaints": total_complaints,
        "resolved_complaints": resolved_complaints,
        "resolution_rate": round(resolution_rate, 2),
        "average_resolution_days": round(avg_resolution_time, 2) if avg_resolution_time else 0,
        "status_distribution": status_distribution,
        "current_month_complaints": current_month_complaints,
        "previous_month_complaints": previous_month_complaints
    }

@router.get("/category")
def get_category_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get category-wise analytics"""
    
    # Complaints by category
    category_counts = db.query(
        Complaint.category,
        func.count(Complaint.id)
    ).group_by(Complaint.category).all()
    
    # Resolution time by category
    resolution_times = db.query(
        Complaint.category,
        func.avg(
            func.extract('epoch', Complaint.resolved_at - Complaint.created_at) / 86400
        )
    ).filter(
        Complaint.resolved_at.isnot(None)
    ).group_by(Complaint.category).all()
    
    return {
        "category_counts": {cat.value: count for cat, count in category_counts},
        "avg_resolution_by_category": {
            cat.value: round(avg_time, 2) if avg_time else 0
            for cat, avg_time in resolution_times
        }
    }

@router.get("/trends")
def get_trend_analytics(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get time-series trends"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Daily complaint counts
    daily_counts = db.query(
        func.date(Complaint.created_at).label('date'),
        func.count(Complaint.id).label('count')
    ).filter(
        Complaint.created_at >= start_date
    ).group_by(func.date(Complaint.created_at)).all()
    
    # Sentiment trends
    sentiment_avg = db.query(
        func.date(Complaint.created_at).label('date'),
        func.avg(Complaint.sentiment_score).label('avg_sentiment')
    ).filter(
        Complaint.created_at >= start_date
    ).group_by(func.date(Complaint.created_at)).all()
    
    return {
        "daily_complaints": [
            {"date": str(date), "count": count}
            for date, count in daily_counts
        ],
        "sentiment_trend": [
            {"date": str(date), "avg_sentiment": round(float(avg), 2)}
            for date, avg in sentiment_avg
        ]
    }

@router.get("/performance")
def get_performance_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get officer performance metrics"""
    
    if current_user.role not in [UserRole.ADMIN, UserRole.OFFICER]:
        return {"message": "Access restricted"}
    
    # Officer performance
    officer_stats = db.query(
        User.id,
        User.full_name,
        func.count(Complaint.id).label('total_assigned'),
        func.count(case(
            (Complaint.status.in_([ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED]), 1)
        )).label('resolved'),
        func.avg(
            func.extract('epoch', Complaint.resolved_at - Complaint.created_at) / 86400
        ).label('avg_resolution_time')
    ).join(
        Complaint, User.id == Complaint.assigned_to
    ).filter(
        User.role == UserRole.OFFICER
    ).group_by(User.id, User.full_name).all()
    
    return {
        "officers": [
            {
                "officer_id": officer_id,
                "officer_name": name,
                "total_assigned": total,
                "resolved": resolved,
                "resolution_rate": round((resolved / total * 100) if total > 0 else 0, 2),
                "avg_resolution_days": round(avg_time, 2) if avg_time else 0
            }
            for officer_id, name, total, resolved, avg_time in officer_stats
        ]
    }
