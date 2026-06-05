from __future__ import annotations
import os
import pathlib
import tomllib
from dataclasses import dataclass, field
from t212.api.limits import LIVE_URL, DEMO_URL

DEFAULT_CONFIG_PATH = pathlib.Path.home() / ".config" / "t212" / "config.toml"
ENV_VAR = "TRADING212_API_KEY"


class MissingKeyError(Exception):
    pass


@dataclass
class Settings:
    api_key: str = field(repr=False)
    environment: str
    base_url: str
    refresh_seconds: int


def _read_key(path: pathlib.Path, environment: str) -> str | None:
    if not path.exists():
        return None
    data = tomllib.loads(path.read_text())
    section = data.get(environment, {})
    return section.get("api_key")


def save_key(path: pathlib.Path, environment: str, api_key: str) -> None:
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = tomllib.loads(path.read_text()) if path.exists() else {}
    existing.setdefault(environment, {})["api_key"] = api_key
    lines = []
    for env, section in existing.items():
        lines.append(f"[{env}]")
        lines.append(f'api_key = "{section["api_key"]}"')
        lines.append("")
    path.write_text("\n".join(lines))
    path.chmod(0o600)


def resolve_settings(*, environment: str, api_key: str | None = None,
                     refresh: int | None = None,
                     config_path: pathlib.Path = DEFAULT_CONFIG_PATH) -> Settings:
    key = api_key or os.environ.get(ENV_VAR) or _read_key(pathlib.Path(config_path), environment)
    if not key:
        raise MissingKeyError(
            f"No API key. Set {ENV_VAR}, pass --api-key, or run `t212 config set-key`.")
    base = LIVE_URL if environment == "live" else DEMO_URL
    return Settings(api_key=key, environment=environment, base_url=base,
                    refresh_seconds=refresh or 10)
