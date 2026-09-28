from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import urlparse

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
            "Configure an AI endpoint in .env."
        )

    def embeddings(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        raise AIProviderError(
            "Embedding provider is disabled."
        )


class OpenAICompatibleProvider(AIProvider):
    """
    Hybrid provider optimized for this project.

    - Local Ollama chat:
        native /api/chat
        think=false by default
        format=json when json_mode=True

    - Embeddings:
        existing OpenAI-compatible /v1/embeddings

    - Non-local/non-Ollama endpoints:
        existing /chat/completions behavior

    This keeps the current .env compatible:

        AI_PROVIDER=openai_compatible
        AI_BASE_URL=http://localhost:11434/v1
    """

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

    def _headers(
        self,
    ) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if settings.ai_api_key:
            headers["Authorization"] = (
                f"Bearer {settings.ai_api_key}"
            )

        return headers

    def _timeout(
        self,
    ) -> httpx.Timeout:
        return httpx.Timeout(
            connect=10.0,
            read=float(
                settings.ai_timeout_seconds
            ),
            write=30.0,
            pool=10.0,
        )

    # =====================================================
    # ENDPOINT DETECTION
    # =====================================================

    def _is_local_ollama(
        self,
    ) -> bool:
        """
        Detect the local Ollama endpoint used by the project.

        Expected:
            http://localhost:11434/v1
            http://127.0.0.1:11434/v1

        10.0.2.2 is included for Android-emulator setups.
        """

        raw = (
            settings.ai_base_url
            or ""
        ).strip()

        try:
            parsed = urlparse(
                raw
            )
        except ValueError:
            return False

        hostname = (
            parsed.hostname
            or ""
        ).lower()

        port = parsed.port

        return (
            hostname
            in {
                "localhost",
                "127.0.0.1",
                "10.0.2.2",
            }
            and (
                port is None
                or port == 11434
            )
        )

    def _ollama_root_url(
        self,
    ) -> str:
        """
        Convert:
            http://localhost:11434/v1

        to:
            http://localhost:11434
        """

        base = (
            settings.ai_base_url
            or ""
        ).rstrip("/")

        if base.endswith(
            "/v1"
        ):
            base = base[:-3]

        return base.rstrip("/")

    # =====================================================
    # CHAT
    # =====================================================

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

        # Local Ollama gets the native fast path.
        if self._is_local_ollama():
            return self._chat_ollama_native(
                messages,
                json_mode=json_mode,
                temperature=temperature,
                max_tokens=max_tokens,
                reasoning_effort=reasoning_effort,
            )

        # Preserve generic OpenAI-compatible fallback.
        return self._chat_openai_compatible(
            messages,
            json_mode=json_mode,
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
        )

    # =====================================================
    # NATIVE OLLAMA FAST PATH
    # =====================================================

    def _chat_ollama_native(
        self,
        messages: list[dict[str, str]],
        *,
        json_mode: bool,
        temperature: float,
        max_tokens: int | None,
        reasoning_effort: Literal[
            "none",
            "low",
            "medium",
            "high",
        ]
        | None,
    ) -> AIChatResult:
        """
        Native Ollama /api/chat.

        PERFORMANCE V2:
        - think=False by default.
        - reasoning is enabled only when a caller
          explicitly requests low/medium/high.
        """

        # The current quiz/RAG workloads benefit from
        # deterministic non-thinking generation.
        think_enabled = (
            reasoning_effort
            in {
                "low",
                "medium",
                "high",
            }
        )

        options: dict[
            str,
            Any,
        ] = {
            "temperature": (
                temperature
            ),
        }

        if max_tokens is not None:
            options[
                "num_predict"
            ] = int(
                max_tokens
            )

        payload: dict[
            str,
            Any,
        ] = {
            "model": (
                settings.ai_chat_model
            ),
            "messages": messages,
            "stream": False,
            "think": (
                think_enabled
            ),
            "options": options,

            # Keep the chat model warm for repeated
            # quiz/verifier calls.
            "keep_alive": "30m",
        }

        if json_mode:
            payload[
                "format"
            ] = "json"

        url = (
            f"{self._ollama_root_url()}"
            "/api/chat"
        )

        started = (
            time.perf_counter()
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
                "Ollama native chat request "
                "timed out after "
                f"{settings.ai_timeout_seconds} "
                "seconds"
            ) from exc

        except httpx.ConnectError as exc:
            raise AIProviderError(
                "Cannot connect to Ollama at "
                f"{self._ollama_root_url()}"
            ) from exc

        except httpx.HTTPStatusError as exc:
            body = (
                exc.response.text[:500]
            )

            raise AIProviderError(
                "Ollama native chat HTTP error "
                f"{exc.response.status_code}: "
                f"{body}"
            ) from exc

        except httpx.HTTPError as exc:
            raise AIProviderError(
                "Ollama native chat HTTP error: "
                f"{exc}"
            ) from exc

        except ValueError as exc:
            raise AIProviderError(
                "Ollama native chat returned "
                "invalid JSON"
            ) from exc

        elapsed_ms = (
            time.perf_counter()
            - started
        ) * 1000.0

        message = (
            data.get(
                "message"
            )
            or {}
        )

        content = str(
            message.get(
                "content"
            )
            or ""
        ).strip()

        if not content:
            raise AIProviderError(
                "Ollama native chat returned "
                "empty content"
            )

        prompt_tokens = data.get(
            "prompt_eval_count"
        )

        completion_tokens = data.get(
            "eval_count"
        )

        load_duration_ns = data.get(
            "load_duration"
        )

        prompt_eval_duration_ns = (
            data.get(
                "prompt_eval_duration"
            )
        )

        eval_duration_ns = data.get(
            "eval_duration"
        )

        def _ns_to_ms(
            value: Any,
        ) -> float | None:
            if not isinstance(
                value,
                (
                    int,
                    float,
                ),
            ):
                return None

            return round(
                float(value)
                / 1_000_000.0,
                2,
            )

        load_ms = _ns_to_ms(
            load_duration_ns
        )

        prompt_eval_ms = (
            _ns_to_ms(
                prompt_eval_duration_ns
            )
        )

        eval_ms = _ns_to_ms(
            eval_duration_ns
        )

        print(
            "[AI PERF] "
            "provider=ollama_native "
            f"model={settings.ai_chat_model} "
            f"think={str(think_enabled).lower()} "
            f"json={str(json_mode).lower()} "
            f"wall_ms={elapsed_ms:.2f} "
            f"prompt_tokens={prompt_tokens} "
            f"completion_tokens={completion_tokens} "
            f"load_ms={load_ms} "
            f"prompt_eval_ms={prompt_eval_ms} "
            f"eval_ms={eval_ms}"
        )

        return AIChatResult(
            content=content,
            model=(
                data.get(
                    "model"
                )
                or settings.ai_chat_model
            ),
            prompt_tokens=(
                int(
                    prompt_tokens
                )
                if isinstance(
                    prompt_tokens,
                    int,
                )
                else None
            ),
            completion_tokens=(
                int(
                    completion_tokens
                )
                if isinstance(
                    completion_tokens,
                    int,
                )
                else None
            ),
        )

    # =====================================================
    # GENERIC OPENAI-COMPATIBLE FALLBACK
    # =====================================================

    def _chat_openai_compatible(
        self,
        messages: list[dict[str, str]],
        *,
        json_mode: bool,
        temperature: float,
        max_tokens: int | None,
        reasoning_effort: Literal[
            "none",
            "low",
            "medium",
            "high",
        ]
        | None,
    ) -> AIChatResult:

        payload: dict[
            str,
            Any,
        ] = {
            "model": (
                settings.ai_chat_model
            ),
            "messages": messages,
            "temperature": (
                temperature
            ),
        }

        if max_tokens is not None:
            payload[
                "max_tokens"
            ] = (
                max_tokens
            )

        if reasoning_effort is not None:
            payload[
                "reasoning_effort"
            ] = (
                reasoning_effort
            )

        if json_mode:
            payload[
                "response_format"
            ] = {
                "type": (
                    "json_object"
                )
            }

        url = (
            f"{settings.ai_base_url.rstrip('/')}"
            "/chat/completions"
        )

        started = (
            time.perf_counter()
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
                f"{settings.ai_timeout_seconds} "
                "seconds"
            ) from exc

        except httpx.ConnectError as exc:
            raise AIProviderError(
                "Cannot connect to AI server at "
                f"{settings.ai_base_url}"
            ) from exc

        except httpx.HTTPStatusError as exc:
            body = (
                exc.response.text[:500]
            )

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

        elapsed_ms = (
            time.perf_counter()
            - started
        ) * 1000.0

        choices = data.get(
            "choices"
        )

        if not choices:
            raise AIProviderError(
                "AI chat response contains "
                "no choices"
            )

        message = (
            choices[0].get(
                "message"
            )
            or {}
        )

        content = str(
            message.get(
                "content"
            )
            or ""
        ).strip()

        if not content:
            raise AIProviderError(
                "AI chat returned empty content"
            )

        usage = (
            data.get(
                "usage"
            )
            or {}
        )

        print(
            "[AI PERF] "
            "provider=openai_compatible "
            f"model={settings.ai_chat_model} "
            f"wall_ms={elapsed_ms:.2f}"
        )

        return AIChatResult(
            content=content,
            model=(
                data.get(
                    "model"
                )
                or settings.ai_chat_model
            ),
            prompt_tokens=(
                usage.get(
                    "prompt_tokens"
                )
            ),
            completion_tokens=(
                usage.get(
                    "completion_tokens"
                )
            ),
        )

    # =====================================================
    # EMBEDDINGS
    # =====================================================

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

        # Keep the already working OpenAI-compatible
        # embedding endpoint.
        url = (
            f"{settings.ai_base_url.rstrip('/')}"
            "/embeddings"
        )

        payload = {
            "model": (
                settings.ai_embedding_model
            ),
            "input": texts,
        }

        started = (
            time.perf_counter()
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
                "Embedding request timed out after "
                f"{settings.ai_timeout_seconds} "
                "seconds"
            ) from exc

        except httpx.ConnectError as exc:
            raise AIProviderError(
                "Cannot connect to AI server at "
                f"{settings.ai_base_url}"
            ) from exc

        except httpx.HTTPStatusError as exc:
            body = (
                exc.response.text[:500]
            )

            raise AIProviderError(
                "Embedding HTTP error "
                f"{exc.response.status_code}: "
                f"{body}"
            ) from exc

        except httpx.HTTPError as exc:
            raise AIProviderError(
                "Embedding HTTP error: "
                f"{exc}"
            ) from exc

        except ValueError as exc:
            raise AIProviderError(
                "Embedding endpoint returned "
                "invalid JSON"
            ) from exc

        rows = sorted(
            data.get(
                "data",
                [],
            ),
            key=lambda row: (
                row.get(
                    "index",
                    0,
                )
            ),
        )

        if len(rows) != len(texts):
            raise AIProviderError(
                "Embedding provider returned "
                f"{len(rows)} vectors for "
                f"{len(texts)} inputs"
            )

        vectors: list[
            list[float]
        ] = []

        for row in rows:
            vector = row.get(
                "embedding"
            )

            if not isinstance(
                vector,
                list,
            ):
                raise AIProviderError(
                    "Embedding response contains "
                    "an invalid vector"
                )

            vectors.append(
                vector
            )

        elapsed_ms = (
            time.perf_counter()
            - started
        ) * 1000.0

        print(
            "[AI PERF] "
            "provider=embedding_openai_compatible "
            f"model={settings.ai_embedding_model} "
            f"inputs={len(texts)} "
            f"wall_ms={elapsed_ms:.2f}"
        )

        return vectors


def get_ai_provider() -> AIProvider:

    if (
        settings.ai_provider
        == "openai_compatible"
    ):
        return OpenAICompatibleProvider()

    return DisabledAIProvider()
