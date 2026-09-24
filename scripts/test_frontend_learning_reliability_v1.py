from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIEWS = ROOT / "src" / "views.js"


def must(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"[PASS] {label}")


def main() -> None:
    text = VIEWS.read_text(encoding="utf-8")

    print()
    print("=" * 92)
    print("FRONTEND LEARNING RELIABILITY V1 REGRESSION")
    print("=" * 92)

    must(
        "Frontend reliability marker exists",
        "SSA-FE-LR-V1" in text,
    )
    must(
        "Analytics uses Promise.allSettled",
        "masteryResult,weakResult,recsResult,planResult" in text
        and "Promise.allSettled" in text,
    )
    must(
        "Flashcards uses independent due/deck settlement",
        "decksResult,dueResult" in text,
    )
    must(
        "Old mastery_score * 100 rendering is removed",
        "t.mastery_score*100" not in text
        and "x.mastery_score*100" not in text,
    )
    must(
        "Mastery bar uses a direct 0..100 score",
        'style="width:${score}%"' in text,
    )
    must(
        "Weak-topic percent uses direct mastery_score",
        "Number(x.mastery_score||0)" in text,
    )
    must(
        "Flashcard due failure has graceful UI fallback",
        "Danh sách deck vẫn được hiển thị" in text,
    )

    print("-" * 92)
    print("RESULT: PASS")
    print("=" * 92)


if __name__ == "__main__":
    main()
