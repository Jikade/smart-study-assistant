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

        # -------------------------------------------------
        # Intentionally bad question.
        #
        # Đây chính là dạng câu trước đó chúng ta
        # đã phát hiện sai semantic:
        # hỏi "mục đích", trong khi SOURCE không
        # trực tiếp hỗ trợ quan hệ "mục đích".
        # -------------------------------------------------

        bad_question = {
            "question_text": (
                "Theo quy luật giá trị, mục đích "
                "của sản xuất và trao đổi hàng hóa "
                "là gì?"
            ),
            "difficulty": "MEDIUM",
            "explanation": (
                "Đảm bảo sự cân bằng giữa cung "
                "và cầu trong thị trường."
            ),
            "options": [
                {
                    "option_key": "A",
                    "option_text": (
                        "Đảm bảo sự cân bằng giữa "
                        "cung và cầu trong thị trường"
                    ),
                    "is_correct": True,
                    "explanation": None,
                    "position": 1,
                },
                {
                    "option_key": "B",
                    "option_text": (
                        "Tăng năng suất lao động "
                        "thông qua cải tiến kỹ thuật"
                    ),
                    "is_correct": False,
                    "explanation": None,
                    "position": 2,
                },
                {
                    "option_key": "C",
                    "option_text": (
                        "Phân hóa người sản xuất "
                        "thành người giàu và "
                        "người nghèo"
                    ),
                    "is_correct": False,
                    "explanation": None,
                    "position": 3,
                },
                {
                    "option_key": "D",
                    "option_text": (
                        "Tạo ra giá trị thặng dư "
                        "cho nhà tư bản"
                    ),
                    "is_correct": False,
                    "explanation": None,
                    "position": 4,
                },
            ],
        }

        question, retries_used, verification = (
            _validate_question_with_retry(
                provider,
                source_chunk=source_chunk,
                initial_raw_question=bad_question,
                difficulty="MEDIUM",
                used_question_texts=set(),
            )
        )

        print()
        print("=" * 70)
        print("SEMANTIC RETRY TEST RESULT")
        print("=" * 70)

        print(
            "Source chunk:",
            source_chunk.id,
        )

        print(
            "Retries used:",
            retries_used,
        )

        print()
        print(
            "Final question:",
            question.question_text,
        )

        print()
        print("Final options:")

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

        print(
            "Relation supported:",
            verification.get(
                "relation_supported"
            ),
        )

        print(
            "Evidence exists:",
            verification.get(
                "evidence_exists_in_source"
            ),
        )

        print(
            "Evidence:",
            verification.get(
                "evidence_quote"
            ),
        )

        print()
        print("=" * 70)


if __name__ == "__main__":
    main()