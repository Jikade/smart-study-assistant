
from __future__ import annotations

from app.services.quiz_service import (
    _evidence_uses_answer_as_label,
    _looks_like_clause_option,
    _sanitize_v6_distractors,
)


def main():
    evidence = (
        "• Giá trị sử dụng: Thể hiện trong quá trình lao động."
    )

    assert _evidence_uses_answer_as_label(
        answer_text="Giá trị sử dụng",
        evidence_quote=evidence,
    )

    assert _looks_like_clause_option(
        "Là nơi lưu trữ giá trị"
    )

    assert not _looks_like_clause_option(
        "Giá trị thặng dư"
    )

    (
        cleaned,
        replacements,
    ) = _sanitize_v6_distractors(
        model_distractors=[
            "Là nơi lưu trữ giá trị",
            "Là nơi sản xuất giá trị",
            "Là nơi tạo ra lợi nhuận",
        ],
        answer_text="Giá trị sử dụng",
        evidence_quote=evidence,
        slot_answers={
            "A0": {
                "text": "Giá trị sử dụng",
                "evidence_id": "E0",
            },
            "A1": {
                "text": "Giá trị thặng dư",
                "evidence_id": "E1",
            },
            "A2": {
                "text": "Giá trị sức lao động",
                "evidence_id": "E2",
            },
            "A3": {
                "text": "Tư bản khả biến",
                "evidence_id": "E3",
            },
            "A4": {
                "text": "Tư bản bất biến",
                "evidence_id": "E4",
            },
        },
    )

    assert len(cleaned) == 3, cleaned

    assert all(
        not _looks_like_clause_option(
            option
        )
        for option
        in cleaned
    ), cleaned

    assert all(
        not option.casefold().startswith(
            "là "
        )
        for option
        in cleaned
    ), cleaned

    assert replacements == 3, replacements

    print()
    print("=" * 72)
    print("PERFORMANCE V6.4.4 OPTION-SHAPE GUARD TEST")
    print("=" * 72)
    print("Label-style evidence detected:", True)
    print("Clause distractors rejected:", True)
    print("Concept-label replacements used:", True)
    print("All distractors grammatically parallel:", True)
    print("Distractors:", cleaned)
    print("Result: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
