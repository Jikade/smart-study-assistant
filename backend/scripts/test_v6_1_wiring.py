
from __future__ import annotations

import inspect

from app.services import quiz_service


def main():
    source = inspect.getsource(
        quiz_service._generate_compact_slot_questions
    )

    preselect_start = source.index(
        "fixed_choice_by_slot = ("
    )

    retry_start = source.index(
        "    retry_context = (",
        preselect_start,
    )

    preselect_block = source[
        preselect_start:
        retry_start
    ]

    parser_start = source.index(
        "_parse_compact_slot_response("
    )

    parser_block = source[
        parser_start:
    ]

    assert (
        "fixed_choice_by_slot=("
        not in preselect_block
    )

    assert (
        "fixed_choice_by_slot=("
        in parser_block
    )

    print()
    print("=" * 72)
    print("PERFORMANCE V6.1.1 WIRING TEST")
    print("=" * 72)
    print("Preselection variable assigned first:", True)
    print("No self-reference during preselection:", True)
    print("Parser receives fixed choices:", True)
    print("Result: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
