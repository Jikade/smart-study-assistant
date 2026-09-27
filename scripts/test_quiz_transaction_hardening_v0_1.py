from __future__ import annotations

from unittest.mock import patch

import app.services.quiz_service as quiz_service

from app.db.models import (
    Question,
    Quiz,
)
from app.schemas.quizzes import (
    OptionCreate,
    QuestionCreate,
    QuizCreate,
)


def make_payload() -> QuizCreate:
    return QuizCreate(
        subject_id=40,
        title="Transaction hardening regression",
        description="rollback test",
        difficulty="MEDIUM",
        duration_minutes=10,
        visibility="PRIVATE",
        document_ids=[20],
        questions=[
            QuestionCreate(
                question_text=(
                    "Sự kiện mẫu diễn ra vào thời gian nào?"
                ),
                difficulty="MEDIUM",
                explanation="Evidence",
                source_chunk_id=557,
                options=[
                    OptionCreate(
                        option_key="A",
                        option_text="968",
                        is_correct=True,
                        position=1,
                    ),
                    OptionCreate(
                        option_key="B",
                        option_text="1009",
                        is_correct=False,
                        position=2,
                    ),
                    OptionCreate(
                        option_key="C",
                        option_text="1226",
                        is_correct=False,
                        position=3,
                    ),
                    OptionCreate(
                        option_key="D",
                        option_text="1400",
                        is_correct=False,
                        position=4,
                    ),
                ],
            )
        ],
    )


class FakeSession:
    def __init__(
        self,
        *,
        fail_on_flush: int | None = None,
        fail_on_commit: bool = False,
    ):
        self.fail_on_flush = fail_on_flush
        self.fail_on_commit = fail_on_commit
        self.flush_count = 0
        self.commit_count = 0
        self.rollback_count = 0
        self.refresh_count = 0
        self.added = []
        self.next_quiz_id = 900
        self.next_question_id = 1900

    def add(self, value):
        self.added.append(value)

    def flush(self):
        self.flush_count += 1

        if (
            self.fail_on_flush is not None
            and self.flush_count
            == self.fail_on_flush
        ):
            raise RuntimeError(
                "simulated flush failure"
            )

        for value in self.added:
            if (
                isinstance(value, Quiz)
                and value.id is None
            ):
                value.id = self.next_quiz_id

            if (
                isinstance(value, Question)
                and value.id is None
            ):
                value.id = self.next_question_id
                self.next_question_id += 1

    def commit(self):
        self.commit_count += 1

        if self.fail_on_commit:
            raise RuntimeError(
                "simulated commit failure"
            )

    def rollback(self):
        self.rollback_count += 1

    def refresh(self, value):
        self.refresh_count += 1


def call_create(db: FakeSession):
    payload = make_payload()

    with (
        patch.object(
            quiz_service,
            "validate_owned_subject_id",
            return_value=40,
        ),
        patch.object(
            quiz_service,
            "validate_owned_document_ids",
            return_value=[20],
        ),
        patch.object(
            quiz_service,
            "validate_owned_active_chunk_ids",
            return_value=[557],
        ),
    ):
        return quiz_service.create_quiz(
            db,
            1,
            payload,
            generation_mode="V5_DETERMINISTIC",
        )


def expect_failure(db: FakeSession) -> None:
    try:
        call_create(db)
    except RuntimeError:
        pass
    else:
        raise AssertionError(
            "Expected simulated DB failure"
        )


def main() -> None:
    # Quiz flush succeeds; Question flush fails.
    flush_failure = FakeSession(
        fail_on_flush=2,
    )

    expect_failure(
        flush_failure
    )

    assert (
        flush_failure.rollback_count
        == 1
    )
    assert (
        flush_failure.commit_count
        == 0
    )
    assert (
        flush_failure.refresh_count
        == 0
    )

    # All flushes succeed; commit fails.
    commit_failure = FakeSession(
        fail_on_commit=True,
    )

    expect_failure(
        commit_failure
    )

    assert (
        commit_failure.rollback_count
        == 1
    )
    assert (
        commit_failure.commit_count
        == 1
    )
    assert (
        commit_failure.refresh_count
        == 0
    )

    # Normal path remains unchanged.
    success = FakeSession()

    quiz = call_create(
        success
    )

    assert quiz.id == 900
    assert success.flush_count == 2
    assert success.commit_count == 1
    assert success.rollback_count == 0
    assert success.refresh_count == 1

    print()
    print("=" * 92)
    print("QUIZ TRANSACTION HARDENING V0.1 REGRESSION")
    print("=" * 92)
    print("Question flush failure rolled back :", True)
    print("Flush failure committed            :", False)
    print("Commit failure rolled back         :", True)
    print("Success path committed once        :", True)
    print("Success path rollback              :", False)
    print("Shared V4/V5 create path intact    :", True)
    print("Result                             : PASS")
    print("=" * 92)


if __name__ == "__main__":
    main()
