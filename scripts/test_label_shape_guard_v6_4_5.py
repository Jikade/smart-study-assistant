
from __future__ import annotations

from app.services.quiz_service import (
    _looks_like_concept_label,
    _sanitize_v6_distractors,
)


def main():
    assert _looks_like_concept_label(
        "Giá trị thặng dư"
    )

    assert _looks_like_concept_label(
        "Giá trị sức lao động"
    )

    assert _looks_like_concept_label(
        "Tư bản khả biến"
    )

    assert not _looks_like_concept_label(
        "cộng với chi phí đào tạo"
    )

    assert not _looks_like_concept_label(
        "Phần lớn hơn đó chính là giá trị thặng dư"
    )

    assert not _looks_like_concept_label(
        "Là nơi lưu trữ giá trị"
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
        evidence_quote=(
            "• Giá trị sử dụng: Thể hiện trong quá trình "
            "lao động."
        ),
        slot_answers={
            "A0": {
                "text": "Giá trị sử dụng",
                "evidence_id": "E0",
            },
            # Actual Quiz 20 bad fragments:
            "A1": {
                "text": "cộng với chi phí đào tạo",
                "evidence_id": "E1",
            },
            "A2": {
                "text": (
                    "Phần lớn hơn đó chính là "
                    "giá trị thặng dư"
                ),
                "evidence_id": "E2",
            },
            # Safe concept-label alternatives:
            "A3": {
                "text": "Giá trị thặng dư",
                "evidence_id": "E3",
            },
            "A4": {
                "text": "Giá trị sức lao động",
                "evidence_id": "E4",
            },
            "A5": {
                "text": "Tư bản khả biến",
                "evidence_id": "E5",
            },
            "A6": {
                "text": "Tư bản bất biến",
                "evidence_id": "E6",
            },
        },
    )

    assert len(cleaned) == 3, cleaned

    assert all(
        _looks_like_concept_label(
            option
        )
        for option
        in cleaned
    ), cleaned

    assert (
        "cộng với chi phí đào tạo"
        not in cleaned
    )

    assert (
        "Phần lớn hơn đó chính là giá trị thặng dư"
        not in cleaned
    )

    assert replacements == 3, replacements

    print()
    print("=" * 72)
    print("PERFORMANCE V6.4.5 LABEL-SHAPE GUARD TEST")
    print("=" * 72)
    print("Short concept labels accepted:", True)
    print("Connector fragment rejected:", True)
    print("Predicate fragment rejected:", True)
    print("Clause distractors rejected:", True)
    print("All final distractors are concept labels:", True)
    print("Distractors:", cleaned)
    print("Result: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
