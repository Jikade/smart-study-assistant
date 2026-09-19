from __future__ import annotations

import json

from app.services.quiz_service import (
    _parse_compact_slot_response,
)


def main():
    partial_payload = {
        "items": [
            {
                "slot": "0",
                "q": "Câu hỏi thử nghiệm?",
                "e": "Đây là bằng chứng thử nghiệm trực tiếp.",
                "c": "B",
                "o": [
                    "Sai A",
                    "Đây là bằng chứng",
                    "Sai C",
                    "Sai D",
                ],
            }
        ]
    }

    content = json.dumps(
        partial_payload,
        ensure_ascii=False,
    )

    # Fast-retry mode: recover the returned slot.
    partial = (
        _parse_compact_slot_response(
            content,
            expected_slot_ids=[
                "0",
                "1",
            ],
            allow_partial=True,
        )
    )

    assert set(
        partial.keys()
    ) == {
        "0"
    }

    # Initial-generation mode must remain strict.
    strict_failed = False

    try:
        _parse_compact_slot_response(
            content,
            expected_slot_ids=[
                "0",
                "1",
            ],
            allow_partial=False,
        )

    except ValueError:
        strict_failed = True

    assert strict_failed is True

    print()
    print("=" * 72)
    print("PERFORMANCE V5.1 PARTIAL RETRY TEST")
    print("=" * 72)
    print("Requested slots:", ["0", "1"])
    print("Returned slots:", sorted(partial.keys()))
    print("Partial recovery accepted:", True)
    print("Initial-generation strict mode preserved:", True)
    print("Result: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
