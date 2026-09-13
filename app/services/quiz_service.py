from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    DailyLearningStat,
    Document,
    DocumentChunk,
    Question,
    QuestionOption,
    Quiz,
    QuizAttempt,
    QuizDocument,
    TopicMastery,
    UserAnswer,
    UserSubjectProgress,
)
from app.schemas.quizzes import (
    QuestionCreate,
    QuizCreate,
    QuizGenerateRequest,
)
from app.services.ai_provider import (
    AIProviderError,
    get_ai_provider,
)
from app.services.gamification_service import (
    add_xp,
    evaluate_badges,
)


OPTION_KEYS = ("A", "B", "C", "D")


# =========================================================
# QUIZ CREATION
# =========================================================


def create_quiz(
    db: Session,
    owner_id: int,
    payload: QuizCreate,
    *,
    generation_mode: str = "MANUAL",
    ai_model: str | None = None,
    generation_prompt: str | None = None,
) -> Quiz:
    quiz = Quiz(
        owner_id=owner_id,
        subject_id=payload.subject_id,
        title=payload.title,
        description=payload.description,
        generation_mode=generation_mode,
        difficulty=payload.difficulty,
        duration_minutes=payload.duration_minutes,
        question_count=len(payload.questions),
        status="DRAFT",
        visibility=payload.visibility,
        ai_model_name=ai_model,
        generation_prompt=generation_prompt,
    )

    db.add(quiz)
    db.flush()

    for document_id in payload.document_ids:
        db.add(
            QuizDocument(
                quiz_id=quiz.id,
                document_id=document_id,
            )
        )

    for order, q in enumerate(
        payload.questions,
        start=1,
    ):
        question = Question(
            quiz_id=quiz.id,
            source_chunk_id=q.source_chunk_id,
            question_order=order,
            question_text=q.question_text,
            difficulty=q.difficulty,
            explanation=q.explanation,
            points=q.points,
            metadata_={},
        )

        db.add(question)
        db.flush()

        for option in q.options:
            db.add(
                QuestionOption(
                    question_id=question.id,
                    option_key=option.option_key,
                    option_text=option.option_text,
                    is_correct=option.is_correct,
                    explanation=option.explanation,
                    position=option.position,
                )
            )

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(quiz)

    return quiz


# =========================================================
# JSON PARSING
# =========================================================


def _parse_json_object(
    text_value: str,
) -> dict:
    value = text_value.strip()

    # Remove possible Markdown fences.
    value = re.sub(
        r"^```(?:json)?\s*",
        "",
        value,
        flags=re.I,
    )

    value = re.sub(
        r"\s*```$",
        "",
        value,
    )

    # Extract JSON object if model added extra text.
    start = value.find("{")
    end = value.rfind("}")

    if start >= 0 and end > start:
        value = value[start : end + 1]

    parsed = json.loads(value)

    if not isinstance(parsed, dict):
        raise ValueError(
            "AI quiz response must be a JSON object"
        )

    return parsed


# =========================================================
# AI OUTPUT NORMALIZATION
# =========================================================


def _normalize_bool(
    value: Any,
) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value == 1

    if isinstance(value, str):
        return (
            value.strip().lower()
            in {
                "true",
                "1",
                "yes",
                "correct",
            }
        )

    return bool(value)


