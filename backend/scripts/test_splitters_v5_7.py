from __future__ import annotations

from app.services.quiz_service import (
    _evidence_units_for_context,
    _micro_context_units,
)


def main():
    numbered = (
        "3. Phương tiện cất trữ: Tiền được rút khỏi "
        "lưu thông và cất giữ lại để khi cần đem ra "
        "mua hàng, vì tiền là đại biểu cho của cải "
        "xã hội dưới hình thái giá trị."
    )

    # -----------------------------------------------------
    # Evidence splitter
    # -----------------------------------------------------

    evidence_units = (
        _evidence_units_for_context(
            numbered
        )
    )

    assert evidence_units == [
        numbered
    ], evidence_units

    # -----------------------------------------------------
    # Micro-context splitter:
    # force an oversized paragraph so sentence splitting
    # path is actually exercised.
    # -----------------------------------------------------

    numbered_long = (
        numbered
        + " "
        + (
            "Nội dung bổ sung giúp đoạn văn vượt giới hạn "
            "micro-context nhưng vẫn phải giữ nguyên nhãn "
            "đánh số ở đầu câu. "
            * 8
        )
    )

    micro_units = (
        _micro_context_units(
            numbered_long
        )
    )

    assert micro_units, micro_units

    assert not any(
        unit.strip() == "3."
        for unit
        in micro_units
    ), micro_units

    assert any(
        unit.startswith(
            "3. Phương tiện cất trữ:"
        )
        for unit
        in micro_units
    ), micro_units

    # -----------------------------------------------------
    # Ordinary sentence boundaries still work.
    # -----------------------------------------------------

    normal = (
        "Hàng hóa có giá trị sử dụng. "
        "Hàng hóa cũng có giá trị."
    )

    normal_evidence = (
        _evidence_units_for_context(
            normal
        )
    )

    assert len(
        normal_evidence
    ) == 2, normal_evidence

    # -----------------------------------------------------
    # Colon + semicolon remain internal punctuation.
    # -----------------------------------------------------

    punctuation = (
        "Đặc điểm: nội dung thứ nhất; nội dung thứ hai."
    )

    punctuation_units = (
        _evidence_units_for_context(
            punctuation
        )
    )

    assert punctuation_units == [
        punctuation
    ], punctuation_units

    # -----------------------------------------------------
    # A numbered sentence followed by a normal sentence.
    # -----------------------------------------------------

    mixed = (
        "1. Tiền là hàng hóa đặc biệt: nó đóng vai trò "
        "vật ngang giá chung. "
        "Nó thực hiện nhiều chức năng."
    )

    mixed_units = (
        _evidence_units_for_context(
            mixed
        )
    )

    assert len(
        mixed_units
    ) == 2, mixed_units

    assert mixed_units[0].startswith(
        "1. Tiền là hàng hóa đặc biệt:"
    )

    print()
    print("=" * 72)
    print("PERFORMANCE V5.7 SHARED SPLITTER REGRESSION TEST")
    print("=" * 72)
    print("Evidence numbered label preserved:", True)
    print("Micro-context numbered label preserved:", True)
    print("Colon preserved:", True)
    print("Semicolon preserved:", True)
    print("Normal sentence splitting preserved:", True)
    print("Result: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
