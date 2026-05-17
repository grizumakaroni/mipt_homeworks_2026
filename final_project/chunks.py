from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from typing import Literal, TypeAlias


ChunkMode: TypeAlias = Literal['paragraph', 'length']
CHUNK_COMMANDS = frozenset(('/file_chunk', '/filechunk'))


class ChunkCommandError(Exception):
    pass


@dataclass(frozen=True)
class ChunkOptions:
    mode: ChunkMode = 'paragraph'
    size: int = 1
    auto_confirm: bool = False


def is_chunk_command(cmd: str) -> bool:
    parts = cmd.split(maxsplit=1)
    return bool(parts) and parts[0] in CHUNK_COMMANDS


def parse_chunk_command(cmd: str) -> ChunkOptions:
    try:
        args = shlex.split(cmd)
    except ValueError as exc:
        raise ChunkCommandError(f'Не удалось разобрать команду: {exc}') from exc

    if not args or args[0] not in CHUNK_COMMANDS:
        raise ChunkCommandError('Ожидалась команда /file_chunk или /filechunk.')

    mode: ChunkMode = 'paragraph'
    size = 1
    seen = False
    auto = False

    for arg in args[1:]:
        if arg == '-y':
            auto = True
            continue

        mode2, size2 = _parse_size_option(arg)
        if seen:
            raise ChunkCommandError('Укажите только один способ деления файла на чанки.')
        mode = mode2
        size = size2
        seen = True

    return ChunkOptions(mode=mode, size=size, auto_confirm=auto)


def split_text(text: str, opts: ChunkOptions) -> list[str]:
    if not text:
        return []
    if opts.mode == 'length':
        return _split_by_length(text, opts.size)
    return _split_by_paragraphs(text, opts.size)


def build_chunk_prompt(prompt: str, chunk: str) -> str:
    return f'{prompt.strip()}\n\nФрагмент:\n{chunk}'


def _parse_size_option(token: str) -> tuple[ChunkMode, int]:
    if token.startswith('paragraph='):
        return 'paragraph', _positive_int(token.removeprefix('paragraph='))
    if token.startswith('len='):
        return 'length', _positive_int(token.removeprefix('len='))
    raise ChunkCommandError(f'Неизвестный параметр команды: {token}')


def _positive_int(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise ChunkCommandError('Размер чанка должен быть целым числом.') from exc
    if value <= 0:
        raise ChunkCommandError('Размер чанка должен быть положительным числом.')
    return value


def _split_by_length(text: str, size: int) -> list[str]:
    return [text[start : start + size] for start in range(0, len(text), size)]


def _split_by_paragraphs(text: str, count: int) -> list[str]:
    pars = [part.strip() for part in re.split(r'\n\s*\n|\n', text) if part.strip()]
    return ['\n'.join(pars[index : index + count]) for index in range(0, len(pars), count)]
