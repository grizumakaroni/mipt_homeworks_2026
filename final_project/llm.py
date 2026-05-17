from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Any, Protocol, cast

from openai import OpenAI, OpenAIError

from .models import Message


class LLMError(Exception):
    pass


class StreamingChat(Protocol):
    def stream_chat(self, messages: Sequence[Message]) -> Iterator[str]:
        pass


class OpenAIChatClient:
    def __init__(self, api_key: str, api_host: str, model: str, temperature: float) -> None:
        self._client = OpenAI(api_key=api_key, base_url=api_host)
        self._model = model
        self._temperature = temperature

    def stream_chat(self, messages: Sequence[Message]) -> Iterator[str]:
        payload = [_to_openai_message(message) for message in messages]
        try:
            stream = self._client.chat.completions.create(
                model=self._model,
                messages=cast(Any, payload),
                temperature=self._temperature,
                stream=True,
            )
            for event in stream:
                content = _extract_delta(event)
                if content:
                    yield content
        except OpenAIError as exc:
            raise LLMError(str(exc)) from exc


def _to_openai_message(message: Message) -> dict[str, str]:
    return {'role': message.role, 'content': message.content}


def _extract_delta(event: object) -> str | None:
    choices = cast(Sequence[object] | None, getattr(event, 'choices', None))
    if not choices:
        return None

    delta = getattr(choices[0], 'delta', None)
    content = getattr(delta, 'content', None)
    return content if isinstance(content, str) else None
