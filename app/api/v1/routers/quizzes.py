from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.db.models import Question, QuestionOption, Quiz, QuizAttempt
from app.schemas.quizzes import AttemptOut, AttemptSubmit, QuizCreate, QuizGenerateRequest, QuizOut
from app.services.quiz_service import create_quiz, generate_quiz, publish_quiz, start_attempt, submit_attempt

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


def get_visible_quiz(db: DbSession, user_id: int, quiz_id: int) -> Quiz:
    row = db.get(Quiz, quiz_id)
    if row is None:
        raise HTTPException(404, "Quiz not found")
    if row.owner_id != user_id and not (row.status == "PUBLISHED" and row.visibility in {"PUBLIC", "UNLISTED"}):
        raise HTTPException(404, "Quiz not found")
    return row


@router.get("", response_model=list[QuizOut])
def list_quizzes(db: DbSession, user: CurrentUser, subject_id: int | None = None, limit: int = 50):
    stmt = select(Quiz).where(Quiz.owner_id == user.id)
    if subject_id is not None:
        stmt = stmt.where(Quiz.subject_id == subject_id)
    return list(db.scalars(stmt.order_by(Quiz.created_at.desc()).limit(limit)).all())


@router.post("", response_model=QuizOut, status_code=201)
def create(payload: QuizCreate, db: DbSession, user: CurrentUser):
    return create_quiz(db, user.id, payload)


@router.post("/generate", response_model=QuizOut, status_code=201)
def generate(payload: QuizGenerateRequest, db: DbSession, user: CurrentUser):
    return generate_quiz(db, user.id, payload)


@router.get("/{quiz_id}")
def get_quiz(quiz_id: int, db: DbSession, user: CurrentUser):
    quiz = get_visible_quiz(db, user.id, quiz_id)
    questions = list(db.scalars(select(Question).where(Question.quiz_id == quiz.id).order_by(Question.question_order)).all())
    data = QuizOut.model_validate(quiz).model_dump()
    data["questions"] = []
    for q in questions:
        opts = list(db.scalars(select(QuestionOption).where(QuestionOption.question_id == q.id).order_by(QuestionOption.position)).all())
        qd = {
            "id": q.id, "question_order": q.question_order, "question_text": q.question_text,
            "difficulty": q.difficulty, "points": float(q.points),
            "explanation": q.explanation if quiz.owner_id == user.id else None,
            "source_chunk_id": q.source_chunk_id if quiz.owner_id == user.id else None,
            "options": [
                {
                    "id": o.id, "option_key": o.option_key, "option_text": o.option_text, "position": o.position,
                    **({"is_correct": o.is_correct, "explanation": o.explanation} if quiz.owner_id == user.id else {}),
                }
                for o in opts
            ],
        }
        data["questions"].append(qd)
    return data


@router.post("/{quiz_id}/publish", response_model=QuizOut)
def publish(quiz_id: int, db: DbSession, user: CurrentUser):
    quiz = db.scalar(select(Quiz).where(Quiz.id == quiz_id, Quiz.owner_id == user.id))
    if quiz is None:
        raise HTTPException(404, "Quiz not found")
    return publish_quiz(db, quiz)


@router.post("/{quiz_id}/attempts", status_code=201)
def begin_attempt(quiz_id: int, db: DbSession, user: CurrentUser):
    quiz = get_visible_quiz(db, user.id, quiz_id)
    attempt = start_attempt(db, user.id, quiz)
    questions = list(db.scalars(select(Question).where(Question.quiz_id == quiz.id).order_by(Question.question_order)).all())
    return {
        "attempt_id": attempt.id,
        "quiz_id": quiz.id,
        "started_at": attempt.started_at,
        "duration_minutes": quiz.duration_minutes,
        "questions": [
            {
                "id": q.id,
                "question_order": q.question_order,
                "question_text": q.question_text,
                "difficulty": q.difficulty,
                "points": float(q.points),
                "options": [
                    {"id": o.id, "option_key": o.option_key, "option_text": o.option_text, "position": o.position}
                    for o in db.scalars(select(QuestionOption).where(QuestionOption.question_id == q.id).order_by(QuestionOption.position)).all()
                ],
            }
            for q in questions
        ],
    }


@router.post("/attempts/{attempt_id}/submit", response_model=AttemptOut)
def finalize_attempt(attempt_id: int, payload: AttemptSubmit, db: DbSession, user: CurrentUser):
    attempt = db.scalar(select(QuizAttempt).where(QuizAttempt.id == attempt_id, QuizAttempt.user_id == user.id))
    if attempt is None:
        raise HTTPException(404, "Attempt not found")
    return submit_attempt(db, attempt, [a.model_dump() for a in payload.answers])


@router.get("/attempts/{attempt_id}/result")
def attempt_result(attempt_id: int, db: DbSession, user: CurrentUser):
    attempt = db.scalar(select(QuizAttempt).where(QuizAttempt.id == attempt_id, QuizAttempt.user_id == user.id))
    if attempt is None:
        raise HTTPException(404, "Attempt not found")
    if attempt.status != "SUBMITTED":
        raise HTTPException(409, "Attempt has not been submitted")
    return AttemptOut.model_validate(attempt)
