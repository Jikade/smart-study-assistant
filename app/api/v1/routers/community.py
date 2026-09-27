from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import delete, func, select, text

from app.api.deps import CurrentUser, DbSession
from app.db.models import (
    CommunityPost,
    CommunityReaction,
    CommunitySave,
    Flashcard,
    FlashcardDeck,
    Question,
    QuestionOption,
    Quiz,
    User,
)
from app.schemas.community import CommunityPostCreate, CommunityPostOut
from app.core.security import decode_access_token

router = APIRouter(prefix="/community", tags=["community"])


@router.get("/posts")
def public_posts(
    db: DbSession,
    limit: int = 50,
    offset: int = 0,
    authorization: str | None = Header(default=None),
):
    rows = db.execute(
        text(
            """
            SELECT *
            FROM vw_public_community_resources
            ORDER BY published_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        {"limit": limit, "offset": offset},
    ).mappings().all()

    posts = [dict(row) for row in rows]

    for post in posts:
        post["liked_by_me"] = False
        post["saved_by_me"] = False

    if not authorization:
        return posts

    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise ValueError("invalid auth scheme")

        payload = decode_access_token(token)
        user_id = int(payload["sub"])

        user = db.get(User, user_id)
        if user is None or user.status != "ACTIVE":
            raise ValueError("inactive user")

    except Exception as exc:
        raise HTTPException(
            401,
            "Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    post_ids = [
        int(post["post_id"])
        for post in posts
    ]

    if not post_ids:
        return posts

    liked_ids = set(
        db.scalars(
            select(CommunityReaction.post_id).where(
                CommunityReaction.user_id == user_id,
                CommunityReaction.post_id.in_(post_ids),
            )
        ).all()
    )

    saved_ids = set(
        db.scalars(
            select(CommunitySave.post_id).where(
                CommunitySave.user_id == user_id,
                CommunitySave.post_id.in_(post_ids),
            )
        ).all()
    )

    for post in posts:
        post_id = int(post["post_id"])
        post["liked_by_me"] = post_id in liked_ids
        post["saved_by_me"] = post_id in saved_ids

    return posts


@router.post("/posts", response_model=CommunityPostOut, status_code=201)
def publish(payload: CommunityPostCreate, db: DbSession, user: CurrentUser):
    if payload.quiz_id is not None:
        quiz = db.get(Quiz, payload.quiz_id)
        if not quiz or quiz.owner_id != user.id:
            raise HTTPException(404, "Quiz not found")
        quiz.visibility = "PUBLIC"; quiz.status = "PUBLISHED"
    else:
        deck = db.get(FlashcardDeck, payload.flashcard_deck_id)
        if not deck or deck.owner_id != user.id:
            raise HTTPException(404, "Flashcard deck not found")
        deck.visibility = "PUBLIC"
    post = CommunityPost(owner_id=user.id, **payload.model_dump(), status="PUBLISHED")
    db.add(post)
    try:
        db.commit()
    except Exception as exc:
        db.rollback(); raise HTTPException(400, str(exc)) from exc
    db.refresh(post)
    return post


@router.post("/posts/{post_id}/like")
def like(post_id: int, db: DbSession, user: CurrentUser):
    if not db.get(CommunityPost, post_id):
        raise HTTPException(404, "Post not found")

    row = db.get(CommunityReaction, (post_id, user.id))

    if row:
        db.delete(row)
        liked = False
    else:
        db.add(
            CommunityReaction(
                post_id=post_id,
                user_id=user.id,
            )
        )
        liked = True

    db.commit()

    like_count = db.scalar(
        select(func.count())
        .select_from(CommunityReaction)
        .where(CommunityReaction.post_id == post_id)
    )

    return {
        "liked": liked,
        "like_count": int(like_count or 0),
    }


@router.post("/posts/{post_id}/save")
def save(post_id: int, db: DbSession, user: CurrentUser):
    if not db.get(CommunityPost, post_id):
        raise HTTPException(404, "Post not found")

    row = db.get(CommunitySave, (post_id, user.id))

    if row:
        db.delete(row)
        saved = False
    else:
        db.add(
            CommunitySave(
                post_id=post_id,
                user_id=user.id,
            )
        )
        saved = True

    db.commit()

    save_count = db.scalar(
        select(func.count())
        .select_from(CommunitySave)
        .where(CommunitySave.post_id == post_id)
    )

    return {
        "saved": saved,
        "save_count": int(save_count or 0),
    }


@router.post("/posts/{post_id}/fork")
def fork(post_id: int, db: DbSession, user: CurrentUser):
    post = db.get(CommunityPost, post_id)
    if not post or post.status != "PUBLISHED":
        raise HTTPException(404, "Post not found")
    if post.quiz_id:
        src = db.get(Quiz, post.quiz_id)
        new = Quiz(owner_id=user.id, subject_id=None, source_quiz_id=src.id, title=f"{src.title} (fork)", description=src.description, generation_mode="FORKED", difficulty=src.difficulty, duration_minutes=src.duration_minutes, status="DRAFT", visibility="PRIVATE")
        db.add(new); db.flush()
        for q in db.scalars(select(Question).where(Question.quiz_id == src.id).order_by(Question.question_order)).all():
            nq = Question(quiz_id=new.id, # A community fork copies the public quiz content, not the source-document ownership link.
                source_chunk_id=None, question_order=q.question_order, question_text=q.question_text, difficulty=q.difficulty, explanation=q.explanation, points=q.points, metadata_={})
            db.add(nq); db.flush()
            for o in db.scalars(select(QuestionOption).where(QuestionOption.question_id == q.id).order_by(QuestionOption.position)).all():
                db.add(QuestionOption(question_id=nq.id, option_key=o.option_key, option_text=o.option_text, is_correct=o.is_correct, explanation=o.explanation, position=o.position))
        db.commit(); return {"resource_type": "QUIZ", "resource_id": new.id}
    src = db.get(FlashcardDeck, post.flashcard_deck_id)
    new = FlashcardDeck(owner_id=user.id, source_deck_id=src.id, title=f"{src.title} (fork)", description=src.description, generation_mode="FORKED", visibility="PRIVATE", status="ACTIVE")
    db.add(new); db.flush()
    for c in db.scalars(select(Flashcard).where(Flashcard.deck_id == src.id).order_by(Flashcard.card_order)).all():
        db.add(Flashcard(deck_id=new.id, # A community fork copies the public card content, not the source-document ownership link.
            source_chunk_id=None, front_text=c.front_text, back_text=c.back_text, hint=c.hint, card_order=c.card_order))
    db.commit(); return {"resource_type": "FLASHCARD_DECK", "resource_id": new.id}
