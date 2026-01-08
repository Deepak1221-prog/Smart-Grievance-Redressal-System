from app.database import engine, Base
from app.models.user import User
from app.models.complaint import (
    Complaint, Attachment, Comment, AuditLog, Feedback, Notification
)

print("Dropping all tables...")
Base.metadata.drop_all(bind=engine)

print("Creating all tables...")
Base.metadata.create_all(bind=engine)

print("✅ Tables created successfully!")
