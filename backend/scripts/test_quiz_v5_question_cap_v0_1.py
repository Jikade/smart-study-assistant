from __future__ import annotations

from pydantic import ValidationError

from app.main import app
from app.schemas.quizzes import (
    QuizGenerateRequest,
    QuizV5GenerateRequest,
    QuizV5PreviewRequest,
)


def expect_validation_error(
    factory,
) -> None:
    try:
        factory()
    except ValidationError:
        return

    raise AssertionError(
        "Expected Pydantic validation failure"
    )


def main() -> None:
    v5_generate = QuizV5GenerateRequest(
        subject_id=40,
        document_ids=[20],
        title="V5 cap boundary",
        question_count=5,
        subject_family="history",
    )

    v5_preview = QuizV5PreviewRequest(
        subject_id=40,
        document_ids=[20],
        question_count=5,
        subject_family="history",
    )

    assert v5_generate.question_count == 5
    assert v5_preview.question_count == 5

    expect_validation_error(
        lambda: QuizV5GenerateRequest(
            subject_id=40,
            document_ids=[20],
            title="Must fail",
            question_count=6,
            subject_family="history",
        )
    )

    expect_validation_error(
        lambda: QuizV5PreviewRequest(
            subject_id=40,
            document_ids=[20],
            question_count=6,
            subject_family="history",
        )
    )

    v4 = QuizGenerateRequest(
        subject_id=40,
        document_ids=[20],
        title="V4 remains unchanged",
        question_count=50,
        difficulty="MEDIUM",
    )

    assert v4.question_count == 50

    generate_schema = (
        QuizV5GenerateRequest
        .model_json_schema()
    )

    preview_schema = (
        QuizV5PreviewRequest
        .model_json_schema()
    )

    assert (
        generate_schema["properties"]
        ["question_count"]
        ["maximum"]
        == 5
    )

    assert (
        preview_schema["properties"]
        ["question_count"]
        ["maximum"]
        == 5
    )

    paths = app.openapi()["paths"]

    assert "/api/v1/quizzes/generate-v5" in paths
    assert "/api/v1/quizzes/generate-v5-preview" in paths
    assert "/api/v1/quizzes/generate" in paths

    print()
    print("=" * 88)
    print("QUIZ V5 QUESTION CAP V0.1 REGRESSION")
    print("=" * 88)
    print("V5 generate accepts 5      :", True)
    print("V5 generate rejects 6      :", True)
    print("V5 preview accepts 5       :", True)
    print("V5 preview rejects 6       :", True)
    print("V5 OpenAPI maximum         :", 5)
    print("V4 still accepts 50        :", True)
    print("V4 route intact            :", True)
    print("Result                     : PASS")
    print("=" * 88)


if __name__ == "__main__":
    main()
