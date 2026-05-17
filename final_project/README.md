# GigaVibeMiptCode

## Описание

Простой консольный чат с LLM. Я проверяла на Ollama,
но работает с любым OpenAI-compatible API.

## Реализовано

Чат с историей сообщений
Лимиты истории по числу сообщений и по символам
Настройки из `config.yaml` и из переменных окружения
Streaming-вывод ответа
`Ctrl+C` во время ответа модели отменяет только текущий запрос, можно его уточнить
`@::path/to/file::` добавляет текст файла в сообщение
`/file_chunk` обрабатывает файл кусками
`/reset` чистит историю, `\q` выходит из программы
Потоковый вывод  ответа
Unit тесты, html-отчёт покрытия

## Установка

Из корня репозитория:

```bash
source .venv/bin/activate
uv sync --group lint --group test
```

`ollama` уже добавлен в зависимости. Для локальной модели можно скачать маленькую
`gemma3:270m`:

```bash
ollama pull gemma3:270m
```

## Настройки

Можно создать файл:

```bash
cp final_project/config.example.yaml final_project/config.yaml
```

Пример:

```yaml
api_key: ollama
api_host: http://localhost:11434/v1/
model: gemma3:270m
limit_message: 20
limit_chars: 12000
temperature: 0.2
system_prompt: You are a helpful Python backend assistant.
```

То же самое можно задать через окружение (значения из окружения важнее YAML):

```bash
export API_KEY=ollama
export API_HOST=http://localhost:11434/v1/
export MODEL=gemma3:270m
export LIMIT_MESSAGE=20
export LIMIT_CHARS=12000
export TEMPERATURE=0.2
```

## Запуск

```bash
cd final_project
python main.py
```

## Команды

\q                         выйти
/reset                     начать новый диалог
@::main.py::               подставить файл в сообщение
/file_chunk                обработать файл по абзацам
/filechunk paragraph=3     брать по 3 абзаца
/filechunk len=150 -y      брать по 150 символов и не ждать Enter

## Проверки

```bash
ruff check final_project --config final_project/ruff.toml
mypy final_project
pytest final_project/tests --cov=final_project --cov-report=term-missing --cov-report=html:final_project/coverage_html
```
