from __future__ import annotations

import json
from types import SimpleNamespace

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DocumentChunk
from app.db.session import engine
from app.services.quiz_service import (
    _compact_item_to_raw_question,
    _fast_grounding_check,
    _generate_compact_slot_questions,
    _prepare_question_local,
)


EVIDENCE = (
    "3. Phương tiện cất trữ: Tiền được rút khỏi "
    "lưu thông và cất giữ lại để khi cần đem ra "
    "mua hàng, vì tiền là đại biểu cho của cải "
    "xã hội dưới hình thái giá trị."
)


class FakeCompactProvider:
    can_chat = True

    def __init__(self):
        self.calls = 0

    def chat(self, messages, **kwargs):
        self.calls += 1

        payload = {
            "items": [
                {
                    "slot": "0",
                    "q": (
                        "Chức năng nào của tiền tệ "
                        "thể hiện việc tiền được rút "
                        "khỏi lưu thông và cất giữ lại?"
                    ),
                    "e": EVIDENCE,
                    "c": "B",
                    "o": [
                        "Phương tiện thanh toán",
                        "Phương tiện cất trữ",
                        "Tiền tệ thế giới",
                        "Phương tiện lưu thông",
                    ],
                },
                {
                    "slot": "1",
                    "q": (
                        "Khi tiền được cất giữ để khi cần "
                        "đem ra mua hàng, đó là chức năng nào?"
                    ),
                    "e": EVIDENCE,
                    "c": "B",
                    "o": [
                        "Phương tiện thanh toán",
                        "Phương tiện cất trữ",
                        "Tiền tệ thế giới",
                        "Phương tiện lưu thông",
                    ],
                },
            ]
        }

        return SimpleNamespace(
            content=json.dumps(
                payload,
                ensure_ascii=False,
            ),
            model="fake-compact-v4",
        )


def main():
    provider = FakeCompactProvider()

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

        raw_by_slot, model, duration_ms = (
            _generate_compact_slot_questions(
                provider,
                slot_specs=specs,
                difficulty="MEDIUM",
            )
        )

        assert provider.calls == 1
        assert set(raw_by_slot) == {"0", "1"}
        assert model == "fake-compact-v4"

        seen = set()

        for slot_id in ["0", "1"]:
            raw = raw_by_slot[slot_id]

            question = _prepare_question_local(
                source_chunk=chunk,
                raw_question=raw,
                difficulty="MEDIUM",
                used_question_texts=set(),
                batch_seen_texts=seen,
            )

            ok, reason, verification = (
                _fast_grounding_check(
                    source_text=source_text,
                    question=question,
                    evidence_quote=raw["evidence_quote"],
                )
            )

            assert ok is True, reason
            assert (
                verification["verified_correct_key"]
                == "B"
            )

        print()
        print("=" * 70)
        print("PERFORMANCE V4 COMPACT GENERATION TEST")
        print("=" * 70)
        print("Question slots:", 2)
        print("AI calls:", provider.calls)
        print("Parsed slots:", sorted(raw_by_slot))
        print("Fast Gate passes:", 2)
        print("Result: PASS")
        print("=" * 70)


if __name__ == "__main__":
    main()
