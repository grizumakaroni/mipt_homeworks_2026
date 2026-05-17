from __future__ import annotations

from final_project.history import ChatHistory


def test_history_keeps_recent_messages_by_count() -> None:
    history = ChatHistory(limit_message=2, limit_chars=None)

    history.add('user', 'first')
    history.add('assistant', 'second')
    history.add('user', 'third')

    assert [message.content for message in history.messages] == ['second', 'third']


def test_history_trims_old_messages_by_char_limit() -> None:
    history = ChatHistory(limit_message=None, limit_chars=7)

    history.add('user', 'hello')
    history.add('assistant', 'world')

    assert [message.content for message in history.messages] == ['world']


def test_history_crops_single_too_long_message_from_left() -> None:
    history = ChatHistory(limit_message=None, limit_chars=4)

    history.add('user', 'abcdef')

    assert history.messages[0].content == 'cdef'


def test_history_clear_removes_messages() -> None:
    history = ChatHistory(limit_message=2, limit_chars=10)
    history.add('user', 'question')

    history.clear()

    assert not history.messages
