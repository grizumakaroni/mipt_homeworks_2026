from __future__ import annotations

import re
from pathlib import Path


MAX_FILE_BYTES = 5 * 1024 * 1024
MENTION_RE = re.compile(r'@::(.+?)::')


class FileMentionError(Exception):
    pass


def expand_file_mentions(text: str, base_dir: Path | None = None) -> str:
    root = Path.cwd() if base_dir is None else base_dir

    def replace(match: re.Match[str]) -> str:
        path = _resolve_path(match.group(1), root)
        return f'\n{read_text_file(path)}'

    return MENTION_RE.sub(replace, text)


def read_text_file(path: Path, limit: int = MAX_FILE_BYTES) -> str:
    try:
        stat = path.stat()
    except OSError as exc:
        raise FileMentionError(f'файл {path} не найден или недоступен') from exc

    if not path.is_file():
        raise FileMentionError(f'{path} не является обычным файлом')
    if stat.st_size > limit:
        raise FileMentionError(f'файл {path} больше лимита {limit} байт')

    try:
        return path.read_text(encoding='utf-8')
    except UnicodeDecodeError as exc:
        raise FileMentionError(f'файл {path} не похож на UTF-8 текст') from exc
    except OSError as exc:
        raise FileMentionError(f'не удалось прочитать файл {path}: {exc}') from exc


def _resolve_path(raw: str, base_dir: Path) -> Path:
    text = raw.strip()
    if not text:
        raise FileMentionError('пустой путь в @::...::')

    path = Path(text).expanduser()
    if path.is_absolute():
        return path
    return base_dir / path
