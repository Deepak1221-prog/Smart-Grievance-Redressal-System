import hashlib
import json
from datetime import datetime
import secrets
import string

def generate_complaint_id() -> str:
    """Generate unique complaint ID in format SGRS-YYYY-MM-XXXXX"""
    now = datetime.now()
    random_num = ''.join(secrets.choice(string.digits) for _ in range(5))
    return f"SGRS-{now.year}-{now.month:02d}-{random_num}"

def generate_verification_token() -> str:
    """Generate random verification token"""
    return secrets.token_urlsafe(32)

def compute_hash(data: dict, previous_hash: str = "") -> str:
    """Compute SHA-256 hash for blockchain-inspired audit log"""
    hash_string = json.dumps(data, sort_keys=True) + previous_hash
    return hashlib.sha256(hash_string.encode()).hexdigest()

def validate_file_type(filename: str, allowed_types: list) -> bool:
    """Validate file extension"""
    return any(filename.lower().endswith(ext) for ext in allowed_types)

def get_file_extension(filename: str) -> str:
    """Get file extension"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
