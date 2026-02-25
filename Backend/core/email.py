"""
Gmail SMTP email helper — sends OTP emails for password reset.
Uses smtplib (stdlib, no extra packages needed).
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
MAIL_FROM = os.getenv("MAIL_FROM", MAIL_USERNAME)


def send_reset_otp(to_email: str, otp: str, full_name: str = ""):
    """Send a password-reset OTP email."""
    subject = "Your Decider AI Password Reset Code"
    name = full_name or to_email.split("@")[0]

    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px;background:#0f0f0f;border-radius:16px;border:1px solid #222;">
        <div style="text-align:center;margin-bottom:24px;">
            <div style="display:inline-flex;align-items:center;gap:10px;">
                <div style="width:28px;height:28px;background:#fff;border-radius:8px;display:inline-block;"></div>
                <span style="color:#fff;font-size:18px;font-weight:700;letter-spacing:-0.5px;">DECIDER AI</span>
            </div>
        </div>
        <h2 style="color:#ffffff;font-size:20px;font-weight:700;margin-bottom:8px;">Password Reset Request</h2>
        <p style="color:#aaa;font-size:14px;margin-bottom:24px;">Hi {name}, use the code below to reset your password. It expires in <strong style="color:#fff;">15 minutes</strong>.</p>

        <div style="background:#1a1a1a;border:1px solid #333;border-radius:12px;padding:28px;text-align:center;margin-bottom:24px;">
            <span style="font-size:40px;font-weight:800;letter-spacing:12px;color:#3b82f6;font-family:monospace;">{otp}</span>
        </div>

        <p style="color:#555;font-size:12px;margin:0;">If you didn't request this, you can safely ignore this email. Your password won't change.</p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = MAIL_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(MAIL_FROM, to_email, msg.as_string())
        print(f"[EMAIL] OTP sent to {to_email}", flush=True)
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send OTP to {to_email}: {e}", flush=True)
        raise


def send_registration_otp(to_email: str, otp: str, full_name: str = ""):
    """Send account verification OTP email after registration."""
    subject = "Verify Your Decider AI Account"
    name = full_name or to_email.split("@")[0]

    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px;background:#0f0f0f;border-radius:16px;border:1px solid #222;">
        <div style="text-align:center;margin-bottom:24px;">
            <div style="display:inline-flex;align-items:center;gap:10px;">
                <div style="width:28px;height:28px;background:#fff;border-radius:8px;display:inline-block;"></div>
                <span style="color:#fff;font-size:18px;font-weight:700;letter-spacing:-0.5px;">DECIDER AI</span>
            </div>
        </div>
        <h2 style="color:#ffffff;font-size:20px;font-weight:700;margin-bottom:8px;">Verify Your Account</h2>
        <p style="color:#aaa;font-size:14px;margin-bottom:24px;">Hi {name}, welcome! Use the code below to verify your account. It expires in <strong style="color:#fff;">15 minutes</strong>.</p>

        <div style="background:#1a1a1a;border:1px solid #333;border-radius:12px;padding:28px;text-align:center;margin-bottom:24px;">
            <span style="font-size:40px;font-weight:800;letter-spacing:12px;color:#22c55e;font-family:monospace;">{otp}</span>
        </div>

        <p style="color:#555;font-size:12px;margin:0;">If you didn't create an account, you can safely ignore this email.</p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = MAIL_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(MAIL_FROM, to_email, msg.as_string())
        print(f"[EMAIL] Registration OTP sent to {to_email}", flush=True)
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send registration OTP to {to_email}: {e}", flush=True)
        raise

