import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict
import asyncio
import logging

from core.config import settings
from services.email_service import email_service

logger = logging.getLogger(__name__)


class OTPService:
    def __init__(self):
        # In-memory storage for OTPs (in production, use Redis or database)
        self._otp_storage: Dict[str, Dict] = {}
        self.expire_minutes = settings.OTP_EXPIRE_MINUTES
        self.otp_length = settings.OTP_LENGTH

    def generate_otp(self) -> str:
        """Generate a random OTP code."""
        return "".join(random.choices(string.digits, k=self.otp_length))

    def _get_expiry_time(self) -> datetime:
        """Get the expiry time for a new OTP."""
        return datetime.utcnow() + timedelta(minutes=self.expire_minutes)

    async def send_otp(self, email: str, full_name: str = "") -> bool:
        """
        Generate and send OTP to the specified email.

        Args:
            email: Email address to send OTP to
            full_name: Full name of the recipient (optional)

        Returns:
            bool: True if OTP was sent successfully, False otherwise
        """
        try:
            # Generate new OTP
            otp_code = self.generate_otp()
            expiry_time = self._get_expiry_time()

            # Store OTP in memory
            self._otp_storage[email] = {
                "code": otp_code,
                "expires_at": expiry_time,
                "attempts": 0,
                "verified": False,
            }

            # Send OTP via email
            success = await email_service.send_otp_email(email, otp_code, full_name)

            if success:
                logger.info(f"OTP sent successfully to {email}")
                return True
            else:
                # Remove from storage if email failed
                self._otp_storage.pop(email, None)
                logger.error(f"Failed to send OTP to {email}")
                return False

        except Exception as e:
            logger.error(f"Error sending OTP to {email}: {str(e)}")
            return False

    def verify_otp(self, email: str, otp_code: str) -> Dict[str, any]:
        """
        Verify the OTP code for the given email.

        Args:
            email: Email address
            otp_code: OTP code to verify

        Returns:
            dict: Verification result with status and message
        """
        try:
            # Check if OTP exists for this email
            if email not in self._otp_storage:
                return {
                    "success": False,
                    "message": "No OTP found for this email. Please request a new one.",
                    "error_code": "OTP_NOT_FOUND",
                }

            otp_data = self._otp_storage[email]

            # Check if already verified
            if otp_data.get("verified", False):
                return {
                    "success": False,
                    "message": "This OTP has already been used. Please request a new one.",
                    "error_code": "OTP_ALREADY_USED",
                }

            # Check if expired
            if datetime.utcnow() > otp_data["expires_at"]:
                # Clean up expired OTP
                self._otp_storage.pop(email, None)
                return {
                    "success": False,
                    "message": "OTP has expired. Please request a new one.",
                    "error_code": "OTP_EXPIRED",
                }

            # Check attempt limit (max 5 attempts)
            if otp_data["attempts"] >= 5:
                # Clean up after too many attempts
                self._otp_storage.pop(email, None)
                return {
                    "success": False,
                    "message": "Too many failed attempts. Please request a new OTP.",
                    "error_code": "TOO_MANY_ATTEMPTS",
                }

            # Increment attempt counter
            otp_data["attempts"] += 1

            # Verify the code
            if otp_code == otp_data["code"]:
                # Mark as verified
                otp_data["verified"] = True
                logger.info(f"OTP verified successfully for {email}")
                return {
                    "success": True,
                    "message": "Email verified successfully!",
                    "error_code": None,
                }
            else:
                remaining_attempts = 5 - otp_data["attempts"]
                return {
                    "success": False,
                    "message": f"Invalid OTP code. {remaining_attempts} attempts remaining.",
                    "error_code": "INVALID_OTP",
                    "remaining_attempts": remaining_attempts,
                }

        except Exception as e:
            logger.error(f"Error verifying OTP for {email}: {str(e)}")
            return {
                "success": False,
                "message": "An error occurred while verifying the OTP. Please try again.",
                "error_code": "VERIFICATION_ERROR",
            }

    def is_email_verified(self, email: str) -> bool:
        """
        Check if an email has been verified.

        Args:
            email: Email address to check

        Returns:
            bool: True if email is verified, False otherwise
        """
        if email not in self._otp_storage:
            return False

        otp_data = self._otp_storage[email]

        # Check if verified and not expired
        if (
            otp_data.get("verified", False)
            and datetime.utcnow() <= otp_data["expires_at"]
        ):
            return True

        return False

    def cleanup_expired_otps(self):
        """Remove expired OTPs from storage."""
        current_time = datetime.utcnow()
        expired_emails = [
            email
            for email, data in self._otp_storage.items()
            if current_time > data["expires_at"]
        ]

        for email in expired_emails:
            self._otp_storage.pop(email, None)
            logger.info(f"Cleaned up expired OTP for {email}")

    def get_otp_status(self, email: str) -> Dict[str, any]:
        """
        Get the current status of OTP for an email.

        Args:
            email: Email address

        Returns:
            dict: OTP status information
        """
        if email not in self._otp_storage:
            return {
                "exists": False,
                "verified": False,
                "expired": True,
                "attempts": 0,
                "remaining_attempts": 5,
            }

        otp_data = self._otp_storage[email]
        current_time = datetime.utcnow()
        is_expired = current_time > otp_data["expires_at"]

        return {
            "exists": True,
            "verified": otp_data.get("verified", False),
            "expired": is_expired,
            "attempts": otp_data.get("attempts", 0),
            "remaining_attempts": max(0, 5 - otp_data.get("attempts", 0)),
            "expires_at": otp_data["expires_at"].isoformat()
            if not is_expired
            else None,
        }


# Create a global instance
otp_service = OTPService()


# Background task to clean up expired OTPs every 5 minutes
async def cleanup_expired_otps_task():
    """Background task to periodically clean up expired OTPs."""
    while True:
        try:
            otp_service.cleanup_expired_otps()
            await asyncio.sleep(300)  # 5 minutes
        except Exception as e:
            logger.error(f"Error in OTP cleanup task: {str(e)}")
            await asyncio.sleep(300)  # Continue after error
