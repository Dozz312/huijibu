import secrets
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Column, DateTime, Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _invite_code() -> str:
    return secrets.token_hex(3).upper()[:6]


def _api_token() -> str:
    return secrets.token_urlsafe(32)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    nickname = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    api_token = Column(String, unique=True, index=True, default=_api_token)
    created_at = Column(DateTime, default=datetime.utcnow)

    memberships = relationship("FamilyMember", back_populates="user", cascade="all, delete-orphan")
    statuses = relationship("DailyStatus", back_populates="user", cascade="all, delete-orphan")


class Family(Base):
    __tablename__ = "families"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    invite_code = Column(String, unique=True, index=True, default=_invite_code)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("FamilyMember", back_populates="family", cascade="all, delete-orphan")
    statuses = relationship("DailyStatus", back_populates="family", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])


class FamilyMember(Base):
    __tablename__ = "family_members"
    __table_args__ = (
        UniqueConstraint("family_id", "user_id", name="uq_family_user"),
    )

    id = Column(String, primary_key=True, default=_uuid)
    family_id = Column(String, ForeignKey("families.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    role = Column(String, default="member")
    joined_at = Column(DateTime, default=datetime.utcnow)

    family = relationship("Family", back_populates="members")
    user = relationship("User", back_populates="memberships")


class DailyStatus(Base):
    __tablename__ = "daily_statuses"
    __table_args__ = (
        UniqueConstraint("family_id", "user_id", "date", name="uq_family_user_date"),
    )

    id = Column(String, primary_key=True, default=_uuid)
    family_id = Column(String, ForeignKey("families.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    date = Column(Date, default=date.today, nullable=False)
    going_home = Column(Boolean, default=True)
    reason = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String, default="app")

    family = relationship("Family", back_populates="statuses")
    user = relationship("User", back_populates="statuses")
