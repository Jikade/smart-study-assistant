from __future__ import annotations

import json

from app.services.quiz_service import (
    _evidence_units_for_context,
    _parse_compact_slot_response,
)


def main():
    legacy_evidence = (
        "3. Phương tiện cất trữ: Tiền được rút khỏi "
        "lưu thông và cất giữ lại để khi cần đem ra "
        "mua hàng, vì tiền là đại biểu cho của cải "
        "xã hội dưới hình thái giá trị."
    )

    # -----------------------------------------------------
    # Regression 1:
    # ':' must stay inside one semantic evidence unit.
    # -----------------------------------------------------

    units = (
        _evidence_units_for_context(
            legacy_evidence
        )
    )

    assert len(
        units
    ) == 1, units

    assert (
        "Phương tiện cất trữ:"
        in units[
            0
        ]
    )

    # -----------------------------------------------------
    # Regression 2:
    # Simulate an older catalog that had already split one
    # literal into consecutive evidence spans.
    # V5.5 must reconstruct backend-owned evidence safely.
    # -----------------------------------------------------

    legacy_catalog = {
        "0": {
            "E0": "3. Phương tiện cất trữ:",
            "E1": (
                "Tiền được rút khỏi lưu thông và cất giữ "
                "lại để khi cần đem ra mua hàng, vì tiền "
                "là đại biểu cho của cải xã hội dưới "
                "hình thái giá trị."
            ),
            "E2": "Một nội dung nguồn khác.",
        }
    }

    payload = {
        "items": [
            {
                "slot": "0",
                "q": (
                    "Chức năng nào của tiền tệ thể hiện "
                    "việc tiền được rút khỏi lưu thông "
                    "và cất giữ lại?"
                ),
                "e": legacy_evidence,
                "c": "B",
                "o": [
                    "Phương tiện thanh toán",
                    "Phương tiện cất trữ",
                    "Tiền tệ thế giới",
                    "Phương tiện lưu thông",
                ],
            }
        ]
    }

    parsed = (
        _parse_compact_slot_response(
            json.dumps(
                payload,
                ensure_ascii=False,
            ),
            expected_slot_ids=[
                "0"
            ],
            allow_partial=False,
            evidence_by_slot=(
                legacy_catalog
            ),
        )
    )

    recovered = (
        parsed[
            "0"
        ][
            "evidence_quote"
        ]
    )

    assert (
        "Phương tiện cất trữ:"
        in recovered
    )

    assert (
        "Tiền được rút khỏi lưu thông"
        in recovered
    )

    # -----------------------------------------------------
    # Regression 3:
    # Paraphrase remains rejected.
    # -----------------------------------------------------

    paraphrase_rejected = False

    bad_payload = {
        "items": [
            {
                "slot": "0",
                "q": "Câu hỏi?",
                "e": (
                    "Tiền được để dành nhằm sử dụng "
                    "cho việc mua sắm sau này."
                ),
                "c": "B",
                "o": [
                    "A",
                    "B",
                    "C",
                    "D",
                ],
            }
        ]
    }

    try:
        _parse_compact_slot_response(
            json.dumps(
                bad_payload,
                ensure_ascii=False,
            ),
            expected_slot_ids=[
                "0"
            ],
            allow_partial=False,
            evidence_by_slot=(
                legacy_catalog
            ),
        )

    except ValueError:
        paraphrase_rejected = True

    assert paraphrase_rejected is True

    print()
    print("=" * 72)
    print("PERFORMANCE V5.5 EVIDENCE-SPAN RECOVERY TEST")
    print("=" * 72)
    print("Colon kept inside one evidence unit:", True)
    print("Legacy multi-span literal reconstructed:", True)
    print("Recovered evidence remains backend-owned:", True)
    print("Paraphrase rejected:", True)
    print("Result: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
