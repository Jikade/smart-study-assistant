from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import httpx

from app.core.config import get_settings

settings = get_settings()


class AIProviderError(RuntimeError):
    pass


@dataclass
class AIChatResult:
    content: str
    model: str | None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class AIProvider:
    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        json_mode: bool = False,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        reasoning_effort: Literal[
            "none",
            "low",
            "medium",
            "high",
        ]
        | None = None,
    ) -> AIChatResult:
        raise NotImplementedError

    def embeddings(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        raise NotImplementedError

    @property
    def can_chat(self) -> bool:
        return False

    @property
    def can_embed(self) -> bool:
        return False


class DisabledAIProvider(AIProvider):
    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        json_mode: bool = False,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        reasoning_effort: Literal[
            "none",
            "low",
            "medium",
            "high",
        ]
        | None = None,
    ) -> AIChatResult:
        raise AIProviderError(
            "AI_PROVIDER is disabled. "
            "Configure an OpenAI-compatible endpoint in .env."
        )

    def embeddings(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        raise AIProviderError(
            "Embedding provider is disabled."
        )


class OpenAICompatibleProvider(AIProvider):

    @property
    def can_chat(self) -> bool:
        return bool(
            settings.ai_chat_model
        )

    @property
    def can_embed(self) -> bool:
        return bool(
            settings.ai_embedding_model
        )

    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if settings.ai_api_key:
            headers["Authorization"] = (
                f"Bearer {settings.ai_api_key}"
            )

        return headers

    def _timeout(self) -> httpx.Timeout:
        """
        Timeout riêng cho từng giai đoạn.

        connect:
            Thời gian kết nối tới Ollama.

        read:
            Thời gian chờ Ollama sinh response.
            Đây là timeout quan trọng nhất với Qwen.

        write:
            Thời gian gửi request.

        pool:
            Thời gian chờ connection từ pool.
        """
        return httpx.Timeout(
            connect=10.0,
            read=float(
                settings.ai_timeout_seconds
            ),
            write=30.0,
            pool=10.0,
        )

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        json_mode: bool = False,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        reasoning_effort: Literal[
            "none",
            "low",
            "medium",
            "high",
        ]
        | None = None,
    ) -> AIChatResult:

        if not settings.ai_chat_model:
            raise AIProviderError(
                "AI_CHAT_MODEL is not configured"
            )

        payload: dict[str, Any] = {
            "model": settings.ai_chat_model,
            "messages": messages,
            "temperature": temperature,
        }

        # Chỉ thêm nếu caller yêu cầu.
        # Không hard-code cho mọi tác vụ.
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        if reasoning_effort is not None:
            payload["reasoning_effort"] = (
                reasoning_effort
            )

        if json_mode:
            payload["response_format"] = {
                "type": "json_object"
            }

        url = (
            f"{settings.ai_base_url.rstrip('/')}"
            "/chat/completions"
        )

        try:
            with httpx.Client(
                timeout=self._timeout()
            ) as client:

                response = client.post(
                    url,
                    headers=self._headers(),
                    json=payload,
                )

                response.raise_for_status()

                data = response.json()

        except httpx.ReadTimeout as exc:
            raise AIProviderError(
                "AI chat request timed out after "
                f"{settings.ai_timeout_seconds} seconds"
            ) from exc

        except httpx.ConnectError as exc:
            raise AIProviderError(
                "Cannot connect to AI server at "
                f"{settings.ai_base_url}"
            ) from exc

        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:500]

            raise AIProviderError(
                "AI chat HTTP error "
                f"{exc.response.status_code}: "
                f"{body}"
            ) from exc

        except httpx.HTTPError as exc:
            raise AIProviderError(
                f"AI chat HTTP error: {exc}"
            ) from exc

        except ValueError as exc:
            raise AIProviderError(
                "AI chat returned invalid JSON"
            ) from exc

        # Validate response
        choices = data.get("choices")

        if not choices:
            raise AIProviderError(
                "AI chat response contains no choices"
            )

        message = (
            choices[0].get("message")
            or {}
        )

        content = (
            message.get("content")
            or ""
        ).strip()

        if not content:
            raise AIProviderError(
                "AI chat returned empty content"
            )

        usage = (
            data.get("usage")
            or {}
        )

        return AIChatResult(
            content=content,
            model=(
                data.get("model")
                or settings.ai_chat_model
            ),
            prompt_tokens=(
                usage.get("prompt_tokens")
            ),
            completion_tokens=(
                usage.get(
                    "completion_tokens"
                )
            ),
        )

    def embeddings(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        if not settings.ai_embedding_model:
            raise AIProviderError(
                "AI_EMBEDDING_MODEL "
                "is not configured"
            )

        if not texts:
            return []

        url = (
            f"{settings.ai_base_url.rstrip('/')}"
            "/embeddings"
        )

        payload = {
            "model":
                settings.ai_embedding_model,
            "input": texts,
        }

        try:
            with httpx.Client(
                timeout=self._timeout()
            ) as client:

                response = client.post(
                    url,
                    headers=self._headers(),
                    json=payload,
                )

                response.raise_for_status()

                data = response.json()

        except httpx.ReadTimeout as exc:
            raise AIProviderError(
                "Embedding request timed out after "
                f"{settings.ai_timeout_seconds} seconds"
            ) from exc

        except httpx.ConnectError as exc:
            raise AIProviderError(
                "Cannot connect to AI server at "
                f"{settings.ai_base_url}"
            ) from exc

        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:500]

            raise AIProviderError(
                "Embedding HTTP error "
                f"{exc.response.status_code}: "
                f"{body}"
            ) from exc

        except httpx.HTTPError as exc:
            raise AIProviderError(
                f"Embedding HTTP error: {exc}"
            ) from exc

        except ValueError as exc:
            raise AIProviderError(
                "Embedding endpoint returned "
                "invalid JSON"
            ) from exc

        rows = sorted(
            data.get("data", []),
            key=lambda row:
                row.get("index", 0),
        )

        if len(rows) != len(texts):
            raise AIProviderError(
                "Embedding provider returned "
                f"{len(rows)} vectors for "
                f"{len(texts)} inputs"
            )

        vectors: list[list[float]] = []

        for row in rows:
            vector = row.get("embedding")

            if not isinstance(
                vector,
                list,
            ):
                raise AIProviderError(
                    "Embedding response contains "
                    "an invalid vector"
                )

            vectors.append(vector)

        return vectors


def get_ai_provider() -> AIProvider:

    if (
        settings.ai_provider
        == "openai_compatible"
    ):
        return OpenAICompatibleProvider()

    return DisabledAIProvider()