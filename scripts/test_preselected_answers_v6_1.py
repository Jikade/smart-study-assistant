
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
    _preselect_backend_choices,
    _prepare_question_local,
)


class FakePreselectedProvider:
    can_chat = True

    def __init__(self):
        self.calls = 0
        self.last_prompt = ""

    def chat(
        self,
        messages,
        **kwargs,
    ):
        self.calls += 1
        self.last_prompt = (
            messages[-1][
                "content"
            ]
        )

        # The fake model returns ONLY q+d.
        # No evidence ID, answer ID, correct key,
        # or correct option text is supplied by the model.
        payload = {
            "items": [
                {
                    "slot": "0",
                    "q": (
                        "Theo nguồn, khái niệm nào "
                        "được nêu trực tiếp?"
                    ),
                    "d": [
                        "Nhiễu alpha",
                        "Nhiễu beta",
                        "Nhiễu gamma",
                    ],
                },
                {
                    "slot": "1",
                    "q": (
                        "Theo nguồn, nội dung nào "
                        "được xác định trực tiếp?"
                    ),
                    "d": [
                        "Nhiễu delta",
                        "Nhiễu epsilon",
                        "Nhiễu zeta",
                    ],
                },
            ]
        }

        return SimpleNamespace(
            content=json.dumps(
                payload,
                ensure_ascii=False,
            ),
            model="fake-v6.1",
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

        choices = (
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

        assert set(
            choices.keys()
        ) == {
            "0",
            "1",
        }

        provider = (
            FakePreselectedProvider()
        )

        (
            raw_by_slot,
            model,
            _duration_ms,
        ) = (
            _generate_compact_slot_questions(
                provider,
                slot_specs=specs,
                difficulty="MEDIUM",
            )
        )

        assert provider.calls == 1
        assert model == "fake-v6.1"

        # Prompt must no longer expose the entire answer
        # catalogue to the model.
        assert '"answers"' not in (
            provider.last_prompt
        )

        assert '"correct_answer"' in (
            provider.last_prompt
        )

        seen = set()
        correct_keys = []

        for slot_id in (
            "0",
            "1",
        ):
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

            correct = [
                option
                for option
                in question.options
                if option.is_correct
            ]

            assert len(
                correct
            ) == 1

            expected = (
                choices[
                    slot_id
                ][
                    "answer_text"
                ]
            )

            assert (
                correct[
                    0
                ].option_text
                == expected
            )

            correct_keys.append(
                correct[
                    0
                ].option_key
            )

            ok, reason, _verification = (
                _fast_grounding_check(
                    source_text=(
                        source_text
                    ),
                    question=(
                        question
                    ),
                    evidence_quote=(
                        raw[
                            "evidence_quote"
                        ]
                    ),
                )
            )

            assert ok is True, reason

        assert correct_keys == [
            "A",
            "B",
        ]

        print()
        print("=" * 72)
        print("PERFORMANCE V6.1 PRESELECTED ANSWER TEST")
        print("=" * 72)
        print("AI calls:", provider.calls)
        print("Backend preselects evidence + answer:", True)
        print("Prompt exposes full answer catalogue:", False)
        print("Model returns only q + distractors:", True)
        print("Backend correct keys:", correct_keys)
        print("Fast Gate passes:", 2)
        print("Result: PASS")
        print("=" * 72)


if __name__ == "__main__":
    main()
