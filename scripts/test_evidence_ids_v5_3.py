from __future__ import annotations

import json

from app.services.quiz_service import (
    _consume_retry_budget,
    _parse_compact_slot_response,
)


def main():
    evidence_by_slot = {
        "0": {
            "E0": (
                "Theo Lênin, tự do cạnh tranh đẻ ra "
                "tập trung sản xuất."
            ),
            "E1": (
                "Tập trung sản xuất phát triển đến "
                "một mức độ nhất định sẽ dẫn tới độc quyền."
            ),
        },
        "1": {
            "E0": (
                "Giá cả sản xuất = Chi phí sản xuất "
                "+ Lợi nhuận bình quân."
            ),
        },
    }

    payload = {
        "items": [
            {
                "slot": "0",
                "q": (
                    "Điều gì sẽ dẫn tới độc quyền?"
                ),
                "e": "E1",
                "c": "B",
                "o": [
                    "Lưu thông hàng hóa",
                    "Tập trung sản xuất phát triển "
                    "đến một mức độ nhất định",
                    "Tiêu dùng cá nhân",
                    "Phân phối thu nhập",
                ],
            },
            {
                # Deliberately omit slot to verify the
                # existing backend positional recovery.
                "q": (
                    "Giá cả sản xuất được xác định "
                    "theo công thức nào?"
                ),
                "e": "E0",
                "c": "A",
                "o": [
                    "Chi phí sản xuất + Lợi nhuận bình quân",
                    "Chi phí sản xuất - Lợi nhuận bình quân",
                    "Tiền công + Thuế",
                    "Giá trị sử dụng + Tiền công",
                ],
            },
        ]
    }

    parsed = (
        _parse_compact_slot_response(
            json.dumps(
                payload,
                ensure_ascii=False,
            ),
            expected_slot_ids=[
                "0",
                "1",
            ],
            allow_partial=False,
            evidence_by_slot=(
                evidence_by_slot
            ),
        )
    )

    assert (
        parsed["0"]["evidence_quote"]
        == evidence_by_slot["0"]["E1"]
    )

    assert (
        parsed["1"]["evidence_quote"]
        == evidence_by_slot["1"]["E0"]
    )

    # Critical V5.3 budget regression:
    # request 3 retry slots, model returns only 1.
    # Two retry credits must remain for the two missing slots.
    remaining = _consume_retry_budget(
        3,
        1,
    )

    assert remaining == 2

    print()
    print("=" * 72)
    print("PERFORMANCE V5.3 EVIDENCE-ID + RETRY-BUDGET TEST")
    print("=" * 72)
    print("Evidence ID E1 resolved to exact source:", True)
    print("Missing slot positional recovery preserved:", True)
    print("Retry budget: 3 - 1 returned =", remaining)
    print("Two missing slots retain recovery budget:", True)
    print("Result: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