def _normalize_question(
    raw: dict,
) -> dict:
    """
    Normalize common LLM mistakes before
    Pydantic validation.
    """

    if not isinstance(raw, dict):
        raise ValueError(
            "Every question must be a JSON object"
        )

    question = dict(raw)

    # -----------------------------------------------------
    # question_text
    # -----------------------------------------------------

    if not question.get("question_text"):
        fallback_text = (
            question.get("question")
            or question.get("text")
        )

        if fallback_text:
            question["question_text"] = fallback_text

    # -----------------------------------------------------
    # difficulty
    # -----------------------------------------------------

    if question.get("difficulty"):
        question["difficulty"] = (
            str(question["difficulty"])
            .strip()
            .upper()
        )

    # -----------------------------------------------------
    # options
    # -----------------------------------------------------

    options = question.get("options")

    if not isinstance(options, list):
        raise ValueError(
            "Question options must be a list"
        )

    if len(options) != 4:
        raise ValueError(
            "Question must contain exactly 4 options"
        )

    # Some models put the correct answer
    # at question level.
    correct_hint = (
        question.get("correct_answer")
        or question.get("correct_option")
        or question.get("answer")
    )

    if correct_hint is not None:
        correct_hint = (
            str(correct_hint)
            .strip()
            .upper()
        )

    normalized_options: list[dict] = []

    for index, raw_option in enumerate(options):
        if not isinstance(raw_option, dict):
            raise ValueError(
                "Every option must be a JSON object"
            )

        option = dict(raw_option)

        expected_key = OPTION_KEYS[index]

        # -------------------------------------------------
        # option_key
        # -------------------------------------------------

        option_key = (
            option.get("option_key")
            or option.get("key")
            or option.get("label")
        )

        raw_position = option.get("position")

        # Common Qwen mistake:
        # position = "A"
        if (
            option_key is None
            and isinstance(raw_position, str)
            and raw_position.strip().upper()
            in OPTION_KEYS
        ):
            option_key = (
                raw_position.strip().upper()
            )

        if option_key is None:
            option_key = expected_key

        option_key = (
            str(option_key)
            .strip()
            .upper()
        )

        if option_key not in OPTION_KEYS:
            raise ValueError(
                f"Invalid option_key: {option_key}"
            )

        # -------------------------------------------------
        # position
        # -------------------------------------------------

        position = raw_position

        if isinstance(position, str):
            stripped = position.strip()

            if stripped.isdigit():
                position = int(stripped)
            else:
                position = index + 1

        if not isinstance(position, int):
            position = index + 1

        if not 1 <= position <= 4:
            position = index + 1

        # -------------------------------------------------
        # option_text
        # -------------------------------------------------

        option_text = (
            option.get("option_text")
            or option.get("text")
            or option.get("content")
            or ""
        )

        option_text = str(option_text).strip()

        # -------------------------------------------------
        # is_correct
        # -------------------------------------------------

        if "is_correct" in option:
            is_correct = _normalize_bool(
                option["is_correct"]
            )

        elif "correct" in option:
            is_correct = _normalize_bool(
                option["correct"]
            )

        elif correct_hint is not None:
            is_correct = (
                option_key == correct_hint
            )

        else:
            is_correct = False

        normalized_options.append(
            {
                "option_key": option_key,
                "option_text": option_text,
                "is_correct": is_correct,
                "explanation": option.get(
                    "explanation"
                ),
                "position": position,
            }
        )

    # Always normalize key/position by array order.
    for index, option in enumerate(
        normalized_options
    ):
        option["option_key"] = (
            OPTION_KEYS[index]
        )
        option["position"] = index + 1

    question["options"] = normalized_options

    return question


# =========================================================
# LOCAL QUALITY VALIDATION
# =========================================================


def _normalize_compare_text(
    value: str,
) -> str:
    """
    Normalize text for duplicate comparison.
    """

    value = value.strip().lower()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    value = re.sub(
        r"[.!?;,:\-]+$",
        "",
        value,
    )

    return value


def _validate_question_quality(
    question: QuestionCreate,
) -> None:
    """
    Local validation that does not require another
    LLM call.

    Semantic ambiguity is mainly prevented through
    the strict generation prompt below.
    """

    question_text = (
        question.question_text or ""
    ).strip()

    if len(question_text) < 8:
        raise ValueError(
            "Question text is too short"
        )

    if len(question.options) != 4:
        raise ValueError(
            "Question must contain exactly 4 options"
        )

    correct_options = [
        option
        for option in question.options
        if option.is_correct
    ]

    if len(correct_options) != 1:
        raise ValueError(
            "Question must contain exactly "
            "one correct option"
        )

    option_texts = [
        _normalize_compare_text(
            option.option_text
        )
        for option in question.options
    ]

    if any(
        not text
        for text in option_texts
    ):
        raise ValueError(
            "Option text cannot be empty"
        )

    if len(set(option_texts)) != 4:
        raise ValueError(
            "Question contains duplicate options"
        )

    correct_text = (
        correct_options[0].option_text
        .strip()
    )

    if not correct_text:
        raise ValueError(
            "Correct option text cannot be empty"
        )


