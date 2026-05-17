from __future__ import annotations

from pathlib import Path

import pytest

from final_project.config import AppConfig, ConfigError, load_config


def test_loads_yaml_config(config_file: Path) -> None:
    config_file.write_text(
        '\n'.join(
            [
                'api_key: yaml-key',
                'api_host: http://localhost:11434/v1/',
                'limit_message: 3',
                'limit_chars: 99',
                'temperature: 0.7',
                'model: qwen',
                'system_prompt: Be useful.',
            ],
        ),
        encoding='utf-8',
    )

    config = load_config(config_file, environ={})

    assert config == AppConfig(
        api_key='yaml-key',
        api_host='http://localhost:11434/v1/',
        limit_message=3,
        limit_chars=99,
        temperature=0.7,
        system_prompt='Be useful.',
        model='qwen',
    )


def test_environment_overrides_yaml(config_file: Path) -> None:
    config_file.write_text(
        'api_key: yaml-key\napi_host: http://yaml\nlimit_message: 10\n',
        encoding='utf-8',
    )

    config = load_config(
        config_file,
        environ={
            'API_KEY': 'env-key',
            'API_HOST': 'http://env',
            'LIMIT_MESSAGE': '5',
        },
    )

    assert config.api_key == 'env-key'
    assert config.api_host == 'http://env'
    assert config.limit_message == 5


def test_requires_config_or_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ConfigError):
        load_config(config_path=tmp_path / 'missing.yaml', environ={})


def test_rejects_invalid_temperature(config_file: Path) -> None:
    config_file.write_text(
        'api_key: key\napi_host: http://localhost\ntemperature: 2\n',
        encoding='utf-8',
    )

    with pytest.raises(ConfigError, match='temperature'):
        load_config(config_file, environ={})


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    return tmp_path / 'config.yaml'
