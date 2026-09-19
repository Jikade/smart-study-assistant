from __future__ import annotations

from fastapi import (
    APIRouter,
    HTTPException,
)
from sqlalchemy import select

from app.api.deps import (
    CurrentUser,
    DbSession,
)
from app.db.models import (
    Question,
    QuestionOption,
    Quiz,
    QuizAttempt,
)
from app.schemas.quizzes import (
    AttemptOut,
    AttemptSubmit,
    QuizCreate,
    QuizGenerateRequest,
    QuizOut,
)
from app.services.quiz_service import (
    create_quiz,
    generate_quiz,
    generate_weak_topic_quiz,
    generate_adaptive_quiz,
    generate_due_quiz,
    publish_quiz,
    start_attempt,
    submit_attempt,
)

router = APIRouter(
    prefix="/quizzes",
    tags=["quizzes"],
)


# =========================================================
# HELPERS
# =========================================================


def get_visible_quiz(
    db: DbSession,
    user_id: int,
    quiz_id: int,
) -> Quiz:

    row = db.get(
        Quiz,
        quiz_id,
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Quiz not found",
        )

    if row.owner_id != user_id and not (
        row.status == "PUBLISHED"
        and row.visibility
        in {
            "PUBLIC",
            "UNLISTED",
        }
    ):
        raise HTTPException(
            status_code=404,
            detail="Quiz not found",
        )

    return row


# =========================================================
# LIST QUIZZES
# =========================================================


@router.get(
    "",
    response_model=list[QuizOut],
)
def list_quizzes(
    db: DbSession,
    user: CurrentUser,
    subject_id: int | None = None,
    limit: int = 50,
):
    stmt = select(Quiz).where(Quiz.owner_id == user.id)

    if subject_id is not None:
        stmt = stmt.where(Quiz.subject_id == subject_id)

    return list(db.scalars(stmt.order_by(Quiz.created_at.desc()).limit(limit)).all())


# =========================================================
# CREATE MANUAL QUIZ
# =========================================================


@router.post(
    "",
    response_model=QuizOut,
    status_code=201,
)
def create(
    payload: QuizCreate,
    db: DbSession,
    user: CurrentUser,
):
    return create_quiz(
        db,
        user.id,
        payload,
    )


# =========================================================
# GENERATE NORMAL AI QUIZ
# =========================================================


@router.post(
    "/generate",
    response_model=QuizOut,
    status_code=201,
)
def generate(
    payload: QuizGenerateRequest,
    db: DbSession,
    user: CurrentUser,
):
    return generate_quiz(
        db,
        user.id,
        payload,
    )


# =========================================================
# GENERATE AI QUIZ FROM WEAK TOPICS
# =========================================================
#
# IMPORTANT:
# Keep this route BEFORE /{quiz_id}
#
# Otherwise FastAPI may try to interpret
# "generate-weak-topic" as quiz_id.
# =========================================================


@router.post(
    "/generate-weak-topic",
    response_model=QuizOut,
    status_code=201,
)
def generate_from_weak_topics(
    payload: QuizGenerateRequest,
    db: DbSession,
    user: CurrentUser,
):
    return generate_weak_topic_quiz(
        db=db,
        owner_id=user.id,
        payload=payload,
    )


@router.post(
    "/generate-adaptive",
    response_model=QuizOut,
    status_code=201,
)
def generate_adaptive(
    payload: QuizGenerateRequest,
    db: DbSession,
    user: CurrentUser,
):
    return generate_adaptive_quiz(
        db=db,
        owner_id=user.id,
        payload=payload,
    )


@router.post(
    "/generate-due",
    response_model=QuizOut,
    status_code=201,
)
def generate_due(
    payload: QuizGenerateRequest,
    db: DbSession,
    user: CurrentUser,
):
    return generate_due_quiz(
        db=db,
        owner_id=user.id,
        payload=payload,
    )


# =========================================================
# GET QUIZ
# =========================================================


