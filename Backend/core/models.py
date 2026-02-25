from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, LargeBinary
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255), nullable=True)  # nullable for Google OAuth users
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Extended profile fields
    full_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    gender = Column(String(50), nullable=True)
    occupation = Column(String(255), nullable=True)

    # Email / phone verification
    is_verified = Column(Boolean, default=False)

    # Google OAuth
    google_id = Column(String(255), nullable=True, unique=True, index=True)

    sessions = relationship("Session", back_populates="user")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String(10), index=True)      # 6-digit OTP
    expires_at = Column(DateTime)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class RegistrationOTP(Base):
    """OTP sent after registration to verify email + phone."""
    __tablename__ = "registration_otps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String(10), index=True)   # 6-digit OTP
    expires_at = Column(DateTime)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    dataset_id = Column(String(255), unique=True, index=True)
    filename = Column(String(255))
    # file_path kept for backwards compat; new rows use "db:<dataset_id>"
    file_path = Column(String(500), nullable=True)
    # Raw CSV bytes stored in DB — LONGBLOB (MySQL) / BLOB (SQLite)
    file_content = Column(LargeBinary, nullable=True)
    title = Column(String(255), default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Store analytics and validation results as JSON
    validation_report = Column(Text, nullable=True)  # JSON string
    analytics_result = Column(Text, nullable=True)   # JSON string

    user = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    role = Column(String(50))  # "user" or "assistant"
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="messages")
