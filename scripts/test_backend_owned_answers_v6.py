
from __future__ import annotations

import json
from types import SimpleNamespace

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DocumentChunk
from app.db.session import engine
from app.services.quiz_service import (
    _build_compact_source_catalog,
    _fast_grounding_check,
    _generate_compact_slot_questions,
    _normalize_compare_text,
    _preselect_backend_choices,
    _prepare_question_local,
)


class FakeV6Provider:
    can_chat = True

    def __init__(
        self,
        items,
    ):
        self.items = items
        self.calls = 0

    def chat(
        self,
        messages,
        **kwargs,
    ):
        self.calls += 1

        return SimpleNamespace(
            content=json.dumps(
                {
                    "items": (
                        self.items
                    )
                },
                ensure_ascii=False,
            ),
            model="fake-v6",
        )


def main():
    with Session(engine) as db:
        chunk = db.scalar(
            select(DocumentChunk).where(
                DocumentChunk.id == 410
            )
        )

        if chunk is None:
            raise RuntimeError(
                "Document chunk 410 not found."
            )

        source_text = (
            chunk.content
            or ""
        )[:1600].strip()

        specs = [
            {
                "id": "0",
                "source_chunk": chunk,
                "source_text": source_text,
            },
            {
                "id": "1",
                "source_chunk": chunk,
                "source_text": source_text,
            },
        ]

        (
            _sources,
            slots,
            evidence_by_slot,
            answer_by_slot,
        ) = _build_compact_source_catalog(
            specs
        )

        preselected = (
            _preselect_backend_choices(
                slots=slots,
                evidence_by_slot=(
                    evidence_by_slot
                ),
                answer_by_slot=(
                    answer_by_slot
                ),
            )
        )

        fake_items = []
        expected_answer_texts = {}

        # Deliberately use DIFFERENT direct-fact questions
        # so this regression tests V6 correctness ownership,
        # not the duplicate-question guard.
        question_templates = {
            "0": (
                "Theo nguồn, khái niệm nào "
                "được nêu ở nội dung này?"
            ),
            "1": (
                "Theo nguồn, nội dung trực tiếp "
                "nào được đề cập?"
            ),
        }

        for slot in slots:
            slot_id = str(
                slot[
                    "slot"
                ]
            )

            chosen_choice = (
                preselected[
                    slot_id
                ]
            )

            expected_answer_texts[
                slot_id
            ] = (
                chosen_choice[
                    "answer_text"
                ]
            )

            chosen = {
                "id": (
                    chosen_choice[
                        "answer_id"
                    ]
                ),
                "e": (
                    chosen_choice[
                        "evidence_id"
                    ]
                ),
                "text": (
                    chosen_choice[
                        "answer_text"
                    ]
                ),
            }

            fake_items.append(
                {
                    "slot": (
                        slot_id
                    ),
                    "q": (
                        question_templates[
                            slot_id
                        ]
                    ),
                    "e": (
                        chosen[
                            "e"
                        ]
                    ),
                    "a": (
                        chosen[
                            "id"
                        ]
                    ),
                    "d": [
                        (
                            "Nội dung giả định thứ nhất "
                            + slot_id
                        ),
                        (
                            "Nội dung giả định thứ hai "
                            + slot_id
                        ),
                        (
                            "Nội dung giả định thứ ba "
                            + slot_id
                        ),
                    ],

                    # Deliberately malicious / legacy:
                    # V6 must ignore model-selected
                    # correctness and old four-option output.
                    "c": "D",
                    "o": [
                        "Sai 1",
                        "Sai 2",
                        "Sai 3",
                        "Sai 4",
                    ],
                }
            )

        provider = FakeV6Provider(
            fake_items
        )

        (
            raw_by_slot,
            model,
            _duration_ms,
        ) = _generate_compact_slot_questions(
            provider,
            slot_specs=specs,
            difficulty="MEDIUM",
        )

        assert provider.calls == 1
        assert model == "fake-v6"

        seen = set()
        observed_correct_keys = []

        for slot_id in [
            "0",
            "1",
        ]:
            raw = (
                raw_by_slot[
                    slot_id
                ]
            )

            question = (
                _prepare_question_local(
                    source_chunk=chunk,
                    raw_question=raw,
                    difficulty="MEDIUM",
                    used_question_texts=set(),
                    batch_seen_texts=seen,
                )
            )

            correct_options = [
                option
                for option
                in question.options
                if option.is_correct
            ]

            assert len(
                correct_options
            ) == 1

            correct = (
                correct_options[
                    0
                ]
            )

            observed_correct_keys.append(
                correct.option_key
            )

            # Core V6 requirement:
            # correct text is backend-owned, not model-owned.
            assert (
                correct.option_text
                == expected_answer_texts[
                    slot_id
                ]
            )

            # Malicious c="D" from the fake model must not
            # override backend correctness.
            if slot_id == "0":
                assert (
                    correct.option_key
                    != "D"
                )

            ok, reason, verification = (
                _fast_grounding_check(
                    source_text=source_text,
                    question=question,
                    evidence_quote=(
                        raw[
                            "evidence_quote"
                        ]
                    ),
                )
            )

            assert ok is True, reason

            assert (
                verification[
                    "verified_correct_key"
                ]
                == correct.option_key
            )

        # Backend deterministic placement:
        # slot 0 -> A
        # slot 1 -> B
        assert observed_correct_keys == [
            "A",
            "B",
        ]

        # -------------------------------------------------
        # Separate check: duplicate guard is still active.
        # This proves the previous failure was expected
        # behavior rather than a service bug.
        # -------------------------------------------------
        duplicate_guard_triggered = False

        duplicate_raw = dict(
            raw_by_slot[
                "0"
            ]
        )

        try:
            _prepare_question_local(
                source_chunk=chunk,
                raw_question=duplicate_raw,
                difficulty="MEDIUM",
                used_question_texts=set(),
                batch_seen_texts={
                    _normalize_compare_text(
                        question_templates[
                            "0"
                        ]
                    )
                },
            )

        except ValueError as exc:
            duplicate_guard_triggered = (
                "Duplicate question"
                in str(
                    exc
                )
            )

        assert (
            duplicate_guard_triggered
            is True
        )

        print()
        print("=" * 72)
        print("PERFORMANCE V6 BACKEND-OWNED ANSWER TEST")
        print("=" * 72)
        print("AI calls:", provider.calls)
        print("Backend answer candidates:", True)
        print("V6.1 preselection respected:", True)
        print("Model cannot choose correct A/B/C/D:", True)
        print(
            "Observed backend correct keys:",
            observed_correct_keys,
        )
        print(
            "Correct answers are exact evidence phrases:",
            True,
        )
        print("Fast Gate passes:", 2)
        print(
            "Duplicate-question guard preserved:",
            True,
        )
        print("Result: PASS")
        print("=" * 72)


if __name__ == "__main__":
    main()
