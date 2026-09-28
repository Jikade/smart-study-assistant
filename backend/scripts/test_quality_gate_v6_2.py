
from __future__ import annotations

from types import SimpleNamespace

from app.services.quiz_service import (
    _answer_candidates_for_evidence,
    _clean_answer_candidate,
    _question_answer_fit_issue,
    _score_backend_answer_candidate,
)


def make_question(
    stem: str,
    correct: str,
    distractors: list[str],
):
    options = []

    texts = [
        correct,
        *distractors,
    ]

    for index, text in enumerate(
        texts
    ):
        options.append(
            SimpleNamespace(
                option_key=(
                    "ABCD"[index]
                ),
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
    # 1) Bullet cleanup
    # -----------------------------------------------------

    assert (
        _clean_answer_candidate(
            "• Giá trị"
        )
        == "Giá trị"
    )

    assert (
        _clean_answer_candidate(
            "▪ Cạnh tranh giữa các ngành"
        )
        == "Cạnh tranh giữa các ngành"
    )

    # -----------------------------------------------------
    # 2) Formula extraction
    # -----------------------------------------------------

    formula_source = (
        "W = c + v + m chuyển thành W = k + m."
    )

    candidates = (
        _answer_candidates_for_evidence(
            formula_source
        )
    )

    assert (
        "W = c + v + m"
        in candidates
    ), candidates

    assert (
        "W = k + m"
        in candidates
    ), candidates

    assert not any(
        "chuyển thành"
        in candidate
        and "=" in candidate
        for candidate
        in candidates
    ), candidates

    score_first = (
        _score_backend_answer_candidate(
            answer_text=(
                "W = c + v + m"
            ),
            evidence_text=(
                formula_source
            ),
        )
    )

    score_target = (
        _score_backend_answer_candidate(
            answer_text=(
                "W = k + m"
            ),
            evidence_text=(
                formula_source
            ),
        )
    )

    assert (
        score_target
        > score_first
    ), (
        score_first,
        score_target,
    )

    # -----------------------------------------------------
    # 3) Reject exact-answer leakage / tautology
    # -----------------------------------------------------

    q1 = make_question(
        "Giá trị gồm những yếu tố nào?",
        "Giá trị",
        [
            "Tư liệu sản xuất",
            "Tỷ suất lợi nhuận",
            "Cạnh tranh giữa các ngành",
        ],
    )

    issue1 = (
        _question_answer_fit_issue(
            q1
        )
    )

    assert issue1 is not None
    assert (
        "contains the correct answer"
        in issue1
    )

    q2 = make_question(
        "Cạnh tranh giữa các ngành là gì?",
        "Cạnh tranh giữa các ngành",
        [
            "Cạnh tranh trong ngành",
            "Tỷ suất lợi nhuận",
            "Giá trị thặng dư",
        ],
    )

    issue2 = (
        _question_answer_fit_issue(
            q2
        )
    )

    assert issue2 is not None

    # -----------------------------------------------------
    # 4) Accept a non-tautological term-identification item
    # -----------------------------------------------------

    good_term = make_question(
        (
            "Hình thức cạnh tranh nào diễn ra "
            "giữa các chủ thể thuộc ngành khác nhau?"
        ),
        "Cạnh tranh giữa các ngành",
        [
            "Cạnh tranh trong ngành",
            "Độc quyền",
            "Tích tụ tư bản",
        ],
    )

    assert (
        _question_answer_fit_issue(
            good_term
        )
        is None
    )

    # -----------------------------------------------------
    # 5) Formula fit
    # -----------------------------------------------------

    good_formula = make_question(
        "Biểu thức nào thể hiện công thức sau chuyển đổi?",
        "W = k + m",
        [
            "W = c + v",
            "W = c + m",
            "W = v + m",
        ],
    )

    assert (
        _question_answer_fit_issue(
            good_formula
        )
        is None
    )

    bad_formula = make_question(
        "Công thức nào được sử dụng?",
        "Giá trị",
        [
            "W = c + v",
            "W = k + m",
            "m' = m/v",
        ],
    )

    assert (
        _question_answer_fit_issue(
            bad_formula
        )
        is not None
    )

    print()
    print("=" * 72)
    print("PERFORMANCE V6.2 PEDAGOGICAL QUALITY GATE TEST")
    print("=" * 72)
    print("Bullet prefixes cleaned:", True)
    print("Formula equations extracted cleanly:", True)
    print("Target formula preferred after transition:", True)
    print("Answer leakage rejected:", True)
    print("Tautological definition rejected:", True)
    print("Valid term-identification accepted:", True)
    print("Formula question/answer compatibility checked:", True)
    print("Result: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
