from __future__ import annotations

import json
from types import SimpleNamespace

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DocumentChunk
from app.db.session import engine
from app.schemas.quizzes import QuestionCreate
from app.services.quiz_service import (
    _batch_verify_initial_questions,
)


GOOD_EVIDENCE = (
    "3. Phương tiện cất trữ: Tiền được rút khỏi "
    "lưu thông và cất giữ lại để khi cần đem ra "
    "mua hàng, vì tiền là đại biểu cho của cải "
    "xã hội dưới hình thái giá trị."
)


class FakeBatchProvider:
    can_chat = True

    def __init__(self):
        self.stage1_calls = 0
        self.stage2_calls = 0

    @staticmethod
    def _result(payload: dict):
        return SimpleNamespace(
            content=json.dumps(
                payload,
                ensure_ascii=False,
            ),
            model="fake-batch-v2.6",
        )

    def chat(self, messages, **kwargs):
        system_text = "\n".join(
            str(message.get("content", ""))
            for message in messages
            if message.get("role") == "system"
        ).lower()

        if "batch-verify source grounding" in system_text:
            self.stage1_calls += 1

            return self._result(
                {
                    "results": [
                        {
                            "id": "0",
                            "answerable": True,
                            "relation_supported": True,
                            "answer_text": "Phương tiện cất trữ",
                            "evidence_quote": GOOD_EVIDENCE,
                            "reason": "Grounded.",
                        },
                        {
                            "id": "1",
                            "answerable": True,
                            "relation_supported": True,
                            "answer_text": "Phương tiện cất trữ",
                            "evidence_quote": GOOD_EVIDENCE,
                            "reason": "Grounded.",
                        },
                    ]
                }
            )

        if "batch-match answer options" in system_text:
            self.stage2_calls += 1

            return self._result(
                {
                    "results": [
                        {
                            "id": "0",
                            "selected_option_key": "B",
                            "supported_option_keys": ["B"],
                            "ambiguous": False,
                            "reason": "Only B matches.",
                        },
                        {
                            "id": "1",
                            "selected_option_key": "B",
                            "supported_option_keys": ["B"],
                            "ambiguous": False,
                            "reason": "Only B matches.",
                        },
                    ]
                }
            )

        raise AssertionError(
            f"Unexpected prompt: {system_text[:300]}"
        )


def build_question(text: str, chunk_id: int) -> QuestionCreate:
    return QuestionCreate.model_validate(
        {
            "source_chunk_id": chunk_id,
            "question_text": text,
            "difficulty": "MEDIUM",
            "explanation": "Grounded test question.",
            "points": 1,
            "options": [
                {
                    "option_key": "A",
                    "option_text": "Phương tiện thanh toán",
                    "is_correct": False,
                    "explanation": None,
                    "position": 1,
                },
                {
                    "option_key": "B",
                    "option_text": "Phương tiện cất trữ",
                    "is_correct": True,
                    "explanation": "Correct.",
                    "position": 2,
                },
                {
                    "option_key": "C",
                    "option_text": "Tiền tệ thế giới",
                    "is_correct": False,
                    "explanation": None,
                    "position": 3,
                },
                {
                    "option_key": "D",
                    "option_text": "Phương tiện lưu thông",
                    "is_correct": False,
                    "explanation": None,
                    "position": 4,
                },
            ],
        }
    )


def main():
    provider = FakeBatchProvider()

    with Session(engine) as db:
        source_chunk = db.scalar(
            select(DocumentChunk).where(
                DocumentChunk.id == 410
            )
        )

        if source_chunk is None:
            raise RuntimeError(
                "Document chunk 410 not found."
            )

        source_text = (
            source_chunk.content or ""
        )[:1600].strip()

        question_1 = build_question(
            (
                "Chức năng nào của tiền tệ thể hiện "
                "việc tiền được rút khỏi lưu thông "
                "và cất giữ lại?"
            ),
            source_chunk.id,
        )

        question_2 = build_question(
            (
                "Theo nguồn tài liệu, khi tiền được "
                "rút khỏi lưu thông và cất giữ lại "
                "thì tiền đang thực hiện chức năng nào?"
            ),
            source_chunk.id,
        )

        outcomes, metrics = (
            _batch_verify_initial_questions(
                provider,
                prepared_items=[
                    {
                        "id": "0",
                        "source_chunk": source_chunk,
                        "source_text": source_text,
                        "raw_question": {},
                        "question": question_1,
                    },
                    {
                        "id": "1",
                        "source_chunk": source_chunk,
                        "source_text": source_text,
                        "raw_question": {},
                        "question": question_2,
                    },
                ],
            )
        )

        assert provider.stage1_calls == 1
        assert provider.stage2_calls == 1

        assert outcomes["0"]["ok"] is True
        assert outcomes["1"]["ok"] is True

        assert metrics["stage1_calls"] == 1
        assert metrics["stage2_calls"] == 1
        assert metrics["stage1_items"] == 2
        assert metrics["stage2_items"] == 2

        print()
        print("=" * 70)
        print("SEMANTIC V2.6 BATCH VERIFICATION TEST")
        print("=" * 70)
        print("Questions verified:", 2)
        print("Stage-1 AI calls:", provider.stage1_calls)
        print("Stage-2 AI calls:", provider.stage2_calls)
        print("Stage-1 items:", metrics["stage1_items"])
        print("Stage-2 items:", metrics["stage2_items"])
        print("Stage-1 ms:", metrics["stage1_ms"])
        print("Stage-2 ms:", metrics["stage2_ms"])
        print("Result: PASS")
        print("=" * 70)


if __name__ == "__main__":
    main()
