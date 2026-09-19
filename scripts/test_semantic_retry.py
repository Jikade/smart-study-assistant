from __future__ import annotations

import json
from types import SimpleNamespace

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DocumentChunk
from app.db.session import engine
from app.services.quiz_service import (
    _validate_question_with_retry,
)

# =========================================================
# TEST DATA
# =========================================================


GOOD_QUESTION_TEXT = (
    "Chức năng nào của tiền tệ thể hiện việc "
    "tiền được rút khỏi lưu thông và cất giữ lại?"
)


GOOD_EVIDENCE = (
    "3. Phương tiện cất trữ: Tiền được rút khỏi "
    "lưu thông và cất giữ lại để khi cần đem ra "
    "mua hàng, vì tiền là đại biểu cho của cải "
    "xã hội dưới hình thái giá trị."
)


# =========================================================
# FAKE AI PROVIDER
# =========================================================


class FakeSemanticRetryProvider:
    """
    Deterministic regression provider for Semantic V2.5.

    Expected flow:

        Initial candidate
            ↓
        Stage 1 rejects
            ↓
        Normal replacement
            ↓
        Stage 1 rejects
            ↓
        Evidence-anchored final replacement
            ↓
        Stage 1 passes
            ↓
        Stage 2 selects B
            ↓
        PASS

    No real Ollama / Qwen call is made.
    """

    can_chat = True

    def __init__(self):
        self.normal_replacement_calls = 0
        self.evidence_retry_calls = 0
        self.stage1_calls = 0
        self.stage2_calls = 0
        self.stage3_calls = 0

    # -----------------------------------------------------
    # RESPONSE HELPER
    # -----------------------------------------------------

    @staticmethod
    def _result(
        payload: dict,
    ):
        return SimpleNamespace(
            content=json.dumps(
                payload,
                ensure_ascii=False,
            ),
            model="fake-semantic-v2.5",
        )

    # -----------------------------------------------------
    # CHAT
    # -----------------------------------------------------

    def chat(
        self,
        messages,
        **kwargs,
    ):
        system_text = ""

        user_text = ""

        for message in messages:
            role = message.get(
                "role",
                "",
            )

            content = str(
                message.get(
                    "content",
                    "",
                )
            )

            if role == "system":
                system_text += content + "\n"

            elif role == "user":
                user_text += content + "\n"

        system_lower = system_text.lower()

        user_lower = user_text.lower()

        # =================================================
        # FINAL EVIDENCE-ANCHORED GENERATION
        # =================================================

        if "evidence-anchored" in system_lower or "final grounding retry" in user_lower:
            self.evidence_retry_calls += 1

            return self._result(
                {
                    "questions": [
                        {
                            "question_text": GOOD_QUESTION_TEXT,
                            "difficulty": "MEDIUM",
                            "explanation": (
                                "Nguồn nêu rõ "
                                "phương tiện cất trữ "
                                "là chức năng trong đó "
                                "tiền được rút khỏi "
                                "lưu thông và cất giữ lại."
                            ),
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
                                    "explanation": (
                                        "Tiền được rút "
                                        "khỏi lưu thông "
                                        "và cất giữ lại."
                                    ),
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
                    ]
                }
            )

        # =================================================
        # NORMAL REPLACEMENT
        #
        # Deliberately generate another semantically
        # unsupported PURPOSE question.
        # =================================================

        if "fully grounded" in system_lower and "replacement" in system_lower:
            self.normal_replacement_calls += 1

            return self._result(
                {
                    "questions": [
                        {
                            "question_text": (
                                "Mục đích của " "quy luật giá trị " "là gì?"
                            ),
                            "difficulty": "MEDIUM",
                            "explanation": (
                                "Candidate intentionally "
                                "invalid for regression test."
                            ),
                            "options": [
                                {
                                    "option_key": "A",
                                    "option_text": ("Bảo đảm cân bằng " "cung và cầu"),
                                    "is_correct": True,
                                    "explanation": None,
                                    "position": 1,
                                },
                                {
                                    "option_key": "B",
                                    "option_text": ("Tạo ra " "giá trị thặng dư"),
                                    "is_correct": False,
                                    "explanation": None,
                                    "position": 2,
                                },
                                {
                                    "option_key": "C",
                                    "option_text": ("Xóa bỏ " "cạnh tranh"),
                                    "is_correct": False,
                                    "explanation": None,
                                    "position": 3,
                                },
                                {
                                    "option_key": "D",
                                    "option_text": ("Loại bỏ " "lưu thông hàng hóa"),
                                    "is_correct": False,
                                    "explanation": None,
                                    "position": 4,
                                },
                            ],
                        }
                    ]
                }
            )

        # =================================================
        # STAGE 1
        # SOURCE-ONLY GROUNDING VERIFIER
        # =================================================

        if "source-grounding examiner" in system_lower:
            self.stage1_calls += 1

            # ---------------------------------------------
            # Final good candidate.
            # ---------------------------------------------

            if GOOD_QUESTION_TEXT in user_text:
                return self._result(
                    {
                        "answerable": True,
                        "relation_supported": True,
                        "answer_text": "Phương tiện cất trữ",
                        "evidence_quote": GOOD_EVIDENCE,
                        "reason": (
                            "SOURCE trực tiếp nêu "
                            "chức năng phương tiện "
                            "cất trữ và mô tả tiền "
                            "được rút khỏi lưu thông."
                        ),
                    }
                )

            # ---------------------------------------------
            # Initial candidate + normal replacement
            # must fail.
            # ---------------------------------------------

            return self._result(
                {
                    "answerable": False,
                    "relation_supported": False,
                    "answer_text": "",
                    "evidence_quote": "",
                    "reason": ("SOURCE không trực tiếp " "nêu mục đích được hỏi."),
                }
            )

        # =================================================
        # STAGE 2
        # BLIND OPTION MATCHING
        # =================================================

        if "multiple-choice answer matcher" in user_lower:
            self.stage2_calls += 1

            return self._result(
                {
                    "selected_option_key": "B",
                    "supported_option_keys": ["B"],
                    "ambiguous": False,
                    "reason": (
                        "Phương tiện cất trữ "
                        "khớp duy nhất với "
                        "evidence từ SOURCE."
                    ),
                }
            )

        # =================================================
        # STAGE 3
        #
        # Should NOT run because final candidate
        # already marks B correctly.
        # =================================================

        if "adversarial" in system_lower and "repair" in system_lower:
            self.stage3_calls += 1

            raise AssertionError(
                "Stage 3 should not run " "in this regression scenario."
            )

        # =================================================
        # UNKNOWN PROMPT
        # =================================================

        raise AssertionError(
            "Fake provider received an "
            "unexpected prompt.\n\n"
            "SYSTEM:\n"
            f"{system_text}\n\n"
            "USER:\n"
            f"{user_text[:1000]}"
        )


# =========================================================
# TEST
# =========================================================


def main():
    provider = FakeSemanticRetryProvider()

    with Session(engine) as db:

        source_chunk = db.scalar(select(DocumentChunk).where(DocumentChunk.id == 410))

        if source_chunk is None:
            raise RuntimeError("Document chunk 410 not found.")

        # =================================================
        # INITIAL CANDIDATE
        #
        # Intentionally invalid semantic relationship:
        # asks PURPOSE although the corresponding SOURCE
        # statement describes a REQUIREMENT.
        # =================================================

        bad_question = {
            "question_text": (
                "Theo quy luật giá trị, "
                "mục đích của sản xuất "
                "và trao đổi hàng hóa "
                "là gì?"
            ),
            "difficulty": "MEDIUM",
            "explanation": ("Intentionally bad " "semantic candidate."),
            "options": [
                {
                    "option_key": "A",
                    "option_text": ("Bảo đảm cân bằng " "giữa cung và cầu"),
                    "is_correct": True,
                    "explanation": None,
                    "position": 1,
                },
                {
                    "option_key": "B",
                    "option_text": ("Dựa trên hao phí " "lao động xã hội cần thiết"),
                    "is_correct": False,
                    "explanation": None,
                    "position": 2,
                },
                {
                    "option_key": "C",
                    "option_text": ("Tạo ra " "giá trị thặng dư"),
                    "is_correct": False,
                    "explanation": None,
                    "position": 3,
                },
                {
                    "option_key": "D",
                    "option_text": ("Loại bỏ cạnh tranh " "trên thị trường"),
                    "is_correct": False,
                    "explanation": None,
                    "position": 4,
                },
            ],
        }

        # =================================================
        # RUN V2.5 RETRY PIPELINE
        # =================================================

        (
            question,
            retries_used,
            verification,
        ) = _validate_question_with_retry(
            provider,
            source_chunk=source_chunk,
            initial_raw_question=(bad_question),
            difficulty="MEDIUM",
            used_question_texts=set(),
        )

        # =================================================
        # ASSERTIONS
        # =================================================

        assert retries_used == 2, (
            "Expected exactly 2 retries " f"but got {retries_used}"
        )

        assert provider.normal_replacement_calls == 1, (
            "Normal replacement should " "run exactly once."
        )

        assert provider.evidence_retry_calls == 1, (
            "Evidence-anchored final retry " "should run exactly once."
        )

        assert provider.stage1_calls == 3, (
            "Stage 1 should run for all " "three candidates."
        )

        assert provider.stage2_calls == 1, (
            "Stage 2 should run only for " "the final grounded candidate."
        )

        assert provider.stage3_calls == 0, (
            "Stage 3 should not run because "
            "the final candidate already "
            "marks the verified option."
        )

        assert question.question_text == GOOD_QUESTION_TEXT

        correct_options = [option for option in question.options if option.is_correct]

        assert len(correct_options) == 1

        assert correct_options[0].option_key == "B"

        assert correct_options[0].option_text == "Phương tiện cất trữ"

        assert verification.get("correctness_repaired") is False

        assert verification.get("verified_correct_key") == "B"

        # =================================================
        # RESULT
        # =================================================

        print()
        print("=" * 70)

        print("SEMANTIC V2.5 " "EVIDENCE-ANCHORED RETRY TEST")

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
            "Normal replacements:",
            provider.normal_replacement_calls,
        )

        print(
            "Evidence-anchored retries:",
            provider.evidence_retry_calls,
        )

        print(
            "Stage-1 calls:",
            provider.stage1_calls,
        )

        print(
            "Stage-2 calls:",
            provider.stage2_calls,
        )

        print(
            "Stage-3 calls:",
            provider.stage3_calls,
        )

        print(
            "Final question:",
            question.question_text,
        )

        print(
            "Verified correct key:",
            verification.get("verified_correct_key"),
        )

        print(
            "Correct answer:",
            correct_options[0].option_text,
        )

        print("=" * 70)


if __name__ == "__main__":
    main()
