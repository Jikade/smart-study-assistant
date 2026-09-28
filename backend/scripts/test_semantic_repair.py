from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DocumentChunk
from app.db.session import engine
from app.services.ai_provider import get_ai_provider
from app.services.quiz_service import (
    _validate_question_with_retry,
)


def main():
    provider = get_ai_provider()

    if not provider.can_chat:
        raise RuntimeError(
            "AI chat provider is not configured."
        )

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

        # =================================================
        # CÂU HỎI HỢP LỆ NHƯNG CỐ TÌNH GẮN SAI ĐÁP ÁN
        #
        # Nội dung đúng phải là:
        # B. Phương tiện cất trữ
        #
        # Nhưng ta cố tình đánh:
        # A = True
        #
        # Mục tiêu:
        # Stage 2 + Stage 3 phải phát hiện và
        # backend repair A -> B.
        # =================================================

        wrong_label_question = {
            "question_text": (
                "Chức năng nào của tiền tệ thể hiện "
                "việc tiền được rút khỏi lưu thông "
                "và cất giữ lại?"
            ),

            "difficulty": "MEDIUM",

            "explanation": (
                "Cố tình gắn sai đáp án để "
                "kiểm thử Semantic V2.2."
            ),

            "options": [
                {
                    "option_key": "A",
                    "option_text": (
                        "Phương tiện thanh toán"
                    ),
                    "is_correct": True,
                    "explanation": None,
                    "position": 1,
                },
                {
                    "option_key": "B",
                    "option_text": (
                        "Phương tiện cất trữ"
                    ),
                    "is_correct": False,
                    "explanation": None,
                    "position": 2,
                },
                {
                    "option_key": "C",
                    "option_text": (
                        "Tiền tệ thế giới"
                    ),
                    "is_correct": False,
                    "explanation": None,
                    "position": 3,
                },
                {
                    "option_key": "D",
                    "option_text": (
                        "Phương tiện lưu thông"
                    ),
                    "is_correct": False,
                    "explanation": None,
                    "position": 4,
                },
            ],
        }

        (
            question,
            retries_used,
            verification,
        ) = _validate_question_with_retry(
            provider,
            source_chunk=source_chunk,
            initial_raw_question=(
                wrong_label_question
            ),
            difficulty="MEDIUM",
            used_question_texts=set(),
        )

        print()
        print("=" * 70)
        print("SEMANTIC V2.2 REPAIR TEST")
        print("=" * 70)

        print(
            "Source chunk:",
            source_chunk.id,
        )

        print(
            "Retries used:",
            retries_used,
        )

        print(
            "Correctness repaired:",
            verification.get(
                "correctness_repaired"
            ),
        )

        print(
            "Original correct key:",
            verification.get(
                "original_correct_key"
            ),
        )

        print(
            "Final correct key:",
            verification.get(
                "final_correct_key"
            ),
        )

        print(
            "Verifier selected:",
            verification.get(
                "selected_key"
            ),
        )

        print(
            "Supported keys:",
            verification.get(
                "supported_keys"
            ),
        )

        print()

        print(
            "Final question:",
            question.question_text,
        )

        print()

        for option in question.options:
            marker = (
                " <-- CORRECT"
                if option.is_correct
                else ""
            )

            print(
                f"{option.option_key}. "
                f"{option.option_text}"
                f"{marker}"
            )

        print()
        print("=" * 70)


if __name__ == "__main__":
    main()