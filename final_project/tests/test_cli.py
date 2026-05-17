from __future__ import annotations

from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest

from final_project.cli import answer_chat_message, build_conversation, render_stream
from final_project.config import AppConfig
from final_project.history import ChatHistory
from final_project.llm import LLMError
from final_project.models import Message


class FakeClient:
    def __init__(self, parts: Sequence[str] = ('ok',), fail: bool = False) -> None:
        self.messages: list[Sequence[Message]] = []
        self._parts = parts
        self._fail = fail

    def stream_chat(self, messages: Sequence[Message]) -> Iterator[str]:
        self.messages.append(messages)
        if self._fail:
            raise LLMError('server is down')
        yield from self._parts


class InterruptingClient:
    def stream_chat(self, messages: Sequence[Message]) -> Iterator[str]:
        raise KeyboardInterrupt
        yield from ()


def test_build_conversation_prepends_system_prompt(config: AppConfig) -> None:
    messages = build_conversation(config, [Message(role='user', content='hi')])

    assert messages == [
        Message(role='system', content='system'),
        Message(role='user', content='hi'),
    ]


def test_render_stream_writes_and_returns_answer() -> None:
    written: list[str] = []
    answer = render_stream(
        FakeClient(parts=('he', 'llo')),
        [Message(role='user', content='hi')],
        written.append,
    )

    assert answer == 'hello'
    assert written == ['he', 'llo']


def test_answer_chat_message_updates_history(config: AppConfig, tmp_path: Path) -> None:
    history = ChatHistory(limit_message=10, limit_chars=1000)
    written: list[str] = []

    ok = answer_chat_message(
        line='Hello',
        cfg=config,
        hist=history,
        bot=FakeClient(parts=('Hi',)),
        root=tmp_path,
        out=written.append,
    )

    assert ok
    assert [message.role for message in history.messages] == ['user', 'assistant']
    assert history.messages[-1].content == 'Hi'
    assert ''.join(written) == 'Ассистент: Hi\n'


def test_answer_chat_message_reports_file_error(config: AppConfig, tmp_path: Path) -> None:
    history = ChatHistory(limit_message=10, limit_chars=1000)
    written: list[str] = []

    ok = answer_chat_message(
        line='@::missing.py::',
        cfg=config,
        hist=history,
        bot=FakeClient(),
        root=tmp_path,
        out=written.append,
    )

    assert not ok
    assert not history.messages
    assert written[0].startswith('Ошибка файла:')


def test_answer_chat_message_keeps_user_message_on_llm_error(
    config: AppConfig,
    tmp_path: Path,
) -> None:
    history = ChatHistory(limit_message=10, limit_chars=1000)
    written: list[str] = []

    ok = answer_chat_message(
        line='Hello',
        cfg=config,
        hist=history,
        bot=FakeClient(fail=True),
        root=tmp_path,
        out=written.append,
    )

    assert not ok
    assert [message.role for message in history.messages] == ['user']
    assert 'Ошибка LLM' in ''.join(written)


def test_answer_chat_message_handles_keyboard_interrupt_during_llm_waiting(
    config: AppConfig,
    tmp_path: Path,
) -> None:
    history = ChatHistory(limit_message=10, limit_chars=1000)
    written: list[str] = []

    ok = answer_chat_message(
        line='Hello',
        cfg=config,
        hist=history,
        bot=InterruptingClient(),
        root=tmp_path,
        out=written.append,
    )

    assert not ok
    assert [message.role for message in history.messages] == ['user']
    assert 'Запрос прерван' in ''.join(written)


def test_answer_chat_message_expands_file_mentions(config: AppConfig, tmp_path: Path) -> None:
    source = tmp_path / 'sample.txt'
    source.write_text('payload', encoding='utf-8')
    history = ChatHistory(limit_message=10, limit_chars=1000)

    answer_chat_message(
        line='Read @::sample.txt::',
        cfg=config,
        hist=history,
        bot=FakeClient(),
        root=tmp_path,
        out=lambda _text: None,
    )

    assert history.messages[0].content == 'Read \npayload'


@pytest.fixture
def config() -> AppConfig:
    return AppConfig(
        api_key='key',
        api_host='http://localhost:11434/v1/',
        system_prompt='system',
    )
