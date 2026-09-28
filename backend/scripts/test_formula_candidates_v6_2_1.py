
from __future__ import annotations

from app.services.quiz_service import (
    _answer_candidates_for_evidence,
    _score_backend_answer_candidate,
)


def main():
    source = (
        "W = c + v + m chuyển thành W = k + m."
    )

    candidates = (
        _answer_candidates_for_evidence(
            source
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

    assert (
        "W = k + m."
        not in candidates
    ), candidates

    assert not any(
        "chuyển thành"
        in candidate.casefold()
        and "=" in candidate
        for candidate
        in candidates
    ), candidates

    source_score = (
        _score_backend_answer_candidate(
            answer_text="W = c + v + m",
            evidence_text=source,
        )
    )

    target_score = (
        _score_backend_answer_candidate(
            answer_text="W = k + m",
            evidence_text=source,
        )
    )

    assert (
        target_score > source_score
    ), (
        source_score,
        target_score,
    )

    print()
    print("=" * 72)
    print("PERFORMANCE V6.2.1 FORMULA CANDIDATE TEST")
    print("=" * 72)
    print("Source formula extracted cleanly:", True)
    print("Target formula extracted cleanly:", True)
    print("Terminal period removed:", True)
    print("Mixed transition clause rejected:", True)
    print("Target formula ranked above source formula:", True)
    print("Candidates:", candidates)
    print("Result: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
