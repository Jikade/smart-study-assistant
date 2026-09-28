
from __future__ import annotations

from types import SimpleNamespace

from app.services.quiz_service import (
    _answer_candidate_source_fit_issue,
    _deterministic_cloze_repair,
    _question_answer_fit_issue,
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
                is_correct=(index == 0),
            )
        )

    return SimpleNamespace(
        question_text=stem,
        options=options,
    )


def main():
    # -----------------------------------------------------
    # 1) Weak one-word heading must not be preselected.
    # -----------------------------------------------------
    weak = (
        _answer_candidate_source_fit_issue(
            answer_text="Giá trị",
            evidence_text=(
                "• Giá trị của hàng hóa biểu hiện "
                "một nội dung kinh tế nhất định."
            ),
        )
    )

    assert weak is not None

    # But an explicit definition is allowed.
    defined = (
        _answer_candidate_source_fit_issue(
            answer_text="Tiền",
            evidence_text=(
                "Tiền là hàng hóa đặc biệt được "
                "tách ra làm vật ngang giá chung."
            ),
        )
    )

    assert defined is None

    # -----------------------------------------------------
    # 2) Tautological term question is deterministically
    #    repaired into a cloze stem.
    # -----------------------------------------------------
    bad_term = make_question(
        "Cạnh tranh giữa các ngành là gì?",
        "Cạnh tranh giữa các ngành",
        [
            "Cạnh tranh trong ngành",
            "Độc quyền",
            "Tích tụ tư bản",
        ],
    )

    evidence_term = (
        "Cạnh tranh giữa các ngành là cạnh tranh "
        "giữa các chủ thể thuộc những ngành "
        "sản xuất khác nhau."
    )

    assert (
        _question_answer_fit_issue(
            bad_term,
            evidence_quote=evidence_term,
        )
        is not None
    )

    repaired_term = (
        _deterministic_cloze_repair(
            bad_term,
            evidence_quote=evidence_term,
        )
    )

    assert repaired_term is not None
    assert "_____" in repaired_term.question_text
    assert (
        "Cạnh tranh giữa các ngành"
        not in repaired_term.question_text
    )

    assert (
        _question_answer_fit_issue(
            repaired_term,
            evidence_quote=evidence_term,
        )
        is None
    )

    # -----------------------------------------------------
    # 3) English stem over Vietnamese formula source is
    #    repaired into a Vietnamese cloze.
    # -----------------------------------------------------
    bad_formula = make_question(
        "What is the correct formula after substitution?",
        "W = k + m",
        [
            "W = k + v",
            "W = c + m",
            "W = v + m",
        ],
    )

    evidence_formula = (
        "Công thức W = c + v + m chuyển thành "
        "W = k + m."
    )

    repaired_formula = (
        _deterministic_cloze_repair(
            bad_formula,
            evidence_quote=evidence_formula,
        )
    )

    assert repaired_formula is not None
    assert repaired_formula.question_text.startswith(
        "Điền công thức thích hợp"
    )

    assert "W = k + m" not in (
        repaired_formula.question_text
    )

    assert (
        _question_answer_fit_issue(
            repaired_formula,
            evidence_quote=evidence_formula,
        )
        is None
    )

    print()
    print("=" * 72)
    print("PERFORMANCE V6.4 EARLY QUALITY REPAIR TEST")
    print("=" * 72)
    print("Weak one-word heading rejected:", True)
    print("Explicit one-word definition preserved:", True)
    print("Tautological term repaired by cloze:", True)
    print("Cross-language formula repaired to VI cloze:", True)
    print("Correct answer removed from repaired stem:", True)
    print("Repaired questions pass deterministic fit:", True)
    print("Result: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
