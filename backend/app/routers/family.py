from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Family, FamilyMember, User
from ..schemas import FamilyBrief, FamilyCreate, FamilyInfo, FamilyJoin, MemberInfo

router = APIRouter(prefix="/api/v1/family", tags=["家庭"])


@router.post("", response_model=FamilyInfo, status_code=201)
def create_family(body: FamilyCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    family = Family(name=body.name, created_by=user.id)
    db.add(family)
    db.flush()

    member = FamilyMember(family_id=family.id, user_id=user.id, role="creator")
    db.add(member)
    db.commit()
    db.refresh(family)

    return _family_to_info(family)


@router.post("/join", response_model=FamilyInfo)
def join_family(body: FamilyJoin, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    family = db.query(Family).filter(Family.invite_code == body.invite_code.upper()).first()
    if not family:
        raise HTTPException(status_code=404, detail="邀请码无效")

    exists = (
        db.query(FamilyMember)
        .filter(FamilyMember.family_id == family.id, FamilyMember.user_id == user.id)
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="你已经是这个家庭的成员了")

    member = FamilyMember(family_id=family.id, user_id=user.id, role="member")
    db.add(member)
    db.commit()
    db.refresh(family)

    return _family_to_info(family)


@router.get("", response_model=list[FamilyBrief])
def list_my_families(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = db.query(FamilyMember).filter(FamilyMember.user_id == user.id).all()
    result = []
    for m in memberships:
        family = db.query(Family).filter(Family.id == m.family_id).first()
        count = db.query(FamilyMember).filter(FamilyMember.family_id == family.id).count()
        result.append(FamilyBrief(id=family.id, name=family.name, role=m.role, member_count=count))
    return result


@router.get("/{family_id}", response_model=FamilyInfo)
def get_family(family_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _assert_member(db, family_id, user.id)
    family = db.query(Family).filter(Family.id == family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="家庭不存在")
    return _family_to_info(family)


@router.delete("/{family_id}/members/{member_user_id}", status_code=204)
def remove_member(
    family_id: str,
    member_user_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    me = _assert_member(db, family_id, user.id)

    if member_user_id == user.id:
        db.delete(me)
        db.commit()
        return

    if me.role != "creator":
        raise HTTPException(status_code=403, detail="只有创建者才能移除其他成员")

    target = (
        db.query(FamilyMember)
        .filter(FamilyMember.family_id == family_id, FamilyMember.user_id == member_user_id)
        .first()
    )
    if not target:
        raise HTTPException(status_code=404, detail="成员不存在")

    db.delete(target)
    db.commit()


def _assert_member(db: Session, family_id: str, user_id: str) -> FamilyMember:
    m = (
        db.query(FamilyMember)
        .filter(FamilyMember.family_id == family_id, FamilyMember.user_id == user_id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=403, detail="你不是这个家庭的成员")
    return m


def _family_to_info(family: Family) -> FamilyInfo:
    return FamilyInfo(
        id=family.id,
        name=family.name,
        invite_code=family.invite_code,
        created_by=family.created_by,
        members=[
            MemberInfo(
                user_id=m.user_id,
                nickname=m.user.nickname,
                avatar_url=m.user.avatar_url,
                role=m.role,
            )
            for m in family.members
        ],
    )
