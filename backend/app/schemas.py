from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class UserRegister(BaseModel):
    username: str
    password: str
    nickname: str


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    id: str
    username: str
    nickname: str
    avatar_url: Optional[str] = None
    api_token: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None


class AdminResetPassword(BaseModel):
    username: str
    new_password: str


class FamilyCreate(BaseModel):
    name: str


class FamilyJoin(BaseModel):
    invite_code: str


class MemberInfo(BaseModel):
    user_id: str
    nickname: str
    avatar_url: Optional[str] = None
    role: str


class FamilyInfo(BaseModel):
    id: str
    name: str
    invite_code: str
    created_by: str
    members: list[MemberInfo] = []


class FamilyBrief(BaseModel):
    id: str
    name: str
    role: str
    member_count: int


class StatusUpdate(BaseModel):
    going_home: bool
    reason: Optional[str] = None


class MemberStatus(BaseModel):
    user_id: str
    nickname: str
    avatar_url: Optional[str] = None
    going_home: bool
    reason: Optional[str] = None
    updated_at: Optional[datetime] = None
    source: Optional[str] = None


class FamilyStatus(BaseModel):
    family_id: str
    family_name: str
    date: date
    reset_at: str
    members: list[MemberStatus]
    summary: str


class MyStatus(BaseModel):
    family_id: str
    family_name: str
    going_home: bool
    reason: Optional[str] = None
    updated_at: Optional[datetime] = None
