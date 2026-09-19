from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from datetime import (
    date,
    datetime,
    timedelta,
)


# =========================================================
# MASTERY RULES
# =========================================================

MIN_MASTERY_ATTEMPTS = 2

WEAK_MASTERY_THRESHOLD = 60.0
STRONG_MASTERY_THRESHOLD = 80.0


def _classify_mastery(
    attempts: int,
    mastery_score: float,
) -> str:

    if attempts < MIN_MASTERY_ATTEMPTS:
        return "NOT_ENOUGH_DATA"

    if mastery_score < WEAK_MASTERY_THRESHOLD:
        return "WEAK"

    if mastery_score < STRONG_MASTERY_THRESHOLD:
        return "DEVELOPING"

    return "STRONG"


# =========================================================
# TOPIC MASTERY
# =========================================================


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
    # 2. LOAD SECTIONS + MASTERY
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

# =========================================================
# ADAPTIVE PRACTICE RECOMMENDATION
# =========================================================


PRACTICE_STATUS_PRIORITY = {
    "WEAK": 0,
    "DEVELOPING": 1,
    "NOT_ENOUGH_DATA": 2,
}


PRACTICE_STRATEGY = (
    "WEAK > DEVELOPING > "
    "NOT_ENOUGH_DATA; STRONG skipped"
)


def _practice_recommendation_sort_key(
    topic: dict,
) -> tuple:
    """
    Adaptive Practice ranking algorithm.

    Priority:
        1. WEAK
        2. DEVELOPING
        3. NOT_ENOUGH_DATA
        4. STRONG is excluded

    Inside WEAK / DEVELOPING:
        - lower mastery first
        - more attempts first when scores tie

    Inside NOT_ENOUGH_DATA:
        - fewer attempts first
    """

    status = str(
        topic.get(
            "status",
            "",
        )
    )

    priority = (
        PRACTICE_STATUS_PRIORITY.get(
            status,
            999,
        )
    )

    attempts = int(
        topic.get(
            "attempts",
            0,
        )
        or 0
    )

    mastery_score = float(
        topic.get(
            "mastery_score",
            0,
        )
        or 0
    )

    section_id = int(
        topic.get(
            "section_id",
            0,
        )
        or 0
    )

    if (
        status
        == "NOT_ENOUGH_DATA"
    ):
        return (
            priority,
            attempts,
            section_id,
        )

    return (
        priority,
        mastery_score,
        -attempts,
        section_id,
    )


def _practice_recommendation_reason(
    topic: dict,
) -> str:

    status = str(
        topic.get(
            "status",
            "",
        )
    )

    score = float(
        topic.get(
            "mastery_score",
            0,
        )
        or 0
    )

    attempts = int(
        topic.get(
            "attempts",
            0,
        )
        or 0
    )

    if status == "WEAK":
        return (
            "Mastery is below 60%, "
            "so this topic should be "
            "reviewed first."
        )

    if status == "DEVELOPING":
        return (
            f"Mastery is {score:.2f}%. "
            "The learner has basic "
            "understanding but still needs "
            "more practice to reach STRONG."
        )

    if (
        status
        == "NOT_ENOUGH_DATA"
    ):
        return (
            f"Only {attempts} attempt(s) "
            "are available. More practice "
            "is needed to measure mastery "
            "reliably."
        )

    return (
        "No adaptive practice "
        "is currently required."
    )


