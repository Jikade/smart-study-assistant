
from __future__ import annotations

import json

from app.services.quiz_service import (
    _parse_compact_slot_response,
    _recover_compact_items_from_malformed_json,
)


def main():
    evidence_by_slot = {
        "0": {
            "E0": (
                "Tiền được rút khỏi lưu thông "
                "và cất giữ lại."
            ),
        },
        "1": {
            "E0": (
                "Tự do cạnh tranh đẻ ra "
                "tập trung sản xuất."
            ),
        },
        "2": {
            "E0": (
                "Giá cả sản xuất bằng chi phí "
                "sản xuất cộng lợi nhuận bình quân."
            ),
        },
    }

    malformed = '''
{
  "items": [
    {
      "slot": "0",
      "q": "Tiền được cất giữ là chức năng gì?",
      "e": "E0",
      "c": "B",
      "o": ["Thanh toán","Cất trữ","Thế giới","Lưu thông"]
    }
    {
      "slot": "1",
      "q": "Tự do cạnh tranh tạo ra điều gì?",
      "e": "E0",
      "c": "A",
      "o": ["Tập trung sản xuất","Tiêu dùng","Thuế","Tiền công"]
    }
    {
      "slot": "2",
      "q": "Giá cả sản xuất gồm những gì?",
      "e": "E0",
      "c": "C",
      "o": ["Tiền công","Thuế","Chi phí sản xuất + lợi nhuận bình quân","Giá trị sử dụng"]
    }
  ]
}
'''

    salvaged = (
        _recover_compact_items_from_malformed_json(
            malformed
        )
    )

    assert len(
        salvaged[
            "items"
        ]
    ) == 3

    parsed = (
        _parse_compact_slot_response(
            malformed,
            expected_slot_ids=[
                "0",
                "1",
                "2",
            ],
            allow_partial=False,
            evidence_by_slot=(
                evidence_by_slot
            ),
        )
    )

    assert set(
        parsed.keys()
    ) == {
        "0",
        "1",
        "2",
    }

    assert (
        parsed[
            "0"
        ][
            "evidence_quote"
        ]
        == evidence_by_slot[
            "0"
        ][
            "E0"
        ]
    )

    valid_payload = {
        "items": [
            {
                "slot": "0",
                "q": "Câu hỏi?",
                "e": "E0",
                "c": "A",
                "o": [
                    "A",
                    "B",
                    "C",
                    "D",
                ],
            }
        ]
    }

    valid = (
        _parse_compact_slot_response(
            json.dumps(
                valid_payload,
                ensure_ascii=False,
            ),
            expected_slot_ids=[
                "0"
            ],
            evidence_by_slot={
                "0": {
                    "E0": "Nguồn thử nghiệm."
                }
            },
        )
    )

    assert set(
        valid.keys()
    ) == {
        "0"
    }

    print()
    print("=" * 72)
    print("PERFORMANCE V5.8 ROBUST COMPACT JSON TEST")
    print("=" * 72)
    print("Missing inter-item commas recovered:", True)
    print("All three items preserved:", True)
    print("Evidence IDs still backend-resolved:", True)
    print("Valid JSON path preserved:", True)
    print("Result: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