# =========================================================
# SOURCE CHUNK SELECTION
# =========================================================


def _looks_like_toc(
    content: str,
) -> bool:
    """
    Detect chunks that are mainly table-of-contents
    material.

    Only inspect the beginning instead of rejecting
    every chunk that happens to mention "MỤC LỤC"
    somewhere later.
    """

    normalized = (
        content.strip().upper()
    )

    beginning = normalized[:700]

    toc_markers = (
        "MỤC LỤC",
        "TABLE OF CONTENTS",
    )

    has_toc_marker = any(
        marker in beginning
        for marker in toc_markers
    )

    if not has_toc_marker:
        return False

    # A long chunk may contain TOC followed by useful
    # content. We only reject it if it looks strongly
    # like navigation/index material.
    chapter_count = beginning.count(
        "CHƯƠNG"
    )

    return chapter_count >= 3


def _get_quiz_candidate_chunks(
    chunks: list[DocumentChunk],
) -> list[DocumentChunk]:
    """
    Remove tiny or TOC-heavy chunks.
    """

    candidates = [
        chunk
        for chunk in chunks
        if (
            len(
                (chunk.content or "").strip()
            )
            >= 500
            and not _looks_like_toc(
                chunk.content or ""
            )
        )
    ]

    if not candidates:
        candidates = [
            chunk
            for chunk in chunks
            if len(
                (chunk.content or "").strip()
            )
            >= 200
        ]

    if not candidates:
        candidates = chunks

    return candidates


def _select_source_chunks(
    chunks: list[DocumentChunk],
    question_count: int,
    max_sources: int = 6,
) -> list[DocumentChunk]:
    """
    Select chunks distributed across the document
    instead of always choosing the first chunks.
    """

    if not chunks:
        return []

    source_count = min(
        len(chunks),
        question_count,
        max_sources,
    )

    if source_count <= 1:
        return [chunks[0]]

    last_index = len(chunks) - 1

    indexes = [
        round(
            index
            * last_index
            / (source_count - 1)
        )
        for index in range(source_count)
    ]

    selected: list[DocumentChunk] = []
    seen_ids: set[int] = set()

    for index in indexes:
        chunk = chunks[index]

        if chunk.id not in seen_ids:
            selected.append(chunk)
            seen_ids.add(chunk.id)

    if len(selected) < source_count:
        for chunk in chunks:
            if chunk.id in seen_ids:
                continue

            selected.append(chunk)
            seen_ids.add(chunk.id)

            if len(selected) >= source_count:
                break

    return selected


def _allocate_question_counts(
    chunks: list[DocumentChunk],
    question_count: int,
) -> list[tuple[DocumentChunk, int]]:
    """
    Example:

    3 questions / 3 chunks
        -> 1, 1, 1

    10 questions / 4 chunks
        -> 3, 3, 2, 2
    """

    if not chunks:
        return []

    base = (
        question_count
        // len(chunks)
    )

    remainder = (
        question_count
        % len(chunks)
    )

    allocation: list[
        tuple[DocumentChunk, int]
    ] = []

    for index, chunk in enumerate(
        chunks
    ):
        count = base

        if index < remainder:
            count += 1

        if count > 0:
            allocation.append(
                (
                    chunk,
                    count,
                )
            )

    return allocation


# =========================================================
# AI QUIZ GENERATION
# =========================================================