def get_practice_recommendations(
    db: Session,
    *,
    user_id: int,
    subject_id: int,
) -> dict:
    """
    Build a personalized topic queue.

    This function does NOT use AI to decide
    priorities. Ranking is controlled entirely
    by backend rules.
    """

    mastery = (
        get_subject_topic_mastery(
            db,
            user_id=user_id,
            subject_id=subject_id,
        )
    )

    topics = list(
        mastery.get(
            "topics",
            []
        )
    )

    # -----------------------------------------------------
    # Exclude STRONG topics
    # -----------------------------------------------------

    candidates = [
        dict(topic)

        for topic
        in topics

        if (
            str(
                topic.get(
                    "status",
                    "",
                )
            )
            in PRACTICE_STATUS_PRIORITY
        )
    ]

    candidates.sort(
        key=(
            _practice_recommendation_sort_key
        )
    )

    recommendations: list[
        dict
    ] = []

    for rank, topic in enumerate(
        candidates,
        start=1,
    ):
        recommendation = {
            "rank": rank,

            "section_id":
                int(
                    topic[
                        "section_id"
                    ]
                ),

            "title":
                topic[
                    "title"
                ],

            "attempts":
                int(
                    topic.get(
                        "attempts",
                        0,
                    )
                    or 0
                ),

            "correct_answers":
                int(
                    topic.get(
                        "correct_answers",
                        0,
                    )
                    or 0
                ),

            "wrong_answers":
                int(
                    topic.get(
                        "wrong_answers",
                        0,
                    )
                    or 0
                ),

            "mastery_score":
                float(
                    topic.get(
                        "mastery_score",
                        0,
                    )
                    or 0
                ),

            "status":
                topic[
                    "status"
                ],

            "last_practiced_at":
                topic.get(
                    "last_practiced_at"
                ),

            "reason":
                _practice_recommendation_reason(
                    topic
                ),
        }

        recommendations.append(
            recommendation
        )

    skipped_strong_topics = sum(
        1

        for topic
        in topics

        if (
            topic.get(
                "status"
            )
            == "STRONG"
        )
    )

    return {
        "subject_id":
            mastery[
                "subject_id"
            ],

        "subject_name":
            mastery[
                "subject_name"
            ],

        "strategy":
            PRACTICE_STRATEGY,

        "recommendation_count":
            len(
                recommendations
            ),

        "skipped_strong_topics":
            skipped_strong_topics,

        "recommendations":
            recommendations,
    }

# =========================================================
# SPACED PRACTICE SCHEDULER
# =========================================================


SPACED_PRACTICE_ALGORITHM = (
    "SSA-SR-V1"
)


SPACED_STATUS_WEIGHT = {
    "WEAK": 400,
    "DEVELOPING": 300,
    "NOT_ENOUGH_DATA": 250,
    "STRONG": 100,
}


def _spacing_interval_days(
    *,
    status: str,
    mastery_score: float,
    attempts: int,
) -> int:
    """
    Smart Study Assistant Spaced Repetition V1.

    The interval is controlled completely
    by backend rules.

    No LLM is involved.
    """

    status = str(
        status or ""
    ).upper()

    score = float(
        mastery_score
        or 0
    )

    attempts = max(
        0,
        int(
            attempts
            or 0
        ),
    )

    # =====================================================
    # NOT ENOUGH DATA
    #
    # Needs another observation as soon as possible.
    # =====================================================

    if (
        status
        == "NOT_ENOUGH_DATA"
    ):
        return 0

    # =====================================================
    # WEAK
    # =====================================================

    if status == "WEAK":

        if score < 40:
            return 1

        return 2

    # =====================================================
    # DEVELOPING
    # =====================================================

    if status == "DEVELOPING":

        if score < 70:
            return 2

        return 3

    # =====================================================
    # STRONG
    # =====================================================

    if status == "STRONG":

        if (
            score >= 95
            and attempts >= 4
        ):
            return 14

        if score >= 90:
            return 10

        return 7

    # Defensive fallback.
    return 1


def _normalize_learning_datetime(
    value: datetime | None,
    *,
    now: datetime,
) -> datetime | None:
    """
    Normalize DB datetime into the same timezone
    used by current server time.
    """

    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(
            tzinfo=now.tzinfo
        )

    return value.astimezone(
        now.tzinfo
    )


def _spacing_due_status(
    *,
    now: datetime,
    next_review_at: datetime,
    never_practiced: bool,
) -> str:

    if never_practiced:
        return "NEW"

    if next_review_at <= now:
        return "DUE"

    if (
        next_review_at.date()
        == now.date()
    ):
        return "DUE_TODAY"

    return "UPCOMING"


