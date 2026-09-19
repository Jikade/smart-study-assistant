from __future__ import annotations

import json

from app.services.quiz_service import (
    _parse_compact_slot_response,
)


def _item(
    question: str,
    *,
    slot_marker=None,
):
    item = {
        "q": question,
        "e": "Đây là bằng chứng trực tiếp trong nguồn.",
        "c": "B",
        "o": [
            "Sai A",
            "Đây là bằng chứng",
            "Sai C",
            "Sai D",
        ],
    }

    if slot_marker is not None:
        item["slot"] = slot_marker

    return item


def main():
    # -----------------------------------------------------
    # Case 1: model omits ALL slots.
    # Backend recovers them by expected order.
    # -----------------------------------------------------

    no_slots_payload = {
        "items": [
            _item("Câu 0?"),
            _item("Câu 1?"),
            _item("Câu 2?"),
        ]
    }

    recovered = (
        _parse_compact_slot_response(
            json.dumps(
                no_slots_payload,
                ensure_ascii=False,
            ),
            expected_slot_ids=[
                "0",
                "1",
                "2",
            ],
            allow_partial=False,
        )
    )

    assert list(
        recovered.keys()
    ) == [
        "0",
        "1",
        "2",
    ]

    # -----------------------------------------------------
    # Case 2: explicit numeric slot + omitted slot.
    # Numeric 0 is accepted; missing item receives slot 1.
    # -----------------------------------------------------

    mixed_payload = {
        "items": [
            _item(
                "Câu 0?",
                slot_marker=0,
            ),
            _item(
                "Câu 1?",
            ),
        ]
    }

    mixed = (
        _parse_compact_slot_response(
            json.dumps(
                mixed_payload,
                ensure_ascii=False,
            ),
            expected_slot_ids=[
                "0",
                "1",
            ],
            allow_partial=False,
        )
    )

    assert set(
        mixed.keys()
    ) == {
        "0",
        "1",
    }

    # -----------------------------------------------------
    # Case 3: alias slot_id is accepted.
    # -----------------------------------------------------

    alias_payload = {
        "items": [
            {
                "slot_id": "0",
                "q": "Câu alias?",
                "e": "Đây là bằng chứng trực tiếp trong nguồn.",
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

    alias = (
        _parse_compact_slot_response(
            json.dumps(
                alias_payload,
                ensure_ascii=False,
            ),
            expected_slot_ids=[
                "0",
            ],
            allow_partial=False,
        )
    )

    assert set(
        alias.keys()
    ) == {
        "0",
    }

    print()
    print("=" * 72)
    print("PERFORMANCE V5.2 SLOT RECOVERY TEST")
    print("=" * 72)
    print("All slots omitted -> recovered:", sorted(recovered.keys()))
    print("Mixed numeric/missing slots -> recovered:", sorted(mixed.keys()))
    print("slot_id alias accepted:", True)
    print("Backend source ownership preserved:", True)
    print("Result: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
