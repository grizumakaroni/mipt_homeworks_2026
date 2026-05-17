from __future__ import annotations

from collections.abc import Sequence

from .models import Message, Role


class ChatHistory:
    def __init__(self, limit_message: int | None, limit_chars: int | None) -> None:
        self._limit_message = limit_message
        self._limit_chars = limit_chars
        self._messages: list[Message] = []

    @property
    def messages(self) -> Sequence[Message]:
        return tuple(self._messages)

    def add(self, role: Role, content: str) -> None:
        self._messages.append(Message(role=role, content=content))
        self._trim()

    def clear(self) -> None:
        self._messages.clear()

    def _trim(self) -> None:
        if self._limit_message is not None:
            del self._messages[: max(0, len(self._messages) - self._limit_message)]

        if self._limit_chars is None:
            return

        while len(self._messages) > 1 and self._total_chars() > self._limit_chars:
            del self._messages[0]

        if self._messages and self._total_chars() > self._limit_chars:
            latest = self._messages[-1]
            self._messages[-1] = Message(
                role=latest.role,
                content=latest.content[-self._limit_chars:],
            )

    def _total_chars(self) -> int:
        return sum(len(message.content) for message in self._messages)
