import logging
import random
import smtplib
import socket
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def generate_otp() -> str:
    return str(random.randint(100000, 999999))


def send_otp_email(to_email: str, otp: str) -> bool:
    """Send OTP email via Gmail SMTP with retries."""
    sender_email = settings.SMTP_USER
    sender_pass = settings.SMTP_PASS.replace(" ", "") if settings.SMTP_PASS else ""

    if not sender_email or not sender_pass:
        logger.error("SMTP_USER or SMTP_PASS not set in .env")
        return False

    # ====== BUILD MESSAGE ======
    msg = MIMEMultipart("alternative")
    msg["From"] = f"DocuExtract AI <{sender_email}>"
    msg["To"] = to_email
    msg["Subject"] = "Your DocuExtract AI Verification Code"

    text_body = (
        f"DocuExtract AI\n"
        f"Your verification code is: {otp}\n\n"
        f"This code expires in 10 minutes.\n"
        f"If you didn't request this, ignore this email."
    )

    html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#0b1220;font-family:'Segoe UI',Arial,sans-serif;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#0b1220;padding:40px 20px;">
    <tr><td align="center">
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="520" style="max-width:520px;background:#0f172a;border-radius:16px;border:1px solid rgba(148,163,184,.15);overflow:hidden;">
        <tr><td style="background:linear-gradient(135deg,#06b6d4,#8b5cf6);padding:28px;text-align:center;">
          <div style="font-size:26px;font-weight:800;color:#ffffff;">DocuExtract AI</div>
          <div style="font-size:11px;color:rgba(255,255,255,.75);letter-spacing:.25em;margin-top:6px;text-transform:uppercase;">Document Intelligence</div>
        </td></tr>
        <tr><td style="padding:36px 32px 24px;">
          <h1 style="margin:0 0 12px;font-size:22px;font-weight:700;color:#e2e8f0;">Verify your email</h1>
          <p style="margin:0 0 24px;font-size:14px;line-height:1.6;color:#94a3b8;">Enter the code below to complete your signup. This code is valid for <strong style="color:#e2e8f0;">10 minutes</strong>.</p>
          <div style="background:rgba(34,211,238,.08);border:1px solid rgba(34,211,238,.3);border-radius:12px;padding:24px 20px;text-align:center;margin-bottom:24px;">
            <div style="font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:#22d3ee;font-weight:600;margin-bottom:10px;">Your verification code</div>
            <div style="font-size:38px;font-weight:800;letter-spacing:.3em;color:#ffffff;font-family:'Courier New',monospace;">{otp}</div>
          </div>
          <p style="margin:0;font-size:12px;line-height:1.6;color:#64748b;">If you didn't request this, you can safely ignore this email.</p>
        </td></tr>
        <tr><td style="padding:20px 32px 28px;border-top:1px solid rgba(148,163,184,.1);">
          <div style="font-size:11px;line-height:1.6;color:#475569;text-align:center;">© 2026 DocuExtract AI · Built by Tanush Sharma<br>This is an automated message — please do not reply.</div>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    # ====== SEND (SSL on 465 = faster than TLS on 587) ======
    for attempt in range(1, 3):
        try:
            logger.info(f"Sending OTP to {to_email} (attempt {attempt}/2)")
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
                server.login(sender_email, sender_pass)
                server.send_message(msg)
            logger.info(f"OTP email sent successfully to {to_email}")
            return True
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP auth failed: {e}")
            return False
        except (socket.timeout, TimeoutError) as e:
            logger.warning(f"Timeout attempt {attempt}/2: {e}")
            continue
        except Exception as e:
            logger.warning(f"Attempt {attempt}/2 failed: {type(e).__name__}: {e}")
            continue

    logger.error(f"Failed to send OTP to {to_email} after 2 attempts")
    return False


def send_otp_email_async(to_email: str, otp: str):
    """
    Fire-and-forget: sends email in a background thread.
    Returns IMMEDIATELY so the user doesn't wait.
    """
    def _worker():
        try:
            send_otp_email(to_email, otp)
        except Exception as e:
            logger.error(f"Background email task crashed: {e}")

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    logger.info(f"OTP email queued in background for {to_email}")