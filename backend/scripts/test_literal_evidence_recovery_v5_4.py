from __future__ import annotations

import json

from app.services.quiz_service import (
    _parse_compact_slot_response,
)


def _base_item(evidence):
    return {
        "slot": "0",
        "q": (
            "Yếu tố nào cấu thành giá trị "
            "sức lao động?"
        ),
        "e": evidence,
        "c": "B",
        "o": [
            "Chỉ có tiền công danh nghĩa",
            (
                "Giá trị tư liệu sinh hoạt cần thiết "
                "và chi phí đào tạo"
            ),
            "Chỉ có chi phí đào tạo",
            "Chỉ có giá trị máy móc",
        ],
    }


def main():
    source_span = (
        "Bao gồm giá trị những tư liệu sinh hoạt "
        "cần thiết để tái sản xuất sức lao động, "
        "duy trì đời sống người công nhân và gia đình "
        "họ, cộng với chi phí đào tạo."
    )

    evidence_by_slot = {
        "0": {
            "E0": "Một câu nguồn khác.",
            "E1": source_span,
            "E2": "Một nội dung khác nữa.",
        }
    }

    # -----------------------------------------------------
    # Case 1: preferred Evidence ID.
    # -----------------------------------------------------

    by_id = _parse_compact_slot_response(
        json.dumps(
            {
                "items": [
                    _base_item(
                        "E1"
                    )
                ]
            },
            ensure_ascii=False,
        ),
        expected_slot_ids=[
            "0"
        ],
        evidence_by_slot=(
            evidence_by_slot
        ),
    )

    assert (
        by_id[
            "0"
        ][
            "evidence_quote"
        ]
        == source_span
    )

    # -----------------------------------------------------
    # Case 2: exact literal copied by Qwen.
    # This is the production failure observed in V5.3.
    # -----------------------------------------------------

    by_literal = (
        _parse_compact_slot_response(
            json.dumps(
                {
                    "items": [
                        _base_item(
                            source_span
                        )
                    ]
                },
                ensure_ascii=False,
            ),
            expected_slot_ids=[
                "0"
            ],
            evidence_by_slot=(
                evidence_by_slot
            ),
        )
    )

    assert (
        by_literal[
            "0"
        ][
            "evidence_quote"
        ]
        == source_span
    )

    # -----------------------------------------------------
    # Case 3: long exact excerpt uniquely contained in E1.
    # Backend returns full backend-owned E1, not the model
    # excerpt.
    # -----------------------------------------------------

    excerpt = (
        "giá trị những tư liệu sinh hoạt cần thiết "
        "để tái sản xuất sức lao động, duy trì đời "
        "sống người công nhân và gia đình họ"
    )

    by_excerpt = (
        _parse_compact_slot_response(
            json.dumps(
                {
                    "items": [
                        _base_item(
                            excerpt
                        )
                    ]
                },
                ensure_ascii=False,
            ),
            expected_slot_ids=[
                "0"
            ],
            evidence_by_slot=(
                evidence_by_slot
            ),
        )
    )

    assert (
        by_excerpt[
            "0"
        ][
            "evidence_quote"
        ]
        == source_span
    )

    # -----------------------------------------------------
    # Case 4: paraphrase must NOT be accepted.
    # -----------------------------------------------------

    paraphrase_failed = False

    try:
        _parse_compact_slot_response(
            json.dumps(
                {
                    "items": [
                        _base_item(
                            "Giá trị sức lao động gồm "
                            "sinh hoạt và đào tạo."
                        )
                    ]
                },
                ensure_ascii=False,
            ),
            expected_slot_ids=[
                "0"
            ],
            evidence_by_slot=(
                evidence_by_slot
            ),
        )

    except ValueError:
        paraphrase_failed = True

    assert paraphrase_failed is True

    print()
    print("=" * 72)
    print("PERFORMANCE V5.4 LITERAL EVIDENCE RECOVERY TEST")
    print("=" * 72)
    print("Evidence ID resolves:", True)
    print("Exact literal evidence recovers:", True)
    print("Unique exact excerpt recovers:", True)
    print("Returned evidence remains backend-owned:", True)
    print("Paraphrase rejected:", True)
    print("Result: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
