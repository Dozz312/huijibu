from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import create_access_token, get_current_user, hash_password, verify_password
from ..config import settings
from ..database import get_db
from ..models import User, _api_token
from ..schemas import AdminResetPassword, TokenResponse, UserInfo, UserLogin, UserRegister, UserUpdate

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(body: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        nickname=body.nickname,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
def login(body: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserInfo)
def get_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserInfo)
def update_me(body: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.nickname is not None:
        user.nickname = body.nickname
    if body.avatar_url is not None:
        user.avatar_url = body.avatar_url
    db.commit()
    db.refresh(user)
    return user


@router.post("/token/regenerate", response_model=UserInfo)
def regenerate_api_token(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.api_token = _api_token()
    db.commit()
    db.refresh(user)
    return user


@router.post("/admin/reset-password")
def admin_reset_password(
    body: AdminResetPassword,
    x_admin_key: str = Header(alias="X-Admin-Key"),
    db: Session = Depends(get_db),
):
    if x_admin_key != settings.ADMIN_KEY:
        raise HTTPException(status_code=403, detail="管理员密钥错误")

    user = db.query(User).filter(User.username == body.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"message": f"用户 {user.nickname}（@{user.username}）的密码已重置"}
