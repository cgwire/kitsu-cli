"""Test config management."""

import os
from pathlib import Path
from unittest.mock import patch

from kitsu_cli.config import load_config, save_config, get_host, get_token, store_credentials, clear_credentials


def test_load_empty_config(tmp_path):
    with patch("kitsu_cli.config.CONFIG_FILE", tmp_path / "config.toml"):
        assert load_config() == {}


def test_save_and_load_config(tmp_path):
    config_file = tmp_path / "config.toml"
    with patch("kitsu_cli.config.CONFIG_FILE", config_file), \
         patch("kitsu_cli.config.CONFIG_DIR", tmp_path):
        save_config({"host": "http://localhost", "token": "abc123"})
        cfg = load_config()
        assert cfg["host"] == "http://localhost"
        assert cfg["token"] == "abc123"
        # Check file permissions
        assert oct(config_file.stat().st_mode)[-3:] == "600"


def test_get_host_priority(tmp_path):
    config_file = tmp_path / "config.toml"
    with patch("kitsu_cli.config.CONFIG_FILE", config_file), \
         patch("kitsu_cli.config.CONFIG_DIR", tmp_path):
        save_config({"host": "http://from-config"})

        # CLI flag takes precedence
        assert get_host("http://from-cli") == "http://from-cli"

        # Env var next
        with patch.dict(os.environ, {"KITSU_HOST": "http://from-env"}):
            assert get_host() == "http://from-env"

        # Config file fallback
        assert get_host() == "http://from-config"


def test_get_token_priority(tmp_path):
    config_file = tmp_path / "config.toml"
    with patch("kitsu_cli.config.CONFIG_FILE", config_file), \
         patch("kitsu_cli.config.CONFIG_DIR", tmp_path):
        save_config({"token": "config-token"})
        assert get_token("cli-token") == "cli-token"

        with patch.dict(os.environ, {"KITSU_TOKEN": "env-token"}):
            assert get_token() == "env-token"

        assert get_token() == "config-token"


def test_store_and_clear_credentials(tmp_path):
    config_file = tmp_path / "config.toml"
    with patch("kitsu_cli.config.CONFIG_FILE", config_file), \
         patch("kitsu_cli.config.CONFIG_DIR", tmp_path):
        store_credentials("http://localhost", "my-token")
        cfg = load_config()
        assert cfg["token"] == "my-token"

        clear_credentials()
        cfg = load_config()
        assert "token" not in cfg
        assert cfg["host"] == "http://localhost"