def _spacing_priority_score(
    *,
    status: str,
    mastery_score: float,
    attempts: int,
    next_review_at: datetime,
    now: datetime,
) -> float:
    """
    Higher score = higher study priority.

    Components:
      status importance
      weakness
      data uncertainty
      whether already due
      how many days overdue
    """

    status = str(
        status or ""
    ).upper()

    mastery_score = float(
        mastery_score
        or 0
    )

    attempts = max(
        0,
        int(
            attempts
            or 0
        ),
    )

    status_weight = float(
        SPACED_STATUS_WEIGHT.get(
            status,
            0,
        )
    )

    weakness_bonus = max(
        0.0,
        100.0
        - mastery_score,
    )

    # attempts < 2 means mastery is not reliable yet.
    uncertainty_bonus = float(
        max(
            0,
            2 - attempts,
        )
        * 40
    )

    due_bonus = (
        100.0
        if (
            next_review_at
            <= now
        )
        else 0.0
    )

    overdue_days = max(
        0,
        (
            now.date()
            - next_review_at.date()
        ).days,
    )

    overdue_bonus = float(
        min(
            overdue_days,
            30,
        )
        * 10
    )

    return round(
        status_weight
        + weakness_bonus
        + uncertainty_bonus
        + due_bonus
        + overdue_bonus,
        2,
    )


def _spacing_reason(
    *,
    status: str,
    mastery_score: float,
    attempts: int,
    interval_days: int,
) -> str:

    status = str(
        status or ""
    ).upper()

    score = float(
        mastery_score
        or 0
    )

    attempts = int(
        attempts
        or 0
    )

    if (
        status
        == "NOT_ENOUGH_DATA"
    ):
        return (
            f"Only {attempts} attempt(s) are available. "
            "Another practice session is scheduled "
            "to obtain enough mastery evidence."
        )

    if status == "WEAK":
        return (
            f"Mastery is {score:.2f}%. "
            f"Review again after {interval_days} "
            "day(s) because this topic is WEAK."
        )

    if status == "DEVELOPING":
        return (
            f"Mastery is {score:.2f}%. "
            f"Review after {interval_days} "
            "day(s) to reinforce the topic."
        )

    if status == "STRONG":
        return (
            f"Mastery is {score:.2f}%. "
            f"The topic is STRONG, so its review "
            f"interval is expanded to "
            f"{interval_days} day(s)."
        )

    return (
        f"Review after "
        f"{interval_days} day(s)."
    )


