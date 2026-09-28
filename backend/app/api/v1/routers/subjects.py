from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.db.models import Subject, SubjectMember
from app.schemas.common import MessageResponse, Page
from app.schemas.subjects import SubjectCreate, SubjectOut, SubjectUpdate

router = APIRouter(prefix="/subjects", tags=["subjects"])


def owned_subject(db: DbSession, user_id: int, subject_id: int) -> Subject:
    row = db.scalar(select(Subject).where(Subject.id == subject_id, Subject.owner_id == user_id))
    if row is None:
        raise HTTPException(404, "Subject not found")
    return row


@router.get("", response_model=Page[SubjectOut])
def list_subjects(db: DbSession, user: CurrentUser, limit: int = 50, offset: int = 0):
    accessible = select(Subject.id).outerjoin(SubjectMember, SubjectMember.subject_id == Subject.id).where(
        (Subject.owner_id == user.id) | (SubjectMember.user_id == user.id)
    )
    total = db.scalar(select(func.count()).select_from(accessible.subquery())) or 0
    items = list(db.scalars(select(Subject).where(Subject.id.in_(accessible)).order_by(Subject.updated_at.desc()).limit(limit).offset(offset)).all())
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=SubjectOut, status_code=201)
def create_subject(payload: SubjectCreate, db: DbSession, user: CurrentUser):
    if db.scalar(select(Subject).where(Subject.owner_id == user.id, Subject.name == payload.name)):
        raise HTTPException(409, "A subject with this name already exists")
    row = Subject(owner_id=user.id, **payload.model_dump())
    db.add(row)
    db.flush()
    db.add(SubjectMember(subject_id=row.id, user_id=user.id, member_role="OWNER"))
    db.commit()
    db.refresh(row)
    return row


@router.get("/{subject_id}", response_model=SubjectOut)
def get_subject(subject_id: int, db: DbSession, user: CurrentUser):
    row = db.scalar(select(Subject).outerjoin(SubjectMember, SubjectMember.subject_id == Subject.id).where(
        Subject.id == subject_id,
        (Subject.owner_id == user.id) | (SubjectMember.user_id == user.id),
    ))
    if row is None:
        raise HTTPException(404, "Subject not found")
    return row


@router.patch("/{subject_id}", response_model=SubjectOut)
def update_subject(subject_id: int, payload: SubjectUpdate, db: DbSession, user: CurrentUser):
    row = owned_subject(db, user.id, subject_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit(); db.refresh(row)
    return row


@router.delete("/{subject_id}", response_model=MessageResponse)
def delete_subject(subject_id: int, db: DbSession, user: CurrentUser):
    row = owned_subject(db, user.id, subject_id)
    db.delete(row); db.commit()
    return MessageResponse(message="Subject deleted")
