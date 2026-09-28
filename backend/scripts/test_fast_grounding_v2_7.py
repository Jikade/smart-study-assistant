from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DocumentChunk
from app.db.session import engine
from app.schemas.quizzes import QuestionCreate
from app.services.quiz_service import (
    _fast_grounding_check,
)


def main():
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
            source_chunk.content
            or ""
        )[:1600].strip()

        evidence_quote = (
            "3. Phương tiện cất trữ: Tiền được rút khỏi "
            "lưu thông và cất giữ lại để khi cần đem ra "
            "mua hàng, vì tiền là đại biểu cho của cải "
            "xã hội dưới hình thái giá trị."
        )

        question = QuestionCreate.model_validate(
            {
                "source_chunk_id": source_chunk.id,
                "question_text": (
                    "Chức năng nào của tiền tệ thể hiện "
                    "việc tiền được rút khỏi lưu thông "
                    "và cất giữ lại?"
                ),
                "difficulty": "MEDIUM",
                "explanation": evidence_quote,
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
                        "explanation": evidence_quote,
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

        ok, reason, verification = _fast_grounding_check(
            source_text=source_text,
            question=question,
            evidence_quote=evidence_quote,
        )

        assert ok is True, reason
        assert verification["verified_correct_key"] == "B"
        assert (
            verification["verification_mode"]
            == "fast_grounding_gate"
        )

        print()
        print("=" * 70)
        print("SEMANTIC V2.7 FAST GROUNDING TEST")
        print("=" * 70)
        print("Source chunk:", source_chunk.id)
        print("Result: PASS")
        print("Verified correct key:", verification["verified_correct_key"])
        print("Verification mode:", verification["verification_mode"])
        print("=" * 70)


if __name__ == "__main__":
    main()
