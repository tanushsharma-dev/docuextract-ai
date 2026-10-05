import logging
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def generate_otp() -> str:
    return str(random.randint(100000, 999999))


def send_otp_email(to_email: str, otp: str) -> bool:
    """Professional HTML email ke saath OTP bhejo."""
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"DocuExtract AI <{settings.SMTP_USER}>"
        msg["To"] = to_email
        msg["Subject"] = "🔐 DocuExtract AI — Email Verification Code"

        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;background:#0f172a;color:#e2e8f0;border-radius:16px;overflow:hidden">
          <div style="background:linear-gradient(135deg,#06b6d4,#a855f7);padding:24px;text-align:center">
            <h1 style="margin:0;color:#fff;font-size:22px">📄 DocuExtract AI</h1>
            <p style="margin:4px 0 0;color:#e0f2fe;font-size:13px">Document Intelligence Platform</p>
          </div>
          <div style="padding:32px;text-align:center">
            <p style="font-size:15px">Aapka verification code:</p>
            <div style="font-size:34px;font-weight:bold;letter-spacing:8px;color:#22d3ee;background:#1e293b;border:1px dashed #334155;border-radius:12px;padding:16px;margin:20px 0">{otp}</div>
            <p style="font-size:13px;color:#94a3b8">Ye code <b>10 minute</b> tak valid hai.<br>Agar aapne signup nahi kiya, toh is email ko ignore karein.</p>
          </div>
          <div style="padding:16px;text-align:center;font-size:11px;color:#64748b;border-top:1px solid #1e293b">
            © 2026 DocuExtract AI — Secure Document Processing
          </div>
        </div>
        """
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.send_message(msg)

        logger.info(f"OTP email sent to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False