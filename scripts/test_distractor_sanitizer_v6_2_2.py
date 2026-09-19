
from __future__ import annotations

from app.services.quiz_service import (
    _sanitize_v6_distractors,
)


def main():
    # -----------------------------------------------------
    # TERM case:
    # one model distractor is actually supported by the
    # selected evidence. Backend replaces it with a safe
    # candidate from another evidence span.
    # -----------------------------------------------------

    term_answer = (
        "Cạnh tranh giữa các ngành"
    )

    term_evidence = (
        "Cạnh tranh giữa các ngành là sự cạnh tranh "
        "giữa các chủ thể thuộc các ngành khác nhau."
    )

    term_slot_answers = {
        "A0": {
            "text": (
                "Cạnh tranh giữa các ngành"
            ),
            "evidence_id": "E0",
        },
        "A1": {
            "text": (
                "Tỷ suất lợi nhuận"
            ),
            "evidence_id": "E1",
        },
        "A2": {
            "text": (
                "Giá trị thặng dư"
            ),
            "evidence_id": "E2",
        },
        "A3": {
            "text": (
                "Cạnh tranh trong ngành"
            ),
            "evidence_id": "E3",
        },
    }

    term_distractors = [
        # Unsafe: appears in selected evidence.
        "các ngành khác nhau",
        # Safe model distractors.
        "Độc quyền",
        "Tích tụ tư bản",
    ]

    (
        cleaned_term,
        replaced_term,
    ) = _sanitize_v6_distractors(
        model_distractors=(
            term_distractors
        ),
        answer_text=(
            term_answer
        ),
        evidence_quote=(
            term_evidence
        ),
        slot_answers=(
            term_slot_answers
        ),
    )

    assert len(
        cleaned_term
    ) == 3

    assert (
        "các ngành khác nhau"
        not in cleaned_term
    )

    assert replaced_term >= 1

    # -----------------------------------------------------
    # FORMULA case:
    # all model distractors are unusable. Backend may use
    # candidate pool + deterministic formula variants.
    # -----------------------------------------------------

    formula_answer = (
        "W = k + m"
    )

    formula_evidence = (
        "W = c + v + m chuyển thành W = k + m."
    )

    formula_slot_answers = {
        "A0": {
            "text": (
                "W = k + m"
            ),
            "evidence_id": "E0",
        },
    }

    (
        cleaned_formula,
        replaced_formula,
    ) = _sanitize_v6_distractors(
        model_distractors=[
            "W = k + m",
            "",
            "W = k + m",
        ],
        answer_text=(
            formula_answer
        ),
        evidence_quote=(
            formula_evidence
        ),
        slot_answers=(
            formula_slot_answers
        ),
    )

    assert len(
        cleaned_formula
    ) == 3

    assert (
        formula_answer
        not in cleaned_formula
    )

    assert replaced_formula == 3

    assert any(
        "-" in option
        or "×" in option
        or "/" in option
        for option
        in cleaned_formula
    )

    print()
    print("=" * 72)
    print("PERFORMANCE V6.2.2 DISTRACTOR SANITIZER TEST")
    print("=" * 72)
    print("Evidence-supported distractor removed:", True)
    print("Backend candidate replacement used:", True)
    print("Formula fallback variants generated:", True)
    print("Exactly three safe distractors preserved:", True)
    print("Term distractors:", cleaned_term)
    print("Formula distractors:", cleaned_formula)
    print("Result: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
