import os
import requests

FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY", "")


def send_otp_sms(phone: str, otp: str) -> None:
    """Send OTP to an Indian mobile number via Fast2SMS bulk OTP route."""
    if not FAST2SMS_API_KEY:
        print("[SMS] FAST2SMS_API_KEY not set — skipping SMS delivery", flush=True)
        return

    # Normalize: strip country code, spaces, dashes
    cleaned = phone.replace("+91", "").replace(" ", "").replace("-", "").strip()
    if len(cleaned) != 10 or not cleaned.isdigit():
        print(f"[SMS] Invalid phone number format: {phone} — skipping", flush=True)
        return

    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        "route": "otp",
        "variables_values": otp,
        "numbers": cleaned,
    }
    headers = {
        "authorization": FAST2SMS_API_KEY,
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        result = resp.json()
        if result.get("return"):
            print(f"[SMS] OTP sent to {cleaned}", flush=True)
        else:
            print(f"[SMS ERROR] Fast2SMS response: {result}", flush=True)
    except Exception as e:
        print(f"[SMS ERROR] Exception sending SMS to {cleaned}: {e}", flush=True)
