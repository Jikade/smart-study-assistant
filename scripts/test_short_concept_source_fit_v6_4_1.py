
from __future__ import annotations

from app.services.quiz_service import (
    _answer_candidate_source_fit_issue,
)


def main():
    # "Giá trị" is TWO lexical tokens: Giá + trị.
    weak = (
        _answer_candidate_source_fit_issue(
            answer_text="Giá trị",
            evidence_text=(
                "• Giá trị của hàng hóa biểu hiện "
                "một nội dung kinh tế nhất định."
            ),
        )
    )

    assert weak is not None, weak

    # Two-token concept is valid when explicitly defined.
    defined_two_tokens = (
        _answer_candidate_source_fit_issue(
            answer_text="Tiền tệ",
            evidence_text=(
                "Tiền tệ là một hàng hóa đặc biệt "
                "đóng vai trò vật ngang giá chung."
            ),
        )
    )

    assert defined_two_tokens is None, defined_two_tokens

    # One-token explicit definition remains valid.
    defined_one_token = (
        _answer_candidate_source_fit_issue(
            answer_text="Tiền",
            evidence_text=(
                "Tiền là hàng hóa đặc biệt được "
                "tách ra làm vật ngang giá chung."
            ),
        )
    )

    assert defined_one_token is None, defined_one_token

    # Longer grounded concepts are not blocked merely
    # because they are not written as definitions.
    longer = (
        _answer_candidate_source_fit_issue(
            answer_text="Tỷ suất lợi nhuận bình quân",
            evidence_text=(
                "Sự hình thành tỷ suất lợi nhuận bình quân "
                "làm biến đổi giá trị hàng hóa."
            ),
        )
    )

    assert longer is None, longer

    print()
    print("=" * 72)
    print("PERFORMANCE V6.4.1 SHORT-CONCEPT SOURCE-FIT TEST")
    print("=" * 72)
    print("'Giá trị' weak short concept rejected:", True)
    print("'Tiền tệ' explicit definition preserved:", True)
    print("'Tiền' explicit definition preserved:", True)
    print("Longer grounded concept unaffected:", True)
    print("Result: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
