import asyncio
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Dict
import logging
import os

from core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[Dict[str, str]]] = None,
    ) -> bool:
        """
        Send an email using SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)
            attachments: List of attachments with format:
                [{"file_path": "/path/to/file", "filename": "display_name.pdf"}]

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("mixed")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email

            # Create alternative container for text/html content
            content_container = MIMEMultipart("alternative")

            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, "plain")
                content_container.attach(text_part)

            # Add HTML content
            html_part = MIMEText(html_content, "html")
            content_container.attach(html_part)

            # Attach the content container to the main message
            message.attach(content_container)

            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    file_path = attachment.get("file_path")
                    filename = attachment.get("filename")

                    if file_path and os.path.exists(file_path):
                        try:
                            with open(file_path, "rb") as attachment_file:
                                # Create MIMEBase object
                                part = MIMEBase("application", "octet-stream")
                                part.set_payload(attachment_file.read())

                                # Encode file in ASCII characters to send by email
                                encoders.encode_base64(part)

                                # Add header as key/value pair to attachment part
                                part.add_header(
                                    "Content-Disposition",
                                    f"attachment; filename= {filename or os.path.basename(file_path)}",
                                )

                                # Attach the part to message
                                message.attach(part)
                                logger.info(f"Attached file: {filename or file_path}")
                        except Exception as e:
                            logger.error(f"Failed to attach file {file_path}: {str(e)}")
                    else:
                        logger.warning(f"Attachment file not found: {file_path}")

            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                start_tls=True,
                username=self.smtp_username,
                password=self.smtp_password,
            )

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    async def send_otp_email(
        self, to_email: str, otp_code: str, full_name: str = ""
    ) -> bool:
        """
        Send OTP verification email.

        Args:
            to_email: Recipient email address
            otp_code: OTP code to send
            full_name: Recipient's full name (optional)

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        subject = "Email Verification - Your OTP Code"

        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Email Verification</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .container {{
                    background-color: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #6366f1;
                    margin-bottom: 10px;
                }}
                .title {{
                    font-size: 28px;
                    font-weight: bold;
                    color: #1f2937;
                    margin-bottom: 10px;
                }}
                .subtitle {{
                    color: #6b7280;
                    font-size: 16px;
                }}
                .otp-container {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    margin: 30px 0;
                }}
                .otp-code {{
                    font-size: 36px;
                    font-weight: bold;
                    color: white;
                    letter-spacing: 8px;
                    margin: 10px 0;
                    font-family: 'Courier New', monospace;
                }}
                .otp-label {{
                    color: #e5e7eb;
                    font-size: 14px;
                    margin-bottom: 10px;
                }}
                .instructions {{
                    background-color: #f3f4f6;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .warning {{
                    background-color: #fef3cd;
                    border: 1px solid #fbbf24;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                    color: #92400e;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e5e7eb;
                    color: #6b7280;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🏢 HR Platform</div>
                    <h1 class="title">Email Verification</h1>
                    <p class="subtitle">
                        {"Hello " + full_name + "!" if full_name else "Hello!"}
                        Please verify your email address to continue with your job application.
                    </p>
                </div>

                <div class="otp-container">
                    <div class="otp-label">Your verification code is:</div>
                    <div class="otp-code">{otp_code}</div>
                </div>

                <div class="instructions">
                    <h3 style="margin-top: 0; color: #374151;">How to use this code:</h3>
                    <ol style="margin: 0; padding-left: 20px;">
                        <li>Return to the job application form</li>
                        <li>Enter this 6-digit code in the verification field</li>
                        <li>Complete your application</li>
                    </ol>
                </div>

                <div class="warning">
                    <strong>⚠️ Important:</strong> This code will expire in 10 minutes for security reasons. 
                    If you didn't request this verification, please ignore this email.
                </div>

                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>© 2024 HR Platform. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Create text content as fallback
        text_content = f"""
        Email Verification - HR Platform

        {"Hello " + full_name + "!" if full_name else "Hello!"}

        Your verification code is: {otp_code}

        Please enter this code in the job application form to verify your email address.

        This code will expire in 10 minutes.

        If you didn't request this verification, please ignore this email.

        ---
        HR Platform
        This is an automated message. Please do not reply.
        """

        return await self.send_email(to_email, subject, html_content, text_content)


# Create a global instance
email_service = EmailService()
