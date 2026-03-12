from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import DailyStatus, Family, FamilyMember, User
from ..schemas import FamilyStatus, MemberStatus, MyStatus, StatusUpdate

router = APIRouter(prefix="/api/v1/status", tags=["回家状态"])


@router.get("", response_model=list[FamilyStatus])
def get_all_status(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取用户所在所有家庭的今日状态"""
    memberships = db.query(FamilyMember).filter(FamilyMember.user_id == user.id).all()
    return [_build_family_status(db, m.family_id) for m in memberships]


@router.get("/family/{family_id}", response_model=FamilyStatus)
def get_family_status(
    family_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """获取指定家庭的今日状态"""
    _assert_member(db, family_id, user.id)
    return _build_family_status(db, family_id)


@router.get("/me", response_model=list[MyStatus])
def get_my_status(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取自己在所有家庭中的今日状态"""
    memberships = db.query(FamilyMember).filter(FamilyMember.user_id == user.id).all()
    result = []
    for m in memberships:
        family = db.query(Family).filter(Family.id == m.family_id).first()
        status_row = _get_or_default_status(db, m.family_id, user.id)
        result.append(
            MyStatus(
                family_id=family.id,
                family_name=family.name,
                going_home=status_row.going_home if status_row else True,
                reason=status_row.reason if status_row else None,
                updated_at=status_row.updated_at if status_row else None,
            )
        )
    return result


@router.put("/me", response_model=MyStatus)
def update_my_status(
    body: StatusUpdate,
    family_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    更新自己的回家状态。
    如果用户只属于一个家庭，family_id 可省略；否则需指定。
    """
    target_family_id = _resolve_family(db, user.id, family_id)
    today = date.today()

    status_row = (
        db.query(DailyStatus)
        .filter(
            DailyStatus.family_id == target_family_id,
            DailyStatus.user_id == user.id,
            DailyStatus.date == today,
        )
        .first()
    )

    if status_row:
        status_row.going_home = body.going_home
        status_row.reason = body.reason
        status_row.source = "api"
    else:
        status_row = DailyStatus(
            family_id=target_family_id,
            user_id=user.id,
            date=today,
            going_home=body.going_home,
            reason=body.reason,
            source="api",
        )
        db.add(status_row)

    db.commit()
    db.refresh(status_row)

    family = db.query(Family).filter(Family.id == target_family_id).first()
    return MyStatus(
        family_id=family.id,
        family_name=family.name,
        going_home=status_row.going_home,
        reason=status_row.reason,
        updated_at=status_row.updated_at,
    )


def _resolve_family(db: Session, user_id: str, family_id: str | None) -> str:
    memberships = db.query(FamilyMember).filter(FamilyMember.user_id == user_id).all()
    if not memberships:
        raise HTTPException(status_code=400, detail="你还没有加入任何家庭")

    if family_id:
        if not any(m.family_id == family_id for m in memberships):
            raise HTTPException(status_code=403, detail="你不是这个家庭的成员")
        return family_id

    if len(memberships) == 1:
        return memberships[0].family_id

    raise HTTPException(status_code=400, detail="你加入了多个家庭，请通过 family_id 参数指定")


def _assert_member(db: Session, family_id: str, user_id: str):
    m = (
        db.query(FamilyMember)
        .filter(FamilyMember.family_id == family_id, FamilyMember.user_id == user_id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=403, detail="你不是这个家庭的成员")


def _get_or_default_status(db: Session, family_id: str, user_id: str):
    return (
        db.query(DailyStatus)
        .filter(
            DailyStatus.family_id == family_id,
            DailyStatus.user_id == user_id,
            DailyStatus.date == date.today(),
        )
        .first()
    )


def _build_family_status(db: Session, family_id: str) -> FamilyStatus:
    family = db.query(Family).filter(Family.id == family_id).first()
    members = db.query(FamilyMember).filter(FamilyMember.family_id == family_id).all()
    today = date.today()

    member_statuses = []
    not_home_count = 0

    for m in members:
        s = _get_or_default_status(db, family_id, m.user_id)
        going = s.going_home if s else True
        if not going:
            not_home_count += 1
        member_statuses.append(
            MemberStatus(
                user_id=m.user_id,
                nickname=m.user.nickname,
                avatar_url=m.user.avatar_url,
                going_home=going,
                reason=s.reason if s else None,
                updated_at=s.updated_at if s else None,
                source=s.source if s else None,
            )
        )

    home_count = len(members) - not_home_count
    summary = f"今晚 {home_count} 人回家"
    if not_home_count:
        summary += f"，{not_home_count} 人不回家"

    return FamilyStatus(
        family_id=family.id,
        family_name=family.name,
        date=today,
        reset_at="04:00",
        members=member_statuses,
        summary=summary,
    )
