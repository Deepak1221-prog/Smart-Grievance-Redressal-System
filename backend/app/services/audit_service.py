from sqlalchemy.orm import Session
from ..models.complaint import AuditLog
from ..utils.helpers import compute_hash
import json
from typing import Optional

class AuditService:
    @staticmethod
    def create_audit_log(
        db: Session,
        complaint_id: int,
        user_id: int,
        action_type: str,
        previous_state: Optional[str],
        new_state: Optional[str],
        details: dict,
        ip_address: str
    ) -> AuditLog:
        """Create an audit log entry with blockchain-inspired hash"""
        
        # Get the last audit log for this complaint
        last_log = db.query(AuditLog).filter(
            AuditLog.complaint_id == complaint_id
        ).order_by(AuditLog.id.desc()).first()
        
        previous_hash = last_log.hash if last_log else ""
        
        # Prepare data for hashing
        hash_data = {
            "complaint_id": complaint_id,
            "user_id": user_id,
            "action_type": action_type,
            "previous_state": previous_state,
            "new_state": new_state,
            "details": details
        }
        
        # Compute hash
        current_hash = compute_hash(hash_data, previous_hash)
        
        # Create audit log
        audit_log = AuditLog(
            complaint_id=complaint_id,
            user_id=user_id,
            action_type=action_type,
            previous_state=previous_state,
            new_state=new_state,
            details=json.dumps(details),
            ip_address=ip_address,
            hash=current_hash,
            previous_hash=previous_hash
        )
        
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        
        return audit_log
    
    @staticmethod
    def verify_audit_chain(db: Session, complaint_id: int) -> bool:
        """Verify integrity of audit log chain for a complaint"""
        logs = db.query(AuditLog).filter(
            AuditLog.complaint_id == complaint_id
        ).order_by(AuditLog.id).all()
        
        if not logs:
            return True
        
        previous_hash = ""
        for log in logs:
            # Reconstruct hash data
            hash_data = {
                "complaint_id": log.complaint_id,
                "user_id": log.user_id,
                "action_type": log.action_type,
                "previous_state": log.previous_state,
                "new_state": log.new_state,
                "details": json.loads(log.details) if log.details else {}
            }
            
            # Compute expected hash
            expected_hash = compute_hash(hash_data, previous_hash)
            
            # Verify hash matches
            if expected_hash != log.hash:
                return False
            
            # Verify previous hash matches
            if log.previous_hash != previous_hash:
                return False
            
            previous_hash = log.hash
        
        return True

audit_service = AuditService()
