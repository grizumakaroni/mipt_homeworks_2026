from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

from .chunks import (
    ChunkCommandError,
    build_chunk_prompt,
    is_chunk_command,
    parse_chunk_command,
    split_text,
)
from .config import AppConfig, ConfigError, load_config
from .files import FileMentionError, expand_file_mentions, read_text_file
from .history import ChatHistory
from .llm import LLMError, OpenAIChatClient, StreamingChat
from .models import Message


EXIT = r'\q'
RESET = '/reset'


def run_app() -> int:
    try:
        cfg = load_config()
    except ConfigError as exc:
        print(f'Ошибка конфигурации: {exc}')
        return 1

    hist = ChatHistory(
        limit_message=cfg.limit_message,
        limit_chars=cfg.limit_chars,
    )
    bot = OpenAIChatClient(
        api_key=cfg.api_key,
        api_host=cfg.api_host,
        model=cfg.model,
        temperature=cfg.temperature,
    )

    print('GigaVibeMiptCode готов. Для выхода введите \\q.')
    while True:
        line = input('>>> ').strip()
        if line == EXIT:
            return 0
        if not line:
            continue
        if line == RESET:
            hist.clear()
            clear_screen()
            print('История очищена.')
            continue
        if is_chunk_command(line):
            process_file_chunks(line, cfg, bot)
            continue

        answer_chat_message(
            line=line,
            cfg=cfg,
            hist=hist,
            bot=bot,
            root=Path.cwd(),
            out=_write,
        )


def answer_chat_message(
    line: str,
    cfg: AppConfig,
    hist: ChatHistory,
    bot: StreamingChat,
    root: Path,
    out: Callable[[str], None],
) -> bool:
    try:
        text = expand_file_mentions(line, base_dir=root)
    except FileMentionError as exc:
        out(f'Ошибка файла: {exc}\n')
        return False

    hist.add('user', text)
    msgs = build_conversation(cfg, hist.messages)
    out('Ассистент: ')
    try:
        reply = render_stream(bot, msgs, out)
    except KeyboardInterrupt:
        out('\nЗапрос прерван. Можно ввести уточненное сообщение.\n')
        return False
    except LLMError as exc:
        out(f'\nОшибка LLM: {exc}\n')
        return False

    out('\n')
    if reply:
        hist.add('assistant', reply)
    return True


def build_conversation(cfg: AppConfig, hist: Sequence[Message]) -> list[Message]:
    msgs = list(hist)
    if cfg.system_prompt is None:
        return msgs
    return [Message(role='system', content=cfg.system_prompt), *msgs]


def render_stream(
    bot: StreamingChat,
    msgs: Sequence[Message],
    out: Callable[[str], None],
) -> str:
    parts: list[str] = []
    for part in bot.stream_chat(msgs):
        out(part)
        parts.append(part)
    return ''.join(parts)


def process_file_chunks(cmd: str, cfg: AppConfig, bot: StreamingChat) -> None:
    try:
        opts = parse_chunk_command(cmd)
    except ChunkCommandError as exc:
        print(f'Ошибка команды: {exc}')
        return

    path = Path(input('Введите путь до файла\n>>> ').strip()).expanduser()
    try:
        text = read_text_file(path)
    except FileMentionError as exc:
        print(f'Ошибка файла: {exc}')
        return

    prompt = input('Что нужно сделать для каждого фрагмента?\n>>> ').strip()
    if not prompt:
        print('Пустой prompt не подходит для обработки файла.')
        return

    chunks = split_text(text, opts)
    if not chunks:
        print('Файл пуст, нечего обрабатывать.')
        return

    print('Принято. Начинаю обработку:')
    for num, chunk in enumerate(chunks):
        ok = _process_one_chunk(num, chunk, prompt, cfg, bot)
        if not ok:
            return
        if not opts.auto_confirm and num != len(chunks) - 1:
            action = input('Нажмите Enter для следующего фрагмента или \\q для выхода\n>>> ')
            if action.strip() == EXIT:
                print('Обработка файла остановлена.')
                return

    print('Обработка файла завершена.')


def _process_one_chunk(
    num: int,
    chunk: str,
    prompt: str,
    cfg: AppConfig,
    bot: StreamingChat,
) -> bool:
    msg = Message(role='user', content=build_chunk_prompt(prompt, chunk))
    msgs = build_conversation(cfg, [msg])
    print(f'\nФрагмент {num + 1}:')
    try:
        render_stream(bot, msgs, _write)
    except KeyboardInterrupt:
        print('\nЗапрос прерван. Возврат в основной чат.')
        return False
    except LLMError as exc:
        print(f'\nОшибка LLM: {exc}')
    print()
    return True


def clear_screen() -> None:
    print('\033c', end='')


def _write(text: str) -> None:
    print(text, end='', flush=True)