def generate_quiz(
    db: Session,
    owner_id: int,
    payload: QuizGenerateRequest,
) -> Quiz:
    provider = get_ai_provider()

    if not provider.can_chat:
        raise HTTPException(
            status_code=503,
            detail=(
                "AI chat model is not configured. "
                "Configure AI_PROVIDER first."
            ),
        )

    # =====================================================
    # 1. AUTHORIZATION
    # =====================================================

    requested_document_ids = list(
        payload.document_ids or []
    )

    if requested_document_ids:
        owned_document_ids = set(
            db.scalars(
                select(Document.id)
                .where(
                    Document.id.in_(
                        requested_document_ids
                    ),
                    Document.owner_id
                    == owner_id,
                )
            ).all()
        )

        requested_set = set(
            requested_document_ids
        )

        if (
            owned_document_ids
            != requested_set
        ):
            raise HTTPException(
                status_code=403,
                detail=(
                    "One or more documents "
                    "are not accessible."
                ),
            )

    # =====================================================
    # 2. LOAD READY CHUNKS
    # =====================================================

    stmt = (
        select(DocumentChunk)
        .join(
            Document,
            Document.id
            == DocumentChunk.document_id,
        )
        .where(
            Document.status == "READY",
            Document.owner_id == owner_id,
        )
    )

    if requested_document_ids:
        stmt = stmt.where(
            DocumentChunk.document_id.in_(
                requested_document_ids
            )
        )

    elif payload.subject_id:
        stmt = stmt.where(
            Document.subject_id
            == payload.subject_id
        )

    all_chunks = list(
        db.scalars(
            stmt
            .order_by(
                DocumentChunk.document_id,
                DocumentChunk.chunk_index,
            )
            .limit(120)
        ).all()
    )

    if not all_chunks:
        raise HTTPException(
            status_code=400,
            detail=(
                "No READY document chunks "
                "found for quiz generation."
            ),
        )

    # =====================================================
    # 3. FILTER CANDIDATES
    # =====================================================

    candidate_chunks = (
        _get_quiz_candidate_chunks(
            all_chunks
        )
    )

    if not candidate_chunks:
        raise HTTPException(
            status_code=400,
            detail=(
                "No suitable document chunks "
                "found for quiz generation."
            ),
        )

    # =====================================================
    # 4. BACKEND SELECTS SOURCE CHUNKS
    # =====================================================

    selected_chunks = (
        _select_source_chunks(
            candidate_chunks,
            payload.question_count,
            max_sources=6,
        )
    )

    if not selected_chunks:
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not select source "
                "chunks for quiz generation."
            ),
        )

    # =====================================================
    # 5. ALLOCATE QUESTIONS
    # =====================================================

    allocation = (
        _allocate_question_counts(
            selected_chunks,
            payload.question_count,
        )
    )

    if not allocation:
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not allocate quiz "
                "questions to source chunks."
            ),
        )

    generated_questions: list[
        QuestionCreate
    ] = []

    used_question_texts: set[
        str
    ] = set()

    ai_model_name: str | None = None

    generation_sources: list[int] = []

    # =====================================================
    # 6. GENERATE CHUNK BY CHUNK
    # =====================================================

    for (
        source_chunk,
        questions_for_chunk,
    ) in allocation:
        generation_sources.append(
            source_chunk.id
        )

        # AI sees ONLY this chunk.
        context = (
            "[SOURCE]\n"
            f"{source_chunk.content[:1600]}"
        )

        # =================================================
        # STRICT PROMPT
        # =================================================

        prompt = f"""
Create exactly {questions_for_chunk}
multiple-choice question(s) using ONLY
the SOURCE below.

Requested difficulty:
{payload.difficulty}

Use the SAME LANGUAGE as the SOURCE.

IMPORTANT:
The backend controls the source ID.

DO NOT generate:
- source_chunk_id
- document_id
- chunk_id

Return ONLY one valid JSON object.
Do not return Markdown.
Do not return ```json.
Do not include any text before or after JSON.

Required JSON structure:

{{
  "questions": [
    {{
      "question_text": "Question text",
      "difficulty": "{payload.difficulty}",
      "explanation": "Explain why the correct answer is correct",
      "options": [
        {{
          "option_key": "A",
          "option_text": "Option A",
          "is_correct": true,
          "explanation": "Why A is correct",
          "position": 1
        }},
        {{
          "option_key": "B",
          "option_text": "Option B",
          "is_correct": false,
          "explanation": null,
          "position": 2
        }},
        {{
          "option_key": "C",
          "option_text": "Option C",
          "is_correct": false,
          "explanation": null,
          "position": 3
        }},
        {{
          "option_key": "D",
          "option_text": "Option D",
          "is_correct": false,
          "explanation": null,
          "position": 4
        }}
      ]
    }}
  ]
}}

STRICT CONTENT RULES:

1. Generate exactly {questions_for_chunk}
   question(s).

2. Use ONLY information explicitly stated
   in SOURCE.

3. Do NOT use outside knowledge.

4. Do NOT generate source_chunk_id,
   document_id, or chunk_id.

5. Each question MUST contain exactly
   four options.

6. option_key MUST be exactly:
   A, B, C, D.

7. position MUST be integer:
   1, 2, 3, 4.

8. Exactly ONE option must be fully correct
   for the specific question.

9. The other THREE options must be clearly
   incorrect for that specific question.

10. NEVER use another true statement from
    SOURCE as an incorrect option.

11. A statement can be true in general but
    MUST NOT be used as a distractor if it
    also answers the question correctly.

12. Before returning JSON, silently check
    ALL FOUR options against SOURCE.

13. If TWO or more options could reasonably
    be considered correct, REWRITE the
    question or REWRITE the distractors.

14. The correct option must be directly and
    explicitly supported by SOURCE.

15. Distractors must not simply be other
    correct facts copied from SOURCE.

16. Distractors should be plausible but must
    fail to satisfy the exact condition asked
    by the question.

17. Avoid vague wording such as:
    "which of the following is one aspect"
    when multiple source statements could
    satisfy the wording.

18. Prefer precise question wording that
    allows exactly ONE answer.

19. Avoid duplicate questions.

20. Do not make all questions use the same
    correct option position.

21. The JSON example above demonstrates
    STRUCTURE ONLY. It does NOT mean option A
    must be the correct answer.

SOURCE:

{context}
""".strip()

        # =================================================
        # OUTPUT TOKEN LIMIT
        # =================================================

        max_output_tokens = min(
            2400,
            max(
                900,
                questions_for_chunk * 500,
            ),
        )

        # =================================================
        # 7. CALL AI
        # =================================================

        try:
            result = provider.chat(
                [
                    {
                        "role": "system",
                        "content": (
                            "You generate grounded "
                            "multiple-choice questions "
                            "as strict JSON. "
                            "Use only the supplied "
                            "source text. "
                            "Every question must have "
                            "exactly one semantically "
                            "correct answer."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                json_mode=True,
                temperature=0.0,
                max_tokens=max_output_tokens,
                reasoning_effort="none",
            )

            ai_model_name = (
                result.model
                or ai_model_name
            )

            data = _parse_json_object(
                result.content
            )

        except AIProviderError as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "AI quiz generation failed "
                    "for source chunk "
                    f"{source_chunk.id}: "
                    f"{exc}"
                ),
            ) from exc

        except (
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "AI returned invalid JSON "
                    "for source chunk "
                    f"{source_chunk.id}: "
                    f"{exc}"
                ),
            ) from exc

        # =================================================
        # 8. QUESTION COUNT CHECK
        # =================================================

        raw_questions = data.get(
            "questions"
        )

        if not isinstance(
            raw_questions,
            list,
        ):
            raise HTTPException(
                status_code=502,
                detail=(
                    "AI response field "
                    "'questions' must be a list "
                    "for source chunk "
                    f"{source_chunk.id}."
                ),
            )

        if (
            len(raw_questions)
            != questions_for_chunk
        ):
            raise HTTPException(
                status_code=502,
                detail=(
                    "AI must return exactly "
                    f"{questions_for_chunk} "
                    "question(s) for source chunk "
                    f"{source_chunk.id}, "
                    "but returned "
                    f"{len(raw_questions)}."
                ),
            )

        # =================================================
        # 9. NORMALIZE + VALIDATE
        # =================================================

        for raw_question in raw_questions:
            try:
                normalized = (
                    _normalize_question(
                        raw_question
                    )
                )

                # -----------------------------------------
                # CRITICAL:
                # Backend owns source_chunk_id.
                # AI does NOT control this value.
                # -----------------------------------------

                normalized[
                    "source_chunk_id"
                ] = source_chunk.id

                # Backend also controls difficulty.
                normalized[
                    "difficulty"
                ] = payload.difficulty

                question = (
                    QuestionCreate
                    .model_validate(
                        normalized
                    )
                )

                _validate_question_quality(
                    question
                )

            except Exception as exc:
                raise HTTPException(
                    status_code=502,
                    detail=(
                        "Quiz JSON validation "
                        "failed for source chunk "
                        f"{source_chunk.id}: "
                        f"{exc}"
                    ),
                ) from exc

            # =============================================
            # 10. DUPLICATE QUESTION PROTECTION
            # =============================================

            normalized_text = (
                _normalize_compare_text(
                    question.question_text
                )
            )

            if (
                normalized_text
                in used_question_texts
            ):
                raise HTTPException(
                    status_code=502,
                    detail=(
                        "AI generated a duplicate "
                        "question: "
                        f"{question.question_text}"
                    ),
                )

            used_question_texts.add(
                normalized_text
            )

            generated_questions.append(
                question
            )

    # =====================================================
    # 11. FINAL COUNT CHECK
    # =====================================================

    if (
        len(generated_questions)
        != payload.question_count
    ):
        raise HTTPException(
            status_code=502,
            detail=(
                "Quiz generation produced "
                f"{len(generated_questions)} "
                "questions but "
                f"{payload.question_count} "
                "were requested."
            ),
        )

    # =====================================================
    # 12. CREATE QUIZ PAYLOAD
    # =====================================================

    create_payload = QuizCreate(
        subject_id=payload.subject_id,
        title=payload.title,
        difficulty=payload.difficulty,
        duration_minutes=(
            payload.duration_minutes
        ),
        document_ids=(
            requested_document_ids
        ),
        questions=(
            generated_questions
        ),
    )

    generation_prompt = (
        "Backend-controlled quiz generation. "
        f"question_count="
        f"{payload.question_count}; "
        f"difficulty="
        f"{payload.difficulty}; "
        f"source_chunk_ids="
        f"{generation_sources}; "
        "single-correct-answer semantic rules enabled."
    )

    # =====================================================
    # 13. SAVE QUIZ
    # =====================================================

    return create_quiz(
        db=db,
        owner_id=owner_id,
        payload=create_payload,
        generation_mode="AI",
        ai_model=ai_model_name,
        generation_prompt=(
            generation_prompt
        ),
    )