@router.get("/{quiz_id}")
def get_quiz(
    quiz_id: int,
    db: DbSession,
    user: CurrentUser,
):
    quiz = get_visible_quiz(
        db,
        user.id,
        quiz_id,
    )

    questions = list(
        db.scalars(
            select(Question)
            .where(Question.quiz_id == quiz.id)
            .order_by(Question.question_order)
        ).all()
    )

    data = QuizOut.model_validate(quiz).model_dump()

    data["questions"] = []

    for question in questions:

        options = list(
            db.scalars(
                select(QuestionOption)
                .where(QuestionOption.question_id == question.id)
                .order_by(QuestionOption.position)
            ).all()
        )

        question_data = {
            "id": question.id,
            "question_order": question.question_order,
            "question_text": question.question_text,
            "difficulty": question.difficulty,
            "points": float(question.points),
            "explanation": (
                question.explanation if (quiz.owner_id == user.id) else None
            ),
            "source_chunk_id": (
                question.source_chunk_id if (quiz.owner_id == user.id) else None
            ),
            "options": [
                {
                    "id": option.id,
                    "option_key": option.option_key,
                    "option_text": option.option_text,
                    "position": option.position,
                    **(
                        {
                            "is_correct": option.is_correct,
                            "explanation": option.explanation,
                        }
                        if (quiz.owner_id == user.id)
                        else {}
                    ),
                }
                for option in options
            ],
        }

        data["questions"].append(question_data)

    return data


# =========================================================
# PUBLISH QUIZ
# =========================================================


@router.post(
    "/{quiz_id}/publish",
    response_model=QuizOut,
)
def publish(
    quiz_id: int,
    db: DbSession,
    user: CurrentUser,
):
    quiz = db.scalar(
        select(Quiz).where(
            Quiz.id == quiz_id,
            Quiz.owner_id == user.id,
        )
    )

    if quiz is None:
        raise HTTPException(
            status_code=404,
            detail="Quiz not found",
        )

    return publish_quiz(
        db,
        quiz,
    )


# =========================================================
# START ATTEMPT
# =========================================================


@router.post(
    "/{quiz_id}/attempts",
    status_code=201,
)
def begin_attempt(
    quiz_id: int,
    db: DbSession,
    user: CurrentUser,
):
    quiz = get_visible_quiz(
        db,
        user.id,
        quiz_id,
    )

    attempt = start_attempt(
        db,
        user.id,
        quiz,
    )

    questions = list(
        db.scalars(
            select(Question)
            .where(Question.quiz_id == quiz.id)
            .order_by(Question.question_order)
        ).all()
    )

    return {
        "attempt_id": attempt.id,
        "quiz_id": quiz.id,
        "started_at": attempt.started_at,
        "duration_minutes": quiz.duration_minutes,
        "questions": [
            {
                "id": question.id,
                "question_order": question.question_order,
                "question_text": question.question_text,
                "difficulty": question.difficulty,
                "points": float(question.points),
                "options": [
                    {
                        "id": option.id,
                        "option_key": option.option_key,
                        "option_text": option.option_text,
                        "position": option.position,
                    }
                    for option in db.scalars(
                        select(QuestionOption)
                        .where(QuestionOption.question_id == question.id)
                        .order_by(QuestionOption.position)
                    ).all()
                ],
            }
            for question in questions
        ],
    }


# =========================================================
# SUBMIT ATTEMPT
# =========================================================


@router.post(
    "/attempts/{attempt_id}/submit",
    response_model=AttemptOut,
)
def finalize_attempt(
    attempt_id: int,
    payload: AttemptSubmit,
    db: DbSession,
    user: CurrentUser,
):
    attempt = db.scalar(
        select(QuizAttempt).where(
            QuizAttempt.id == attempt_id,
            QuizAttempt.user_id == user.id,
        )
    )

    if attempt is None:
        raise HTTPException(
            status_code=404,
            detail=("Attempt not found"),
        )

    return submit_attempt(
        db,
        attempt,
        [answer.model_dump() for answer in payload.answers],
    )


# =========================================================
# ATTEMPT RESULT
# =========================================================


@router.get("/attempts/{attempt_id}/result")
def attempt_result(
    attempt_id: int,
    db: DbSession,
    user: CurrentUser,
):
    attempt = db.scalar(
        select(QuizAttempt).where(
            QuizAttempt.id == attempt_id,
            QuizAttempt.user_id == user.id,
        )
    )

    if attempt is None:
        raise HTTPException(
            status_code=404,
            detail=("Attempt not found"),
        )

    if attempt.status != "SUBMITTED":
        raise HTTPException(
            status_code=409,
            detail=("Attempt has not " "been submitted"),
        )

    return AttemptOut.model_validate(attempt)
