from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import yaml


CONFIG_FILENAME = 'config.yaml'
DEFAULT_LIMIT_CHARS = 12_000
DEFAULT_LIMIT_MESSAGE = 20
DEFAULT_MODEL = 'gemma3:270m'
DEFAULT_TEMPERATURE = 0.2

ENV_OVERRIDES: dict[str, tuple[str, ...]] = {
    'api_key': ('API_KEY',),
    'api_host': ('API_HOST',),
    'limit_message': ('LIMIT_MESSAGE', 'LIMIT_MESSAGES'),
    'limit_chars': ('LIMIT_CHARS',),
    'temperature': ('TEMPERATURE',),
    'system_prompt': ('SYSTEM_PROMPT',),
    'model': ('MODEL', 'LLM_MODEL'),
}


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class AppConfig:
    api_key: str
    api_host: str
    limit_message: int | None = DEFAULT_LIMIT_MESSAGE
    limit_chars: int | None = DEFAULT_LIMIT_CHARS
    temperature: float = DEFAULT_TEMPERATURE
    system_prompt: str | None = None
    model: str = DEFAULT_MODEL


def load_config(
    config_path: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> AppConfig:
    env = os.environ if environ is None else environ
    path = _find_config_path(config_path)
    data = _load_yaml(path) if path is not None else {}
    has_env = _has_config_env(env)

    if path is None and not has_env:
        msg = (
            'Не найден config.yaml и не заданы переменные окружения. '
            'Создайте config.yaml или экспортируйте API_KEY/API_HOST.'
        )
        raise ConfigError(msg)

    raw = _default_values()
    raw.update(data)
    raw.update(_read_env_overrides(env))
    return _parse_config(raw)


def _default_values() -> dict[str, object]:
    return {
        'limit_message': DEFAULT_LIMIT_MESSAGE,
        'limit_chars': DEFAULT_LIMIT_CHARS,
        'temperature': DEFAULT_TEMPERATURE,
        'model': DEFAULT_MODEL,
        'system_prompt': None,
    }


def _find_config_path(path: Path | None) -> Path | None:
    if path is not None:
        return path if path.exists() else None

    candidates = (
        Path.cwd() / CONFIG_FILENAME,
        Path(__file__).resolve().with_name(CONFIG_FILENAME),
    )
    for item in candidates:
        if item.exists():
            return item
    return None


def _load_yaml(path: Path) -> dict[str, object]:
    try:
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
    except OSError as exc:
        raise ConfigError(f'Не удалось прочитать {path}: {exc}') from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f'Некорректный YAML в {path}: {exc}') from exc

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError('config.yaml должен содержать YAML-словарь настроек.')
    return {str(key): value for key, value in data.items()}


def _has_config_env(environ: Mapping[str, str]) -> bool:
    return any(env_name in environ for aliases in ENV_OVERRIDES.values() for env_name in aliases)


def _read_env_overrides(environ: Mapping[str, str]) -> dict[str, object]:
    vals: dict[str, object] = {}
    for setting, aliases in ENV_OVERRIDES.items():
        value = _first_env(environ, aliases)
        if value is not None:
            vals[setting] = value
    return vals


def _first_env(environ: Mapping[str, str], aliases: tuple[str, ...]) -> str | None:
    for alias in aliases:
        value = environ.get(alias)
        if value is not None:
            return value
    return None


def _parse_config(raw: Mapping[str, object]) -> AppConfig:
    api_key = _required_string(raw.get('api_key'), 'api_key/API_KEY')
    api_host = _required_string(raw.get('api_host'), 'api_host/API_HOST')
    model = _string_with_default(raw.get('model'), DEFAULT_MODEL)
    system_prompt = _optional_string(raw.get('system_prompt'), None)

    return AppConfig(
        api_key=api_key,
        api_host=api_host,
        limit_message=_optional_positive_int(raw.get('limit_message'), 'limit_message'),
        limit_chars=_optional_positive_int(raw.get('limit_chars'), 'limit_chars'),
        temperature=_temperature(raw.get('temperature')),
        system_prompt=system_prompt,
        model=model,
    )


def _required_string(value: object, name: str) -> str:
    text = _optional_string(value, None)
    if text is None:
        raise ConfigError(f'Обязательная настройка {name} не задана.')
    return text


def _string_with_default(value: object, default: str) -> str:
    text = _optional_string(value, default)
    return default if text is None else text


def _optional_string(value: object, default: str | None) -> str | None:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _optional_positive_int(value: object, name: str) -> int | None:
    if value in (None, ''):
        return None
    try:
        parsed = int(str(value))
    except ValueError as exc:
        raise ConfigError(f'{name} должен быть целым числом.') from exc
    if parsed <= 0:
        raise ConfigError(f'{name} должен быть положительным числом.')
    return parsed


def _temperature(value: object) -> float:
    if value in (None, ''):
        return DEFAULT_TEMPERATURE
    try:
        parsed = float(str(value))
    except ValueError as exc:
        raise ConfigError('temperature должен быть числом от 0 до 1.') from exc
    if not 0 <= parsed <= 1:
        raise ConfigError('temperature должен быть числом от 0 до 1.')
    return parsed
