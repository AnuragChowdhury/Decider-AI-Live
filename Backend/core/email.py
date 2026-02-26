"""
Brevo (Sendinblue) HTTP API email helper — sends OTP emails for registration and password reset.
Uses standard `requests` via Port 443 to bypass Render's strict SMTP blocking.
"""
import os
import requests

# Requires a free account from brevo.com
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
MAIL_FROM = os.getenv("MAIL_FROM", "noreply@decider-ai.com")
SENDER_NAME = "DECIDER AI"


def _send_email_via_brevo(to_email: str, subject: str, html_content: str, full_name: str) -> None:
    """Helper method to send email via Brevo's v3 API."""
    if not BREVO_API_KEY:
        print(f"[EMAIL ERROR] BREVO_API_KEY is not set. Cannot send email to {to_email}", flush=True)
        raise ValueError("Email delivery is disabled because BREVO_API_KEY is missing.")

    url = "https://api.brevo.com/v3/smtp/email"
    
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    
    payload = {
        "sender": {
            "name": SENDER_NAME,
            "email": MAIL_FROM
        },
        "to": [
            {
                "email": to_email,
                "name": full_name or to_email.split("@")[0]
            }
        ],
        "subject": subject,
        "htmlContent": html_content
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"[EMAIL] Successfully sent '{subject}' to {to_email} via Brevo HTTP API", flush=True)
    except requests.exceptions.RequestException as e:
        print(f"[EMAIL ERROR] HTTP Request failed sending to {to_email}: {e}", flush=True)
        try:
            print(f"[EMAIL ERROR DETAILS] {response.text}", flush=True)
        except Exception:
            pass
        raise ValueError(f"Brevo HTTP API Error: {str(e)}")


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

    _send_email_via_brevo(to_email, subject, html_body, full_name)


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

    _send_email_via_brevo(to_email, subject, html_body, full_name)

