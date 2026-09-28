from __future__ import annotations

from app.services.quiz_service import (
    _evidence_units_for_context,
)


def main():
    # -----------------------------------------------------
    # Case 1: numbered semantic label must remain intact.
    # -----------------------------------------------------
    numbered = (
        "3. Phương tiện cất trữ: Tiền được rút khỏi "
        "lưu thông và cất giữ lại để khi cần đem ra "
        "mua hàng, vì tiền là đại biểu cho của cải "
        "xã hội dưới hình thái giá trị."
    )

    units = _evidence_units_for_context(
        numbered
    )

    assert len(units) == 1, units
    assert units[0] == numbered, units

    # -----------------------------------------------------
    # Case 2: ordinary sentence boundary must still split.
    # -----------------------------------------------------
    normal = (
        "Hàng hóa có giá trị sử dụng. "
        "Hàng hóa cũng có giá trị."
    )

    normal_units = (
        _evidence_units_for_context(
            normal
        )
    )

    assert len(normal_units) == 2, normal_units

    # -----------------------------------------------------
    # Case 3: semicolon and colon stay inside one semantic
    # statement instead of creating tiny fragments.
    # -----------------------------------------------------
    punctuation = (
        "Đặc điểm: nội dung thứ nhất; nội dung thứ hai."
    )

    punctuation_units = (
        _evidence_units_for_context(
            punctuation
        )
    )

    assert len(
        punctuation_units
    ) == 1, punctuation_units

    # -----------------------------------------------------
    # Case 4: numbered list followed by another real
    # sentence still splits only at the real sentence end.
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

    assert (
        mixed_units[0].startswith(
            "1. Tiền là hàng hóa đặc biệt:"
        )
    )

    print()
    print("=" * 72)
    print("PERFORMANCE V5.6 NUMBERED EVIDENCE SPLIT TEST")
    print("=" * 72)
    print("Numbered label preserved:", True)
    print("Colon preserved:", True)
    print("Semicolon preserved:", True)
    print("Normal sentence splitting preserved:", True)
    print("Result: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