def get_subject_study_plan(
    db: Session,
    *,
    user_id: int,
    subject_id: int,
    horizon_days: int = 7,
) -> dict:
    """
    Generate a dynamic spaced-practice calendar.

    V1 does not persist scheduling rows.

    Every request recalculates the plan from:
      - TopicMastery
      - mastery status
      - attempts
      - mastery_score
      - last_practiced_at

    This ensures the study plan automatically changes
    after every quiz attempt.
    """

    # =====================================================
    # VALIDATE HORIZON
    # =====================================================

    if not 1 <= horizon_days <= 90:
        raise HTTPException(
            status_code=400,
            detail=(
                "horizon_days must be "
                "between 1 and 90."
            ),
        )

    # =====================================================
    # LOAD CURRENT MASTERY
    # =====================================================

    mastery = (
        get_subject_topic_mastery(
            db,
            user_id=user_id,
            subject_id=subject_id,
        )
    )

    topics = list(
        mastery.get(
            "topics",
            []
        )
    )

    # Use server local timezone.
    now = (
        datetime.now()
        .astimezone()
    )

    today = now.date()

    horizon_end = (
        today
        + timedelta(
            days=(
                horizon_days
                - 1
            )
        )
    )

    # =====================================================
    # CREATE CALENDAR BUCKETS
    # =====================================================

    day_buckets: dict[
        date,
        list[dict],
    ] = {
        (
            today
            + timedelta(
                days=offset
            )
        ): []

        for offset
        in range(
            horizon_days
        )
    }

    scheduled_topics = 0
    due_topics = 0
    deferred_topics = 0

    # =====================================================
    # CALCULATE ONE REVIEW DATE PER TOPIC
    # =====================================================

    for topic in topics:

        status = str(
            topic.get(
                "status",
                "",
            )
        ).upper()

        score = float(
            topic.get(
                "mastery_score",
                0,
            )
            or 0
        )

        attempts = int(
            topic.get(
                "attempts",
                0,
            )
            or 0
        )

        interval_days = (
            _spacing_interval_days(
                status=status,
                mastery_score=score,
                attempts=attempts,
            )
        )

        last_practiced_at = (
            _normalize_learning_datetime(
                topic.get(
                    "last_practiced_at"
                ),
                now=now,
            )
        )

        never_practiced = (
            last_practiced_at
            is None
        )

        if never_practiced:

            # New / insufficiently measured topic
            # should be available immediately.
            next_review_at = now

        else:

            next_review_at = (
                last_practiced_at
                + timedelta(
                    days=interval_days
                )
            )

        due_status = (
            _spacing_due_status(
                now=now,
                next_review_at=(
                    next_review_at
                ),
                never_practiced=(
                    never_practiced
                ),
            )
        )

        priority_score = (
            _spacing_priority_score(
                status=status,
                mastery_score=score,
                attempts=attempts,
                next_review_at=(
                    next_review_at
                ),
                now=now,
            )
        )

        # Overdue topics are placed today.
        scheduled_date = max(
            today,
            next_review_at.date(),
        )

        item = {
            "section_id":
                int(
                    topic[
                        "section_id"
                    ]
                ),

            "title":
                topic[
                    "title"
                ],

            "attempts":
                attempts,

            "correct_answers":
                int(
                    topic.get(
                        "correct_answers",
                        0,
                    )
                    or 0
                ),

            "wrong_answers":
                int(
                    topic.get(
                        "wrong_answers",
                        0,
                    )
                    or 0
                ),

            "mastery_score":
                score,

            "mastery_status":
                status,

            "interval_days":
                interval_days,

            "last_practiced_at":
                last_practiced_at,

            "next_review_at":
                next_review_at,

            "scheduled_date":
                scheduled_date,

            "due_status":
                due_status,

            "priority_score":
                priority_score,

            "reason":
                _spacing_reason(
                    status=status,
                    mastery_score=score,
                    attempts=attempts,
                    interval_days=(
                        interval_days
                    ),
                ),
        }

        if next_review_at <= now:
            due_topics += 1

        # =================================================
        # WITHIN REQUESTED HORIZON
        # =================================================

        if (
            scheduled_date
            <= horizon_end
        ):
            day_buckets[
                scheduled_date
            ].append(
                item
            )

            scheduled_topics += 1

        else:
            deferred_topics += 1

    # =====================================================
    # SORT EACH DAY BY PRIORITY
    # =====================================================

    days: list[dict] = []

    for plan_date in sorted(
        day_buckets
    ):

        items = day_buckets[
            plan_date
        ]

        items.sort(
            key=lambda item: (
                -float(
                    item[
                        "priority_score"
                    ]
                ),
                int(
                    item[
                        "section_id"
                    ]
                ),
            )
        )

        days.append(
            {
                "date":
                    plan_date,

                "item_count":
                    len(
                        items
                    ),

                "items":
                    items,
            }
        )

    return {
        "subject_id":
            mastery[
                "subject_id"
            ],

        "subject_name":
            mastery[
                "subject_name"
            ],

        "generated_at":
            now,

        "horizon_days":
            horizon_days,

        "algorithm":
            SPACED_PRACTICE_ALGORITHM,

        "total_topics":
            len(
                topics
            ),

        "scheduled_topics":
            scheduled_topics,

        "due_topics":
            due_topics,

        "deferred_topics":
            deferred_topics,

        "days":
            days,
    }

# =========================================================
# WEAK TOPICS
# =========================================================


def get_weak_topics(
    db: Session,
    *,
    user_id: int,
    subject_id: int,
) -> dict:

    mastery = get_subject_topic_mastery(
        db,
        user_id=user_id,
        subject_id=subject_id,
    )

    weak_topics = [
        topic
        for topic in mastery["topics"]
        if topic["status"] == "WEAK"
    ]

    # Weakest topic first.
    weak_topics.sort(
        key=lambda topic: (
            float(
                topic["mastery_score"]
            ),
            -int(
                topic["attempts"]
            ),
            int(
                topic["section_id"]
            ),
        )
    )

    return {
        "subject_id":
            mastery["subject_id"],

        "subject_name":
            mastery["subject_name"],

        "threshold":
            WEAK_MASTERY_THRESHOLD,

        "minimum_attempts":
            MIN_MASTERY_ATTEMPTS,

        "count":
            len(weak_topics),

        "topics":
            weak_topics,
    }