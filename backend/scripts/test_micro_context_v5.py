from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DocumentChunk
from app.db.session import engine
from app.services.quiz_service import (
    MICRO_CONTEXT_MAX_CHARS,
    _apply_micro_contexts_to_slots,
    _boundary_safe_source_text,
    _micro_context_candidates,
)


def main():
    with Session(engine) as db:
        chunk_413 = db.scalar(
            select(DocumentChunk).where(
                DocumentChunk.id == 413
            )
        )

        if chunk_413 is None:
            raise RuntimeError(
                "Document chunk 413 not found."
            )

        original = (
            chunk_413.content
            or ""
        ).strip()

        safe_text, boundary_meta = (
            _boundary_safe_source_text(
                original
            )
        )

        # -------------------------------------------------
        # Boundary regression:
        # chunk 413 is known to contain the beginning of
        # CHƯƠNG 5 even though section_id=4.
        # -------------------------------------------------

        assert (
            boundary_meta[
                "boundary_cut"
            ]
            is True
        ), (
            "Expected chunk 413 to trigger "
            "a high-level boundary cut."
        )

        assert (
            "CHƯƠNG 5"
            not in safe_text.upper()
        ), (
            "Boundary-safe text must exclude "
            "the CHƯƠNG 5 cross-section tail."
        )

        assert (
            "độc quyền"
            in safe_text.casefold()
        ), (
            "Boundary cut removed valid section-4 "
            "content before CHƯƠNG 5."
        )

        assert (
            len(
                safe_text
            )
            < len(
                original
            )
        )

        # -------------------------------------------------
        # Candidate generation.
        # -------------------------------------------------

        candidates = (
            _micro_context_candidates(
                safe_text
            )
        )

        assert candidates, (
            "Micro-context selector returned "
            "no candidates."
        )

        for candidate in candidates:
            assert (
                len(
                    candidate[
                        "text"
                    ]
                )
                <= MICRO_CONTEXT_MAX_CHARS
            )

            assert (
                "CHƯƠNG 5"
                not in candidate[
                    "text"
                ].upper()
            )

        # -------------------------------------------------
        # Slot assignment.
        # -------------------------------------------------

        slot_specs = [
            {
                "id": "0",
                "source_chunk": (
                    chunk_413
                ),
                "source_text": (
                    original
                ),
            },
            {
                "id": "1",
                "source_chunk": (
                    chunk_413
                ),
                "source_text": (
                    original
                ),
            },
        ]

        selected, metrics = (
            _apply_micro_contexts_to_slots(
                slot_specs
            )
        )

        assert len(
            selected
        ) == 2

        assert (
            metrics[
                "boundary_cuts"
            ]
            == 1
        )

        assert (
            metrics[
                "micro_chars"
            ]
            < metrics[
                "original_chars"
            ]
        )

        for item in selected:
            context = item[
                "source_text"
            ]

            assert (
                len(
                    context
                )
                <= MICRO_CONTEXT_MAX_CHARS
            )

            assert (
                "CHƯƠNG 5"
                not in context.upper()
            )

        print()
        print("=" * 72)
        print("PERFORMANCE V5 MICRO-CONTEXT REGRESSION TEST")
        print("=" * 72)
        print("Chunk:", chunk_413.id)
        print("Section:", chunk_413.section_id)
        print(
            "Original chars:",
            metrics[
                "original_chars"
            ],
        )
        print(
            "Boundary-safe chars:",
            metrics[
                "safe_chars"
            ],
        )
        print(
            "Micro-context prompt chars:",
            metrics[
                "micro_chars"
            ],
        )
        print(
            "Compression:",
            f"{metrics['compression_pct']}%",
        )
        print(
            "Boundary cuts:",
            metrics[
                "boundary_cuts"
            ],
        )
        print(
            "Selected context lengths:",
            [
                len(
                    item[
                        "source_text"
                    ]
                )
                for item
                in selected
            ],
        )
        print(
            "Chapter 5 excluded:",
            True,
        )
        print("Result: PASS")
        print("=" * 72)


if __name__ == "__main__":
    main()
