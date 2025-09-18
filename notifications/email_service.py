"""Email notification service for iClicker Evade.

This module provides Gmail-based email notifications for question alerts,
including screenshot attachments and formatted message content.
"""

import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from typing import Optional
import logging


class EmailNotificationService:
    """Gmail-based email notification service.

    Handles sending email notifications with question screenshots when
    iClicker questions are detected. Uses Gmail SMTP with app password
    authentication for secure delivery.

    Attributes:
        sender_email (str): Gmail address to send from
        sender_password (str): Gmail app password for authentication
        smtp_server (str): Gmail SMTP server address
        smtp_port (int): Gmail SMTP server port
    """

    def __init__(self, sender_email: str, sender_password: str) -> None:
        """Initialize the email notification service.

        Args:
            sender_email: Gmail address to send notifications from
            sender_password: Gmail app password for authentication

        Raises:
            ValueError: If sender_email or sender_password is empty
        """
        if not sender_email or not sender_password:
            raise ValueError("Both sender_email and sender_password are required")

        self.sender_email = sender_email
        self.sender_password = sender_password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

        # Set up logging for this service
        self.logger = logging.getLogger(__name__)

    def send_question_alert(
        self,
        recipient_email: str,
        question_text: str,
        screenshot_path: str
    ) -> bool:
        """Send a question alert email with screenshot attachment.

        Creates and sends a formatted email notification when an iClicker
        question is detected. Includes the question text in the email body
        and attaches the screenshot for visual context.

        Args:
            recipient_email: Email address to send the alert to
            question_text: Text content extracted from the question
            screenshot_path: Path to the screenshot file to attach

        Returns:
            True if email was sent successfully, False otherwise

        Example:
            >>> service = EmailNotificationService("sender@gmail.com", "app_password")
            >>> success = service.send_question_alert(
            ...     "student@example.com",
            ...     "What is 2+2? A) 3 B) 4 C) 5",
            ...     "questions/question_20240918_143052.png"
            ... )
            >>> print(f"Email sent: {success}")
            Email sent: True
        """
        try:
            # Create the email message
            msg = self._create_question_message(
                recipient_email,
                question_text,
                screenshot_path
            )

            # Send via Gmail SMTP
            self._send_via_smtp(msg)

            self.logger.info(f"Successfully sent question alert to {recipient_email}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send email to {recipient_email}: {e}")
            return False

    def _create_question_message(
        self,
        recipient_email: str,
        question_text: str,
        screenshot_path: str
    ) -> MIMEMultipart:
        """Create a formatted email message for question alerts.

        Args:
            recipient_email: Email address to send to
            question_text: Question content to include in email
            screenshot_path: Path to screenshot file

        Returns:
            Formatted MIMEMultipart email message
        """
        # Create multipart message
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = recipient_email
        msg['Subject'] = self._generate_subject()

        # Create email body
        body = self._generate_email_body(question_text)
        msg.attach(MIMEText(body, 'plain'))

        # Attach screenshot if it exists
        if os.path.exists(screenshot_path):
            self._attach_screenshot(msg, screenshot_path)
        else:
            self.logger.warning(f"Screenshot not found: {screenshot_path}")

        return msg

    def _generate_subject(self) -> str:
        """Generate a timestamped subject line for question alerts.

        Returns:
            Formatted subject line with current time
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        return f"iClicker Question Alert - {timestamp}"

    def _generate_email_body(self, question_text: str) -> str:
        """Generate the email body content for question alerts.

        Args:
            question_text: The extracted question content

        Returns:
            Formatted email body as a string
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return f"""🚨 iClicker Question Detected! 🚨

Time: {timestamp}

Question Content:
{question_text}

Please see the attached screenshot for the complete question and answer options.

You can respond to this question in your iClicker session.

---
Sent automatically by iClicker Evade
For support: https://github.com/username/iclicker-evade"""

    def _attach_screenshot(self, msg: MIMEMultipart, screenshot_path: str) -> None:
        """Attach a screenshot file to the email message.

        Args:
            msg: Email message to attach the screenshot to
            screenshot_path: Path to the screenshot file

        Raises:
            IOError: If screenshot file cannot be read
        """
        try:
            with open(screenshot_path, 'rb') as f:
                img_data = f.read()

            image = MIMEImage(img_data)
            image.add_header(
                'Content-Disposition',
                f'attachment; filename={os.path.basename(screenshot_path)}'
            )
            msg.attach(image)

            self.logger.debug(f"Attached screenshot: {screenshot_path}")

        except IOError as e:
            self.logger.error(f"Failed to attach screenshot {screenshot_path}: {e}")
            raise

    def _send_via_smtp(self, msg: MIMEMultipart) -> None:
        """Send an email message via Gmail SMTP.

        Args:
            msg: The email message to send

        Raises:
            smtplib.SMTPException: If SMTP operation fails
            smtplib.SMTPAuthenticationError: If authentication fails
        """
        try:
            # Connect to Gmail SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Enable encryption

            # Authenticate with app password
            server.login(self.sender_email, self.sender_password)

            # Send the message
            server.send_message(msg)
            server.quit()

            self.logger.debug("Email sent successfully via SMTP")

        except smtplib.SMTPAuthenticationError as e:
            self.logger.error(f"SMTP authentication failed: {e}")
            raise
        except smtplib.SMTPException as e:
            self.logger.error(f"SMTP error occurred: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during SMTP send: {e}")
            raise

    def test_connection(self) -> bool:
        """Test the SMTP connection and authentication.

        Attempts to connect to Gmail SMTP and authenticate without
        sending an email. Useful for validating credentials.

        Returns:
            True if connection and authentication successful, False otherwise
        """
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.quit()

            self.logger.info("SMTP connection test successful")
            return True

        except Exception as e:
            self.logger.error(f"SMTP connection test failed: {e}")
            return False


def create_email_service(sender_email: Optional[str], sender_password: Optional[str]) -> Optional[EmailNotificationService]:
    """Factory function to create an EmailNotificationService.

    Args:
        sender_email: Gmail address (can be None to disable email)
        sender_password: Gmail app password (can be None to disable email)

    Returns:
        EmailNotificationService instance if credentials provided, None otherwise
    """
    if sender_email and sender_password:
        try:
            return EmailNotificationService(sender_email, sender_password)
        except ValueError as e:
            logging.error(f"Failed to create email service: {e}")
            return None
    return None