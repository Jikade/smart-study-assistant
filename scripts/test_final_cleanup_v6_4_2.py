
from __future__ import annotations

from types import SimpleNamespace

from app.services.quiz_service import (
    _deterministic_cloze_repair,
    _sanitize_v6_distractors,
)


def make_question(
    stem: str,
    correct: str,
    distractors: list[str],
):
    options = []

    for index, text in enumerate(
        [
            correct,
            *distractors,
        ]
    ):
        options.append(
            SimpleNamespace(
                option_key="ABCD"[index],
                option_text=text,
                is_correct=(
                    index == 0
                ),
            )
        )

    return SimpleNamespace(
        question_text=stem,
        options=options,
    )


def main():
    # -----------------------------------------------------
    # 1) Quiz 17 cloze bullet must be removed.
    # -----------------------------------------------------

    q1 = make_question(
        "Giá trị sử dụng là gì?",
        "Giá trị sử dụng",
        [
            "Giá trị thặng dư",
            "Giá trị tư liệu sản xuất",
            "Giá trị sức lao động",
        ],
    )

    repaired1 = (
        _deterministic_cloze_repair(
            q1,
            evidence_quote=(
                "• Giá trị sử dụng: Thể hiện trong "
                "quá trình lao động."
            ),
        )
    )

    assert repaired1 is not None

    assert (
        "•"
        not in repaired1.question_text
    ), repaired1.question_text

    assert (
        "_____: Thể hiện trong quá trình lao động."
        in repaired1.question_text
    ), repaired1.question_text

    # -----------------------------------------------------
    # 2) Quiz 17 section-4 cloze bullet must be removed.
    # -----------------------------------------------------

    q2 = make_question(
        "Cạnh tranh giữa các ngành là gì?",
        "Cạnh tranh giữa các ngành",
        [
            "Cạnh tranh trong ngành",
            "Độc quyền",
            "Tích tụ tư bản",
        ],
    )

    repaired2 = (
        _deterministic_cloze_repair(
            q2,
            evidence_quote=(
                "• Cạnh tranh giữa các ngành: Sự cạnh tranh "
                "giữa các nhà tư bản ở các ngành sản xuất "
                "khác nhau nhằm tìm nơi đầu tư có tỷ suất "
                "lợi nhuận cao hơn."
            ),
        )
    )

    assert repaired2 is not None
    assert "•" not in repaired2.question_text

    # -----------------------------------------------------
    # 3) Formula answer: non-formula distractor must be
    #    discarded and deterministically replaced.
    # -----------------------------------------------------

    formula_answer = "W = k + m"

    formula_evidence = (
        "Khi đó, công thức W = c + v + m "
        "chuyển thành W = k + m."
    )

    formula_slot_answers = {
        "A0": {
            "text": "W = k + m",
            "evidence_id": "E0",
        },
    }

    (
        formula_distractors,
        formula_replacements,
    ) = _sanitize_v6_distractors(
        model_distractors=[
            "W = k + v",
            "W = c + m",
            "lợi nhuận (p)",
        ],
        answer_text=formula_answer,
        evidence_quote=formula_evidence,
        slot_answers=formula_slot_answers,
    )

    assert len(formula_distractors) == 3
    assert all(
        "=" in option
        for option
        in formula_distractors
    ), formula_distractors

    assert (
        "lợi nhuận (p)"
        not in formula_distractors
    )

    assert formula_replacements >= 1

    # -----------------------------------------------------
    # 4) Term answer: formula distractor must not survive.
    # -----------------------------------------------------

    term_answer = "Cạnh tranh giữa các ngành"

    term_evidence = (
        "Cạnh tranh giữa các ngành là sự cạnh tranh "
        "giữa các nhà tư bản ở các ngành khác nhau."
    )

    term_slot_answers = {
        "A0": {
            "text": "Cạnh tranh giữa các ngành",
            "evidence_id": "E0",
        },
        "A1": {
            "text": "Cạnh tranh trong ngành",
            "evidence_id": "E1",
        },
        "A2": {
            "text": "Tỷ suất lợi nhuận",
            "evidence_id": "E2",
        },
        "A3": {
            "text": "Giá trị thặng dư",
            "evidence_id": "E3",
        },
    }

    (
        term_distractors,
        term_replacements,
    ) = _sanitize_v6_distractors(
        model_distractors=[
            "Cạnh tranh trong ngành",
            "W = k + m",
            "Độc quyền",
        ],
        answer_text=term_answer,
        evidence_quote=term_evidence,
        slot_answers=term_slot_answers,
    )

    assert len(term_distractors) == 3
    assert all(
        "=" not in option
        for option
        in term_distractors
    ), term_distractors

    assert term_replacements >= 1

    print()
    print("=" * 72)
    print("PERFORMANCE V6.4.2 FINAL CLEANUP TEST")
    print("=" * 72)
    print("Cloze bullet prefix removed:", True)
    print("Section-4 cloze formatting cleaned:", True)
    print("Formula distractor type enforced:", True)
    print("Term distractor type enforced:", True)
    print("Formula distractors:", formula_distractors)
    print("Term distractors:", term_distractors)
    print("Result: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
