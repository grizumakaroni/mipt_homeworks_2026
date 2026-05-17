from __future__ import annotations

from pathlib import Path

import pytest

from final_project.chunks import (
    ChunkCommandError,
    ChunkOptions,
    build_chunk_prompt,
    parse_chunk_command,
    split_text,
)
from final_project.files import FileMentionError, expand_file_mentions


def test_expands_file_mentions_relative_to_base_dir(tmp_path: Path) -> None:
    source = tmp_path / 'sample.py'
    source.write_text('print(42)\n', encoding='utf-8')

    expanded = expand_file_mentions('Проверь @::sample.py::', base_dir=tmp_path)

    assert expanded == 'Проверь \nprint(42)\n'


def test_missing_file_raises_readable_error(tmp_path: Path) -> None:
    with pytest.raises(FileMentionError, match='не найден'):
        expand_file_mentions('@::missing.txt::', base_dir=tmp_path)


def test_parse_chunk_command_supports_alias_and_auto_mode() -> None:
    options = parse_chunk_command('/filechunk paragraph=3 -y')

    assert options == ChunkOptions(mode='paragraph', size=3, auto_confirm=True)


def test_parse_chunk_command_supports_length_mode() -> None:
    options = parse_chunk_command('/file_chunk len=4')

    assert options == ChunkOptions(mode='length', size=4, auto_confirm=False)


def test_parse_chunk_command_rejects_unknown_option() -> None:
    with pytest.raises(ChunkCommandError):
        parse_chunk_command('/filechunk words=10')


def test_split_text_by_paragraph_groups() -> None:
    chunks = split_text('one\ntwo\nthree', ChunkOptions(mode='paragraph', size=2))

    assert chunks == ['one\ntwo', 'three']


def test_split_text_by_length() -> None:
    chunks = split_text('abcdef', ChunkOptions(mode='length', size=2))

    assert chunks == ['ab', 'cd', 'ef']


def test_build_chunk_prompt_includes_user_task_and_chunk() -> None:
    prompt = build_chunk_prompt('summarize', 'text')

    assert prompt == 'summarize\n\nФрагмент:\ntext'
