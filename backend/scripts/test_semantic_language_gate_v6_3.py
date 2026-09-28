
from __future__ import annotations

from types import SimpleNamespace

from app.services.quiz_service import (
    _answer_candidate_intrinsic_issue,
    _question_answer_fit_issue,
    _text_language_hint,
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
    # 1) Language detector
    # -----------------------------------------------------

    assert (
        _text_language_hint(
            "Giá trị thặng dư được tạo ra trong sản xuất."
        )
        == "VI"
    )

    assert (
        _text_language_hint(
            "What is the correct formula after substitution?"
        )
        == "EN"
    )

    # -----------------------------------------------------
    # 2) Quiz 16 Q1:
    # role question + bare nominal answer must fail.
    # -----------------------------------------------------

    q1 = make_question(
        "Tư liệu sinh hoạt có vai trò gì trong sản xuất?",
        "Giá trị",
        [
            "Tăng năng suất lao động",
            "Đảm bảo an ninh quốc gia",
            "Phát triển công nghệ",
        ],
    )

    issue1 = _question_answer_fit_issue(
        q1,
        evidence_quote=(
            "Giá trị hàng hóa được biểu hiện trong "
            "quá trình sản xuất."
        ),
    )

    assert issue1 is not None
    assert (
        "role/function"
        in issue1
    ), issue1

    # -----------------------------------------------------
    # 3) Quiz 16 Q2:
    # English stem on Vietnamese evidence must fail.
    # -----------------------------------------------------

    q2 = make_question(
        "What is the correct formula after substitution?",
        "W = k + m",
        [
            "W = k + v",
            "W = c + m",
            "W = v + m",
        ],
    )

    issue2 = _question_answer_fit_issue(
        q2,
        evidence_quote=(
            "Công thức W = c + v + m chuyển thành "
            "W = k + m."
        ),
    )

    assert issue2 is not None
    assert (
        "language"
        in issue2
    ), issue2

    # -----------------------------------------------------
    # 4) Quiz 16 Q3:
    # "Khi đó" is intrinsically invalid.
    # -----------------------------------------------------

    issue3 = (
        _answer_candidate_intrinsic_issue(
            "Khi đó"
        )
    )

    assert issue3 is not None

    q3 = make_question(
        "Khi nào hàng hóa được bán theo giá cả sản xuất?",
        "Khi đó",
        [
            "Khi thị trường ổn định",
            "Khi giá cả tăng",
            "Khi sản phẩm mới ra mắt",
        ],
    )

    fit3 = _question_answer_fit_issue(
        q3,
        evidence_quote=(
            "Khi tỷ suất lợi nhuận bình quân được hình thành, "
            "hàng hóa được bán theo giá cả sản xuất."
        ),
    )

    assert fit3 is not None

    # -----------------------------------------------------
    # 5) Good Vietnamese formula question passes.
    # -----------------------------------------------------

    good_formula = make_question(
        "Sau khi chuyển đổi, công thức W được viết như thế nào?",
        "W = k + m",
        [
            "W = k + v",
            "W = c + m",
            "W = v + m",
        ],
    )

    assert (
        _question_answer_fit_issue(
            good_formula,
            evidence_quote=(
                "Công thức W = c + v + m chuyển thành "
                "W = k + m."
            ),
        )
        is None
    )

    # -----------------------------------------------------
    # 6) Good term-identification question passes.
    # -----------------------------------------------------

    good_term = make_question(
        (
            "Hình thức cạnh tranh nào diễn ra giữa "
            "các chủ thể thuộc những ngành khác nhau?"
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
            good_term,
            evidence_quote=(
                "Cạnh tranh giữa các ngành là cạnh tranh "
                "giữa các chủ thể thuộc những ngành "
                "sản xuất khác nhau."
            ),
        )
        is None
    )

    print()
    print("=" * 72)
    print("PERFORMANCE V6.3 SEMANTIC + LANGUAGE FIT TEST")
    print("=" * 72)
    print("Vietnamese/English language hint:", True)
    print("Role-question mismatch rejected:", True)
    print("Cross-language question rejected:", True)
    print("Deictic answer fragment rejected:", True)
    print("Valid Vietnamese formula accepted:", True)
    print("Valid term-identification accepted:", True)
    print("Result: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
