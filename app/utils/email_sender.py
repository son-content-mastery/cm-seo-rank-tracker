import smtplib
import logging
import email.mime.text
import email.mime.multipart
import email.mime.base
import email.encoders
from typing import Dict, List, Optional
from jinja2 import Template
from app.config import Config

logger = logging.getLogger(__name__)


class EmailSender:
    """Handle email sending functionality"""
    
    def __init__(self, gmail_user: str, gmail_password: str, smtp_server: str = 'smtp.gmail.com', smtp_port: int = 587):
        self.gmail_user = gmail_user
        self.gmail_password = gmail_password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
    
    def send_email(self, to_email: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
        """
        Send an email with HTML content
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML content of the email
            text_body: Plain text fallback (optional)
            
        Returns:
            Boolean indicating success
        """
        try:
            # Create message
            msg = email.mime.multipart.MIMEMultipart('alternative')
            msg['From'] = f"{Config.EMAIL_CONFIG['sender_name']} <{self.gmail_user}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text part if provided
            if text_body:
                text_part = email.mime.text.MIMEText(text_body, 'plain')
                msg.attach(text_part)
            
            # Add HTML part
            html_part = email.mime.text.MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.gmail_user, self.gmail_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_weekly_report(self, ranking_data: List[Dict], recipient: str) -> bool:
        """
        Send weekly ranking report
        
        Args:
            ranking_data: List of ranking data dictionaries
            recipient: Recipient email address
            
        Returns:
            Boolean indicating success
        """
        from app.utils.report_generator import generate_weekly_report_html
        
        # Generate report content
        html_content = generate_weekly_report_html(ranking_data)
        
        # Create subject with summary
        improvements = sum(1 for item in ranking_data if item.get('change_direction') == 'up')
        declines = sum(1 for item in ranking_data if item.get('change_direction') == 'down')
        
        subject = f"Weekly SEO Report - {improvements} Improvements, {declines} Declines"
        
        return self.send_email(recipient, subject, html_content)

def smtp_gmail_setup() -> EmailSender:
    """
    Create and return configured EmailSender instance
    
    Returns:
        Configured EmailSender instance
    """
    gmail_user = Config.GMAIL_USER
    gmail_password = Config.GMAIL_PASSWORD
    smtp_server = Config.SMTP_SERVER
    smtp_port = Config.SMTP_PORT
    
    if not gmail_user or not gmail_password:
        raise ValueError("Gmail credentials not configured")
    
    return EmailSender(gmail_user, gmail_password, smtp_server, smtp_port)