"""
Email Utility

Helper functions for sending emails.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

def send_email(
    recipients: List[str],
    subject: str,
    content: str,
    content_type: str = "plain"
) -> bool:
    """
    Send an email using SMTP settings from config.
    
    Args:
        recipients: List of email addresses
        subject: Email subject
        content: Email body
        content_type: "plain" or "html"
        
    Returns:
        True if successful, False otherwise
    """
    if not settings.SMTP_SERVER or not settings.SMTP_EMAIL:
        logger.warning("SMTP settings not configured. Email not sent.")
        print(f"Mock Email: To={recipients}, Subject={subject}, Body={content[:50]}...")
        return False
        
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_EMAIL
        msg["To"] = ", ".join(recipients)
        
        part = MIMEText(content, content_type)
        msg.attach(part)
        
        # Connect to SMTP server
        # Explicitly convert port to int if present, else default
        port = int(settings.SMTP_PORT) if settings.SMTP_PORT else 587
        
        with smtplib.SMTP(settings.SMTP_SERVER, port) as server:
            server.starttls()
            if settings.SMTP_PASSWORD:
                server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
            server.send_message(msg)
            
        logger.info(f"Email sent to {recipients}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        # In production we might want to re-raise or handle differently
        return False

def send_invitation_email(email: str, mission_name: str, role: str):
    """
    Send a mission invitation email.
    """
    # Construct registration link
    # Assuming frontend URL is in settings or default
    base_url = settings.FRONTEND_URL or "http://localhost:3000"
    register_url = f"{base_url}/register?email={email}&invite_mission={mission_name}&invite_role={role}"
    
    subject = f"Invitation to join mission: {mission_name}"
    
    html_content = f"""
    <html>
        <body>
            <h2>Hello!</h2>
            <p>You have been invited to join the mission <strong>{mission_name}</strong> as a <strong>{role}</strong>.</p>
            <p>Please click the link below to register and accept the invitation:</p>
            <p><a href="{register_url}">Join Mission</a></p>
            <p>If you did not expect this invitation, please ignore this email.</p>
        </body>
    </html>
    """
    
    return send_email([email], subject, html_content, "html")
