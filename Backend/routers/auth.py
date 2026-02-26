from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from core import database, models, auth
from core.email import send_reset_otp, send_registration_otp
from core.sms import send_otp_sms
from pydantic import BaseModel, EmailStr
from typing import Optional
import os
import random
import string
from datetime import datetime, timedelta
import requests as http_requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

router = APIRouter(prefix="/auth", tags=["Authentication"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# ── Schemas ───────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class UserProfile(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None

    class Config:
        from_attributes = True

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

class GoogleTokenRequest(BaseModel):
    credential: str  # Google ID token from frontend

class VerifyRegistrationRequest(BaseModel):
    email: EmailStr
    otp: str

class ResendRegistrationOTPRequest(BaseModel):
    email: EmailStr


# ── Helpers ───────────────────────────────────────────────────────────────────

def _generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def _send_registration_otp(user: models.User, otp: str) -> None:
    """Send the registration OTP via email and (if phone exists) SMS."""
    send_registration_otp(to_email=user.email, otp=otp, full_name=user.full_name or "")
    if user.phone:
        send_otp_sms(phone=user.phone, otp=otp)


# ── Standard Auth ─────────────────────────────────────────────────────────────

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(database.get_db)):
    """Create unverified user account and send OTP to email (+ phone if provided)."""
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        if not db_user.is_verified:
            # Re-send OTP for unverified accounts
            otp = _generate_otp()
            db.query(models.RegistrationOTP).filter(
                models.RegistrationOTP.user_id == db_user.id,
                models.RegistrationOTP.used == False,
            ).update({"used": True})
            db.commit()
            reg_otp = models.RegistrationOTP(
                user_id=db_user.id,
                token=otp,
                expires_at=datetime.utcnow() + timedelta(minutes=15),
            )
            db.add(reg_otp)
            db.commit()

            try:
                _send_registration_otp(db_user, otp)
                return {"message": "OTP resent. Please verify your account.", "requires_verification": True, "email": user.email}
            except Exception as e:
                print(f"[AUTH ERROR] Failed to send registration email: {e}", flush=True)
                return {
                    "message": "Account exists, but Render is blocking email delivery (Port 465). Try logging in with Google.",
                    "requires_verification": True,
                    "email": user.email,
                    "email_failed": True
                }
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        phone=user.phone,
        gender=user.gender,
        occupation=user.occupation,
        is_verified=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate and send registration OTP
    otp = _generate_otp()
    reg_otp = models.RegistrationOTP(
        user_id=new_user.id,
        token=otp,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
    )
    db.add(reg_otp)
    db.commit()

    try:
        _send_registration_otp(new_user, otp)
        return {
            "message": "Account created. Please verify using the OTP sent to your email (and phone if provided).",
            "requires_verification": True,
            "email": user.email,
        }
    except Exception as e:
        print(f"[AUTH ERROR] Failed to send registration email: {e}", flush=True)
        # Registration succeeded, but email failed. Let the user know so they can try Resending later.
        return {
            "message": "Account created, but we temporarily failed to send the OTP email. Please try 'Resend OTP' later.",
            "requires_verification": True,
            "email": user.email,
            "email_failed": True
        }


@router.post("/verify-registration")
def verify_registration(request: VerifyRegistrationRequest, db: Session = Depends(database.get_db)):
    """Verify registration OTP. Marks the user as active."""
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    if user.is_verified:
        return {"message": "Account already verified. Please log in."}

    token_record = db.query(models.RegistrationOTP).filter(
        models.RegistrationOTP.user_id == user.id,
        models.RegistrationOTP.token == request.otp,
        models.RegistrationOTP.used == False,
        models.RegistrationOTP.expires_at > datetime.utcnow(),
    ).first()

    if not token_record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    token_record.used = True
    user.is_verified = True
    db.commit()

    return {"message": "Account verified successfully! You can now sign in."}


@router.post("/resend-registration-otp")
def resend_registration_otp(request: ResendRegistrationOTPRequest, db: Session = Depends(database.get_db)):
    """Resend registration OTP (rate-limiting not enforced here — add in prod)."""
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        return {"message": "If that account exists, an OTP has been resent."}
    if user.is_verified:
        return {"message": "Account already verified."}

    db.query(models.RegistrationOTP).filter(
        models.RegistrationOTP.user_id == user.id,
        models.RegistrationOTP.used == False,
    ).update({"used": True})
    db.commit()

    otp = _generate_otp()
    reg_otp = models.RegistrationOTP(
        user_id=user.id,
        token=otp,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
    )
    db.add(reg_otp)
    db.commit()

    try:
        _send_registration_otp(user, otp)
        return {"message": "OTP resent successfully."}
    except Exception as e:
        print(f"[AUTH ERROR] Failed to resend registration email: {e}", flush=True)
        raise HTTPException(status_code=500, detail="Failed to send the OTP email. Please check backend SMTP configuration.")


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not user.hashed_password or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your account first. Check your email (and phone) for the OTP.",
        )

    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserProfile)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user


# ── Forgot Password ───────────────────────────────────────────────────────────

@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(database.get_db)):
    """Generate a 6-digit OTP and email it to the user."""
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        return {"message": "If that email exists, a reset code has been sent."}

    db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.user_id == user.id,
        models.PasswordResetToken.used == False
    ).update({"used": True})
    db.commit()

    otp = _generate_otp()
    reset_token = models.PasswordResetToken(
        user_id=user.id,
        token=otp,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
    )
    db.add(reset_token)
    db.commit()

    try:
        send_reset_otp(to_email=user.email, otp=otp, full_name=user.full_name or "")
        return {"message": "If that email exists, a reset code has been sent."}
    except Exception as e:
        print(f"[AUTH ERROR] Failed to send reset email: {e}", flush=True)
        raise HTTPException(status_code=500, detail="Temporary issue sending password reset email. Please try again later.")


@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(database.get_db)):
    """Validate OTP and update password."""
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset request")

    token_record = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.user_id == user.id,
        models.PasswordResetToken.token == request.otp,
        models.PasswordResetToken.used == False,
        models.PasswordResetToken.expires_at > datetime.utcnow(),
    ).first()

    if not token_record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    token_record.used = True
    user.hashed_password = auth.get_password_hash(request.new_password)
    db.commit()

    return {"message": "Password updated successfully"}


# ── Google OAuth ──────────────────────────────────────────────────────────────

@router.post("/google", response_model=Token)
def google_auth(request: GoogleTokenRequest, db: Session = Depends(database.get_db)):
    """
    Verify a Google ID token sent from the frontend and return a JWT.
    Google users are automatically marked as verified.
    """
    try:
        idinfo = id_token.verify_oauth2_token(
            request.credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")

    google_id = idinfo.get("sub")
    email = idinfo.get("email")
    full_name = idinfo.get("name")

    if not email:
        raise HTTPException(status_code=400, detail="Google account has no email")

    user = db.query(models.User).filter(models.User.google_id == google_id).first()
    if not user:
        user = db.query(models.User).filter(models.User.email == email).first()

    if user:
        if not user.google_id:
            user.google_id = google_id
        # Google users are always verified
        if not user.is_verified:
            user.is_verified = True
        db.commit()
    else:
        user = models.User(
            email=email,
            full_name=full_name,
            google_id=google_id,
            hashed_password=None,
            is_verified=True,  # Google accounts are pre-verified
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
