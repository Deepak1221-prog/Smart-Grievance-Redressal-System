import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from ..config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class NotificationService:
    @staticmethod
    def send_email(to_email: str, subject: str, body: str, html: bool = True):
        """Send email notification"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = settings.SMTP_FROM
            message["To"] = to_email
            
            if html:
                message.attach(MIMEText(body, "html"))
            else:
                message.attach(MIMEText(body, "plain"))
            
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(message)
            
            logger.info(f"Email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return False
    
    @staticmethod
    def send_complaint_confirmation(to_email: str, complaint_id: str, title: str):
        """Send complaint submission confirmation"""
        subject = f"Complaint Registered - {complaint_id}"
        body = f"""
        <html>
            <body>
                <h2>Complaint Registered Successfully</h2>
                <p>Your complaint has been registered with ID: <strong>{complaint_id}</strong></p>
                <p><strong>Title:</strong> {title}</p>
                <p>You can track your complaint status using the complaint ID.</p>
                <p>Thank you for using {settings.APP_NAME}</p>
            </body>
        </html>
        """
        return NotificationService.send_email(to_email, subject, body)
    
    @staticmethod
    def send_status_update(to_email: str, complaint_id: str, old_status: str, new_status: str):
        """Send complaint status update notification"""
        subject = f"Complaint Update - {complaint_id}"
        body = f"""
        <html>
            <body>
                <h2>Complaint Status Updated</h2>
                <p>Complaint ID: <strong>{complaint_id}</strong></p>
                <p>Status changed from <strong>{old_status}</strong> to <strong>{new_status}</strong></p>
                <p>Track your complaint at: {settings.FRONTEND_URL}</p>
            </body>
        </html>
        """
        return NotificationService.send_email(to_email, subject, body)
    
    @staticmethod
    def send_assignment_notification(to_email: str, complaint_id: str, title: str):
        """Send complaint assignment notification to officer"""
        subject = f"New Complaint Assigned - {complaint_id}"
        body = f"""
        <html>
            <body>
                <h2>New Complaint Assigned</h2>
                <p>A new complaint has been assigned to you:</p>
                <p><strong>Complaint ID:</strong> {complaint_id}</p>
                <p><strong>Title:</strong> {title}</p>
                <p>Please review and take action.</p>
                <p>Access dashboard at: {settings.FRONTEND_URL}</p>
            </body>
        </html>
        """
        return NotificationService.send_email(to_email, subject, body)

notification_service = NotificationService()
