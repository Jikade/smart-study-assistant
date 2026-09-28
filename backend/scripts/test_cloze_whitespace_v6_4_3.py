
from __future__ import annotations

from types import SimpleNamespace

from app.services.quiz_service import (
    _compact_cloze_context,
    _deterministic_cloze_repair,
    _mask_answer_in_evidence,
)


def make_question():
    return SimpleNamespace(
        question_text="Công thức tính W là gì?",
        options=[
            SimpleNamespace(
                option_key="A",
                option_text="W = k + m",
                is_correct=True,
            ),
            SimpleNamespace(
                option_key="B",
                option_text="W = k + v",
                is_correct=False,
            ),
            SimpleNamespace(
                option_key="C",
                option_text="W = c + m",
                is_correct=False,
            ),
            SimpleNamespace(
                option_key="D",
                option_text="W = k - m",
                is_correct=False,
            ),
        ],
    )


def main():
    evidence = (
        "Khi đó, công thức W = c + v + m "
        "chuyển thành W = k + m."
    )

    masked = _mask_answer_in_evidence(
        evidence_text=evidence,
        answer_text="W = k + m",
    )

    assert masked == (
        "Khi đó, công thức W = c + v + m "
        "chuyển thành _____."
    ), repr(masked)

    compact = _compact_cloze_context(
        masked
    )

    assert compact == (
        "Khi đó, công thức W = c + v + m "
        "chuyển thành _____."
    ), repr(compact)

    repaired = _deterministic_cloze_repair(
        make_question(),
        evidence_quote=evidence,
    )

    assert repaired is not None

    expected = (
        "Điền công thức thích hợp vào chỗ trống: "
        "Khi đó, công thức W = c + v + m "
        "chuyển thành _____."
    )

    assert (
        repaired.question_text
        == expected
    ), repr(repaired.question_text)

    assert "Khiđó" not in repaired.question_text
    assert "Giá trịthặng dư" not in repaired.question_text

    print()
    print("=" * 72)
    print("V6.4.3 CLOZE WHITESPACE REGRESSION")
    print("=" * 72)
    print("Masked:", repr(masked))
    print("Compact:", repr(compact))
    print("Repaired:", repr(repaired.question_text))
    print("Whitespace preserved:", True)
    print("Result: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
