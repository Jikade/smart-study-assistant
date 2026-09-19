
from __future__ import annotations

from types import SimpleNamespace

from app.services.quiz_service import (
    _deterministic_cloze_repair,
    _question_answer_fit_issue,
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
    # 1) Quiz 18 Q1:
    # distractor containing the entire correct answer
    # must not survive.
    # -----------------------------------------------------

    (
        term_distractors,
        term_replacements,
    ) = _sanitize_v6_distractors(
        model_distractors=[
            "Giá trị thặng dư",
            "Giá trị tư bản",
            "Giá trị sử dụng trong tiêu dùng",
        ],
        answer_text="Giá trị sử dụng",
        evidence_quote=(
            "Giá trị sử dụng: Thể hiện trong quá trình "
            "lao động."
        ),
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
        },
    )

    assert len(
        term_distractors
    ) == 3

    assert (
        "Giá trị sử dụng trong tiêu dùng"
        not in term_distractors
    ), term_distractors

    assert term_replacements >= 1

    # -----------------------------------------------------
    # 2) Quiz 18 Q2:
    # generic formula question is ambiguous because source
    # contains TWO W formulas.
    # -----------------------------------------------------

    evidence = (
        "Khi đó, công thức W = c + v + m "
        "chuyển thành W = k + m."
    )

    ambiguous_formula = make_question(
        "Công thức tính W là gì?",
        "W = k + m",
        [
            "W = k + v",
            "W = c + m",
            "W = k - m",
        ],
    )

    issue = _question_answer_fit_issue(
        ambiguous_formula,
        evidence_quote=evidence,
    )

    assert issue is not None
    assert (
        "ambiguous"
        in issue
    ), issue

    # -----------------------------------------------------
    # 3) Contextualized formula question passes.
    # -----------------------------------------------------

    contextual_formula = make_question(
        (
            "Sau khi chuyển đổi với k = c + v, "
            "công thức W được viết như thế nào?"
        ),
        "W = k + m",
        [
            "W = k + v",
            "W = c + m",
            "W = k - m",
        ],
    )

    assert (
        _question_answer_fit_issue(
            contextual_formula,
            evidence_quote=evidence,
        )
        is None
    )

    # -----------------------------------------------------
    # 4) Early deterministic cloze repair resolves the
    # ambiguous formula stem without an AI call.
    # -----------------------------------------------------

    repaired = _deterministic_cloze_repair(
        ambiguous_formula,
        evidence_quote=evidence,
    )

    assert repaired is not None

    repaired_issue = _question_answer_fit_issue(
        repaired,
        evidence_quote=evidence,
    )

    assert repaired_issue is None, repaired_issue

    assert (
        "_____"
        in repaired.question_text
    )

    assert (
        "W = k + m"
        not in repaired.question_text
    )

    print()
    print("=" * 72)
    print("PERFORMANCE V6.4.3 FINAL AMBIGUITY GUARD TEST")
    print("=" * 72)
    print("Correct-answer-containing distractor rejected:", True)
    print("Ambiguous generic formula stem rejected:", True)
    print("Contextual formula stem accepted:", True)
    print("Ambiguous formula repaired deterministically:", True)
    print("Term distractors:", term_distractors)
    print("Repaired formula stem:", repaired.question_text)
    print("Result: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
