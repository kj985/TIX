"""Loads settings from config.toml (or config.example.toml if that's missing)."""
import tomllib
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class ConfigError(Exception):
    pass


@dataclass
class Project:
    name: str
    keywords: list[str]


@dataclass
class Config:
    path: Path
    is_example: bool
    artist_name: str
    app_id: str
    timezone: str
    currency: str
    port: int
    fallback_project: str | None
    projects: list[Project] = field(default_factory=list)

    @property
    def has_api_credentials(self) -> bool:
        return bool(self.artist_name and self.app_id)

    @property
    def project_names(self) -> list[str]:
        return [p.name for p in self.projects]

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    def today(self) -> date:
        return datetime.now(self.tz).date()


def load_config(base_dir: Path) -> Config:
    path = base_dir / "config.toml"
    is_example = False
    if not path.exists():
        path = base_dir / "config.example.toml"
        is_example = True

    try:
        with open(path, "rb") as f:
            raw = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"There's a typo in {path.name}: {e}") from e

    bit = raw.get("bandsintown", {})
    app = raw.get("app", {})

    projects = []
    for p in raw.get("projects", []):
        name = str(p.get("name", "")).strip()
        if not name:
            raise ConfigError(f"Every [[projects]] entry in {path.name} needs a name.")
        projects.append(Project(name=name, keywords=[str(k) for k in p.get("keywords", [])]))

    fallback = str(raw.get("detection", {}).get("fallback_project", "")).strip() or None
    if fallback and fallback not in [p.name for p in projects]:
        names = ", ".join(p.name for p in projects)
        raise ConfigError(
            f'fallback_project "{fallback}" in {path.name} must exactly match one of the '
            f"[[projects]] names: {names}."
        )

    timezone = str(app.get("timezone", "Australia/Sydney"))
    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError) as e:
        raise ConfigError(f'Unknown timezone "{timezone}" in {path.name}.') from e

    return Config(
        path=path,
        is_example=is_example,
        artist_name=str(bit.get("artist_name", "")).strip(),
        app_id=str(bit.get("app_id", "")).strip(),
        timezone=timezone,
        currency=str(app.get("currency", "AUD")),
        port=int(app.get("port", 5050)),
        fallback_project=fallback,
        projects=projects,
    )
