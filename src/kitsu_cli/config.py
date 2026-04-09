"""Configuration file management (~/.config/kitsu-cli/config.toml)."""

import os
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[no-redef]

import tomli_w

CONFIG_DIR = Path(os.environ.get("KITSU_CONFIG_DIR", "~/.config/kitsu-cli")).expanduser()
CONFIG_FILE = CONFIG_DIR / "config.toml"


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    return tomllib.loads(CONFIG_FILE.read_text())


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_bytes(tomli_w.dumps(config).encode())
    CONFIG_FILE.chmod(0o600)


def get_host(cli_host: str | None = None) -> str | None:
    if cli_host:
        return cli_host
    env = os.environ.get("KITSU_HOST")
    if env:
        return env
    cfg = load_config()
    return cfg.get("host")


def get_token(cli_token: str | None = None) -> str | None:
    if cli_token:
        return cli_token
    env = os.environ.get("KITSU_TOKEN")
    if env:
        return env
    cfg = load_config()
    return cfg.get("token")


def store_credentials(host: str, token: str) -> None:
    cfg = load_config()
    cfg["host"] = host
    cfg["token"] = token
    save_config(cfg)


def clear_credentials() -> None:
    cfg = load_config()
    cfg.pop("token", None)
    save_config(cfg)