# =========================================================
# PUBLISH QUIZ
# =========================================================


def publish_quiz(
    db: Session,
    quiz: Quiz,
) -> Quiz:
    quiz.status = "PUBLISHED"

    try:
        db.commit()

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=(
                "Cannot publish quiz: "
                f"{exc}"
            ),
        ) from exc

    db.refresh(quiz)

    return quiz


# =========================================================
# START QUIZ ATTEMPT
# =========================================================


def start_attempt(
    db: Session,
    user_id: int,
    quiz: Quiz,
) -> QuizAttempt:
    if (
        quiz.status != "PUBLISHED"
        and quiz.owner_id != user_id
    ):
        raise HTTPException(
            status_code=400,
            detail="Quiz is not published",
        )

    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=user_id,
        status="IN_PROGRESS",
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return attempt


# =========================================================
# SUBMIT QUIZ ATTEMPT
# =========================================================


def submit_attempt(
    db: Session,
    attempt: QuizAttempt,
    answers: list[dict],
) -> QuizAttempt:
    if attempt.status != "IN_PROGRESS":
        raise HTTPException(
            status_code=409,
            detail=(
                "Attempt has already "
                "been finalized"
            ),
        )

    quiz = db.get(
        Quiz,
        attempt.quiz_id,
    )

    if quiz is None:
        raise HTTPException(
            status_code=404,
            detail="Quiz not found",
        )

    questions = list(
        db.scalars(
            select(Question)
            .where(
                Question.quiz_id
                == attempt.quiz_id
            )
            .order_by(
                Question.question_order
            )
        ).all()
    )

    answer_map: dict[int, int | None] = {}

    for answer in answers:
        # FastAPI/Pydantic object
        if hasattr(answer, "model_dump"):
            answer_data = answer.model_dump()

        # Dictionary thông thường
        elif isinstance(answer, dict):
            answer_data = answer

        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid answer format"
                ),
            )

        question_id = answer_data.get(
            "question_id"
        )

        selected_option_id = (
            answer_data.get(
                "selected_option_id"
            )
        )

        if question_id is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "question_id is required"
                ),
            )

        answer_map[int(question_id)] = (
            int(selected_option_id)
            if selected_option_id
            is not None
            else None
        )

    question_ids = {
        question.id
        for question in questions
    }

    if not set(
        answer_map
    ).issubset(
        question_ids
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "One or more answers "
                "do not belong to this quiz"
            ),
        )

    max_score = Decimal("0")
    score = Decimal("0")

    correct_count = 0
    wrong_count = 0
    unanswered_count = 0

    # =====================================================
    # SCORE EACH QUESTION
    # =====================================================

    for question in questions:
        max_score += Decimal(
            question.points
        )

        selected_id = answer_map.get(
            question.id
        )

        selected = None

        if selected_id is not None:
            selected = db.scalar(
                select(QuestionOption)
                .where(
                    QuestionOption.id
                    == selected_id,
                    QuestionOption.question_id
                    == question.id,
                )
            )

            if selected is None:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Option {selected_id} "
                        "does not belong to "
                        f"question {question.id}"
                    ),
                )

        is_correct = bool(
            selected
            and selected.is_correct
        )

        awarded = (
            Decimal(question.points)
            if is_correct
            else Decimal("0")
        )

        if selected is None:
            unanswered_count += 1

        elif is_correct:
            correct_count += 1
            score += awarded

        else:
            wrong_count += 1

        db.add(
            UserAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                selected_option_id=(
                    selected_id
                ),
                is_correct=(
                    is_correct
                    if selected is not None
                    else None
                ),
                points_awarded=awarded,
            )
        )

        # =================================================
        # TOPIC MASTERY
        # =================================================

        if (
            question.source_chunk_id
            and quiz.subject_id
        ):
            section_id = db.scalar(
                select(
                    DocumentChunk.section_id
                ).where(
                    DocumentChunk.id
                    == question.source_chunk_id
                )
            )

            if section_id:
                mastery = db.scalar(
                    select(TopicMastery).where(
                        TopicMastery.user_id
                        == attempt.user_id,
                        TopicMastery.section_id
                        == section_id,
                    )
                )

                # -----------------------------------------
                # Create new mastery row
                # -----------------------------------------

                if mastery is None:
                    mastery = TopicMastery(
                        user_id=attempt.user_id,
                        subject_id=quiz.subject_id,
                        section_id=section_id,
                        attempts=0,
                        correct_answers=0,
                        wrong_answers=0,
                        mastery_score=Decimal("0"),
                    )

                    db.add(mastery)
                    db.flush()

                # -----------------------------------------
                # Safely normalize numeric values
                # -----------------------------------------

                attempts = int(
                    mastery.attempts or 0
                )

                correct_answers = int(
                    mastery.correct_answers or 0
                )

                wrong_answers = int(
                    mastery.wrong_answers or 0
                )

                # Every question counts as an attempt,
                # including unanswered questions.
                attempts += 1

                if is_correct:
                    correct_answers += 1

                elif selected is not None:
                    wrong_answers += 1

                # -----------------------------------------
                # Save counters
                # -----------------------------------------

                mastery.attempts = attempts
                mastery.correct_answers = (
                    correct_answers
                )
                mastery.wrong_answers = (
                    wrong_answers
                )

                # -----------------------------------------
                # Calculate mastery score safely
                # -----------------------------------------

                mastery.mastery_score = (
                    Decimal(correct_answers)
                    * Decimal("100")
                    / Decimal(
                        max(1, attempts)
                    )
                ).quantize(
                    Decimal("0.01")
                )

                mastery.last_practiced_at = (
                    datetime.now(
                        timezone.utc
                    )
                )

    # =====================================================
    # FINALIZE ATTEMPT
    # =====================================================

    now = datetime.now(
        timezone.utc
    )

    attempt.status = "SUBMITTED"
    attempt.submitted_at = now

    if attempt.started_at:
        attempt.time_spent_seconds = max(
            0,
            int(
                (
                    now
                    - attempt.started_at
                ).total_seconds()
            ),
        )
    else:
        attempt.time_spent_seconds = None

    attempt.score = score
    attempt.max_score = max_score

    attempt.correct_count = (
        correct_count
    )

    attempt.wrong_count = (
        wrong_count
    )

    attempt.unanswered_count = (
        unanswered_count
    )

    if max_score == 0:
        attempt.percentage = Decimal(
            "0"
        )
    else:
        attempt.percentage = (
            score
            * Decimal("100")
            / max_score
        ).quantize(
            Decimal("0.01")
        )

    # =====================================================
    # DAILY LEARNING STAT
    # =====================================================

    today = date.today()

    stat = db.scalar(
        select(DailyLearningStat).where(
            DailyLearningStat.user_id
            == attempt.user_id,
            DailyLearningStat.activity_date
            == today,
        )
    )

    if stat is None:
        stat = DailyLearningStat(
            user_id=attempt.user_id,
            activity_date=today,
        )

        db.add(stat)
        db.flush()

    stat.quiz_attempts = (
        int(
            stat.quiz_attempts
            or 0
        )
        + 1
    )

    stat.questions_answered = (
        int(
            stat.questions_answered
            or 0
        )
        + len(questions)
    )

    stat.correct_answers = (
        int(
            stat.correct_answers
            or 0
        )
        + correct_count
    )

    # =====================================================
    # SUBJECT PROGRESS
    # =====================================================

    if quiz.subject_id:
        progress = db.scalar(
            select(UserSubjectProgress).where(
                UserSubjectProgress.user_id
                == attempt.user_id,
                UserSubjectProgress.subject_id
                == quiz.subject_id,
            )
        )

        if progress is None:
            progress = UserSubjectProgress(
                user_id=(
                    attempt.user_id
                ),
                subject_id=(
                    quiz.subject_id
                ),
            )

            db.add(progress)

        progress.quizzes_completed = (
            int(
                progress.quizzes_completed
                or 0
            )
            + 1
        )

        prior_count = max(
            0,
            progress.quizzes_completed
            - 1,
        )

        prior_avg = Decimal(
            progress.average_score
            or 0
        )

        progress.average_score = (
            (
                prior_avg
                * prior_count
            )
            + attempt.percentage
        ) / progress.quizzes_completed

        progress.last_activity_at = now

    # =====================================================
    # GAMIFICATION
    # =====================================================

    xp = (
        10
        + correct_count * 2
    )

    add_xp(
        db,
        attempt.user_id,
        xp,
        "QUIZ_ATTEMPT",
        attempt.id,
        "Completed quiz",
    )

    db.flush()

    evaluate_badges(
        db,
        attempt.user_id,
        quiz_percentage=float(
            attempt.percentage
            or 0
        ),
    )

    # =====================================================
    # COMMIT
    # =====================================================

    db.commit()
    db.refresh(attempt)

    return attempt