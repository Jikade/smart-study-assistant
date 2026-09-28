from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.db.models import Badge, UserBadge, UserGamification, XpTransaction
from app.services.gamification_service import ensure_gamification

router = APIRouter(prefix="/gamification", tags=["gamification"])


@router.get("/me")
def my_gamification(db: DbSession, user: CurrentUser):
    gam = ensure_gamification(db, user.id)
    earned = db.execute(
        select(Badge.code, Badge.name, Badge.description, UserBadge.earned_at)
        .join(UserBadge, UserBadge.badge_id == Badge.id)
        .where(UserBadge.user_id == user.id)
        .order_by(UserBadge.earned_at.desc())
    ).mappings().all()
    tx = db.scalars(select(XpTransaction).where(XpTransaction.user_id == user.id).order_by(XpTransaction.created_at.desc()).limit(50)).all()
    db.commit()
    return {
        "xp_total": int(gam.xp_total),
        "level_no": gam.level_no,
        "current_streak": gam.current_streak,
        "longest_streak": gam.longest_streak,
        "last_study_date": gam.last_study_date,
        "badges": [dict(r) for r in earned],
        "recent_xp": [
            {"amount": t.amount, "source_type": t.source_type, "source_id": t.source_id, "description": t.description, "created_at": t.created_at}
            for t in tx
        ],
    }
