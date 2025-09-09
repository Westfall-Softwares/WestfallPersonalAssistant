"""
Email service module for the Westfall Personal Assistant.

This module provides email functionality including sending, receiving,
and managing email accounts.
"""

import smtplib
import imaplib
import email
import logging
from typing import List, Dict, Optional, Any, TYPE_CHECKING
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

# Type checking imports (prevent circular imports)
if TYPE_CHECKING:
    from core.message_handler import MessageHandler

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending and receiving emails."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize email service.
        
        Args:
            config: Email configuration dictionary
        """
        self.config = config or {}
        self.smtp_server = None
        self.imap_server = None
        
    def configure_smtp(self, smtp_host: str, smtp_port: int, 
                      username: str, password: str, use_tls: bool = True):
        """
        Configure SMTP settings for sending emails.
        
        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            username: Email username
            password: Email password
            use_tls: Whether to use TLS encryption
        """
        self.config.update({
            'smtp_host': smtp_host,
            'smtp_port': smtp_port,
            'username': username,
            'password': password,
            'use_tls': use_tls
        })
    
    def configure_imap(self, imap_host: str, imap_port: int = 993,
                      username: str = None, password: str = None, use_ssl: bool = True):
        """
        Configure IMAP settings for receiving emails.
        
        Args:
            imap_host: IMAP server hostname
            imap_port: IMAP server port
            username: Email username (defaults to SMTP username)
            password: Email password (defaults to SMTP password)
            use_ssl: Whether to use SSL encryption
        """
        self.config.update({
            'imap_host': imap_host,
            'imap_port': imap_port,
            'imap_username': username or self.config.get('username'),
            'imap_password': password or self.config.get('password'),
            'use_ssl': use_ssl
        })
    
    def send_email(self, to_address: str, subject: str, body: str,
                  from_address: str = None, cc: List[str] = None, 
                  bcc: List[str] = None, attachments: List[str] = None) -> bool:
        """
        Send an email.
        
        Args:
            to_address: Recipient email address
            subject: Email subject
            body: Email body
            from_address: Sender email (defaults to configured username)
            cc: CC recipients
            bcc: BCC recipients
            attachments: List of file paths to attach
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_address or self.config.get('username')
            msg['To'] = to_address
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {os.path.basename(file_path)}'
                            )
                            msg.attach(part)
            
            # Connect to server and send
            server = smtplib.SMTP(self.config['smtp_host'], self.config['smtp_port'])
            
            if self.config.get('use_tls', True):
                server.starttls()
            
            server.login(self.config['username'], self.config['password'])
            
            recipients = [to_address]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            text = msg.as_string()
            server.sendmail(msg['From'], recipients, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_address}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def get_unread_emails(self, folder: str = 'INBOX', limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get unread emails from specified folder.
        
        Args:
            folder: Email folder to check
            limit: Maximum number of emails to retrieve
            
        Returns:
            List of email dictionaries
        """
        try:
            if not self._connect_imap():
                return []
            
            # Select folder
            self.imap_server.select(folder)
            
            # Search for unread emails
            status, messages = self.imap_server.search(None, 'UNSEEN')
            
            if status != 'OK':
                return []
            
            email_ids = messages[0].split()
            emails = []
            
            # Get the most recent emails up to limit
            for email_id in email_ids[-limit:]:
                try:
                    status, msg_data = self.imap_server.fetch(email_id, '(RFC822)')
                    
                    if status == 'OK':
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)
                        
                        # Extract email info
                        email_info = {
                            'id': email_id.decode(),
                            'subject': email_message['Subject'],
                            'from': email_message['From'],
                            'date': email_message['Date'],
                            'body': self._extract_body(email_message)
                        }
                        emails.append(email_info)
                        
                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {e}")
                    continue
            
            self._disconnect_imap()
            return emails
            
        except Exception as e:
            logger.error(f"Failed to get unread emails: {e}")
            return []
    
    def mark_as_read(self, email_id: str, folder: str = 'INBOX') -> bool:
        """
        Mark an email as read.
        
        Args:
            email_id: Email ID to mark as read
            folder: Email folder
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._connect_imap():
                return False
            
            self.imap_server.select(folder)
            self.imap_server.store(email_id, '+FLAGS', '\\Seen')
            self._disconnect_imap()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark email as read: {e}")
            return False
    
    def _connect_imap(self) -> bool:
        """Connect to IMAP server."""
        try:
            if self.config.get('use_ssl', True):
                self.imap_server = imaplib.IMAP4_SSL(
                    self.config['imap_host'], 
                    self.config.get('imap_port', 993)
                )
            else:
                self.imap_server = imaplib.IMAP4(
                    self.config['imap_host'], 
                    self.config.get('imap_port', 143)
                )
            
            username = self.config.get('imap_username') or self.config.get('username')
            password = self.config.get('imap_password') or self.config.get('password')
            
            self.imap_server.login(username, password)
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to IMAP server: {e}")
            return False
    
    def _disconnect_imap(self):
        """Disconnect from IMAP server."""
        if self.imap_server:
            try:
                self.imap_server.close()
                self.imap_server.logout()
            except:
                pass
            self.imap_server = None
    
    def _extract_body(self, email_message) -> str:
        """Extract text body from email message."""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
        else:
            body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        return body
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test email service connection.
        
        Returns:
            Dictionary with connection test results
        """
        results = {
            'smtp_connected': False,
            'imap_connected': False,
            'errors': []
        }
        
        # Test SMTP
        try:
            server = smtplib.SMTP(self.config['smtp_host'], self.config['smtp_port'])
            if self.config.get('use_tls', True):
                server.starttls()
            server.login(self.config['username'], self.config['password'])
            server.quit()
            results['smtp_connected'] = True
        except Exception as e:
            results['errors'].append(f"SMTP connection failed: {e}")
        
        # Test IMAP
        try:
            if self._connect_imap():
                results['imap_connected'] = True
                self._disconnect_imap()
        except Exception as e:
            results['errors'].append(f"IMAP connection failed: {e}")
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get email service status.
        
        Returns:
            Status dictionary
        """
        return {
            'configured': bool(self.config.get('smtp_host') and self.config.get('username')),
            'smtp_configured': bool(self.config.get('smtp_host')),
            'imap_configured': bool(self.config.get('imap_host')),
            'last_test': None  # Could track last connection test
        }


# Convenience function to get a configured email service
def get_email_service(config: Optional[Dict[str, Any]] = None) -> EmailService:
    """
    Get a configured email service instance.
    
    Args:
        config: Email configuration
        
    Returns:
        EmailService instance
    """
    return EmailService(config)