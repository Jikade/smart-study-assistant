from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session


def _classify_mastery(
    attempts: int,
    mastery_score: float,
) -> str:
    if attempts < 2:
        return "NOT_ENOUGH_DATA"

    if mastery_score < 60:
        return "WEAK"

    if mastery_score < 80:
        return "DEVELOPING"

    return "STRONG"


def get_subject_topic_mastery(
    db: Session,
    *,
    user_id: int,
    subject_id: int,
) -> dict:

    # =====================================================
    # 1. CHECK SUBJECT
    # =====================================================

    subject = db.execute(
        text(
            """
            SELECT
                id,
                name
            FROM subjects
            WHERE id = :subject_id
              AND owner_id = :user_id
              AND is_archived = FALSE
            LIMIT 1
            """
        ),
        {
            "subject_id": subject_id,
            "user_id": user_id,
        },
    ).mappings().first()

    if subject is None:
        raise HTTPException(
            status_code=404,
            detail="Subject not found",
        )

    # =====================================================
    # 2. LOAD ALL SECTIONS OF THIS SUBJECT
    # =====================================================

    rows = db.execute(
        text(
            """
            SELECT
                ds.id AS section_id,
                ds.title AS section_title,
                ds.section_order,

                COALESCE(
                    tm.attempts,
                    0
                ) AS attempts,

                COALESCE(
                    tm.correct_answers,
                    0
                ) AS correct_answers,

                COALESCE(
                    tm.wrong_answers,
                    0
                ) AS wrong_answers,

                COALESCE(
                    tm.mastery_score,
                    0
                ) AS mastery_score,

                tm.last_practiced_at

            FROM document_sections ds

            JOIN documents d
                ON d.id = ds.document_id

            LEFT JOIN topic_mastery tm
                ON tm.section_id = ds.id
               AND tm.user_id = :user_id
               AND tm.subject_id = :subject_id

            WHERE d.subject_id = :subject_id
              AND d.owner_id = :user_id
              AND d.status = 'READY'

            ORDER BY
                ds.section_order,
                ds.id
            """
        ),
        {
            "user_id": user_id,
            "subject_id": subject_id,
        },
    ).mappings().all()

    # =====================================================
    # 3. BUILD TOPIC LIST
    # =====================================================

    topics: list[dict] = []

    weak_topics = 0
    developing_topics = 0
    strong_topics = 0
    not_enough_data_topics = 0

    for row in rows:

        attempts = int(
            row["attempts"] or 0
        )

        correct_answers = int(
            row["correct_answers"] or 0
        )

        wrong_answers = int(
            row["wrong_answers"] or 0
        )

        mastery_score = float(
            row["mastery_score"] or 0
        )

        status = _classify_mastery(
            attempts,
            mastery_score,
        )

        if status == "WEAK":
            weak_topics += 1

        elif status == "DEVELOPING":
            developing_topics += 1

        elif status == "STRONG":
            strong_topics += 1

        else:
            not_enough_data_topics += 1

        topics.append(
            {
                "section_id":
                    int(row["section_id"]),

                "title":
                    row["section_title"],

                "attempts":
                    attempts,

                "correct_answers":
                    correct_answers,

                "wrong_answers":
                    wrong_answers,

                "mastery_score":
                    round(
                        mastery_score,
                        2,
                    ),

                "status":
                    status,

                "last_practiced_at":
                    row[
                        "last_practiced_at"
                    ],
            }
        )

    # =====================================================
    # 4. RESPONSE
    # =====================================================

    return {
        "subject_id":
            int(subject["id"]),

        "subject_name":
            subject["name"],

        "summary": {
            "total_topics":
                len(topics),

            "weak_topics":
                weak_topics,

            "developing_topics":
                developing_topics,

            "strong_topics":
                strong_topics,

            "not_enough_data_topics":
                not_enough_data_topics,
        },

        "topics":
            topics,
    }