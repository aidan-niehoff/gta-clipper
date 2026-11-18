"""Load and validate config/streamers.yaml.

Fails loudly with a readable message, so a typo in the config shows up in CI
instead of as a silent missed stream.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATH = ROOT / "config" / "streamers.yaml"

PLATFORMS = {"twitch", "youtube"}
TWITCH_LOGIN_RE = re.compile(r"^[a-z0-9_]{3,25}$")
YOUTUBE_HANDLE_RE = re.compile(r"^@[A-Za-z0-9._-]{3,30}$")
SLUG_RE = re.compile(r"^[a-z0-9-]+$")


class ConfigError(ValueError):
    """The config file is missing a field or has a bad value."""


@dataclass(frozen=True)
class Channel:
    platform: str  # "twitch" | "youtube"
    id: str        # twitch login, or youtube @handle

    @property
    def url(self) -> str:
        if self.platform == "twitch":
            return f"https://www.twitch.tv/{self.id}"
        return f"https://www.youtube.com/{self.id}"


@dataclass(frozen=True)
class Streamer:
    name: str
    slug: str
    primary: Channel
    backup: Channel | None
    game_source: str  # "twitch" | "twitch:<login>" | "title"

    @property
    def game_twitch_login(self) -> str | None:
        """The Twitch channel whose category log decides 'was this GTA 6'."""
        if self.game_source == "twitch":
            return self.primary.id
        if self.game_source.startswith("twitch:"):
            return self.game_source.split(":", 1)[1]
        return None


@dataclass(frozen=True)
class TargetGame:
    twitch_categories: tuple[str, ...]
    title_keywords: tuple[str, ...]

    def matches_category(self, category: str | None) -> bool:
        if not category:
            return False
        return category.strip().lower() in {c.lower() for c in self.twitch_categories}

    def matches_title(self, title: str | None) -> bool:
        if not title:
            return False
        t = title.lower()
        return any(k.lower() in t for k in self.title_keywords)


@dataclass(frozen=True)
class StreamersConfig:
    streamers: tuple[Streamer, ...]
    target_game: TargetGame
    by_slug: dict = field(default_factory=dict, compare=False)


def _channel(raw, where: str) -> Channel:
    if not isinstance(raw, dict):
        raise ConfigError(f"{where}: expected a mapping like {{platform: twitch, login: name}}")
    platform = raw.get("platform")
    if platform not in PLATFORMS:
        raise ConfigError(f"{where}.platform: must be one of {sorted(PLATFORMS)}, got {platform!r}")
    if platform == "twitch":
        login = str(raw.get("login", "")).strip().lower()
        if not TWITCH_LOGIN_RE.match(login):
            raise ConfigError(f"{where}.login: {login!r} is not a valid Twitch login")
        return Channel("twitch", login)
    handle = str(raw.get("handle", "")).strip()
    if not YOUTUBE_HANDLE_RE.match(handle):
        raise ConfigError(f"{where}.handle: {handle!r} must look like @ChannelName")
    return Channel("youtube", handle)


def parse(data) -> StreamersConfig:
    if not isinstance(data, dict):
        raise ConfigError("streamers.yaml: top level must be a mapping")
    raw_list = data.get("streamers")
    if not isinstance(raw_list, list) or not raw_list:
        raise ConfigError("streamers: must be a non-empty list")

    streamers: list[Streamer] = []
    seen: set[str] = set()
    for i, raw in enumerate(raw_list):
        where = f"streamers[{i}]"
        if not isinstance(raw, dict):
            raise ConfigError(f"{where}: expected a mapping")
        name = str(raw.get("name", "")).strip()
        if not name:
            raise ConfigError(f"{where}.name: required")
        slug = str(raw.get("slug", "")).strip()
        if not SLUG_RE.match(slug):
            raise ConfigError(f"{where}.slug: {slug!r} must be lowercase letters, digits and dashes")
        if slug in seen:
            raise ConfigError(f"{where}.slug: duplicate slug {slug!r}")
        seen.add(slug)
        primary = _channel(raw.get("primary"), f"{where}.primary")
        backup = _channel(raw["backup"], f"{where}.backup") if raw.get("backup") else None
        game_source = str(raw.get("game_source", "")).strip()
        if game_source == "twitch":
            if primary.platform != "twitch":
                raise ConfigError(f"{where}.game_source: 'twitch' needs a Twitch primary; use 'twitch:<login>' or 'title'")
        elif game_source.startswith("twitch:"):
            login = game_source.split(":", 1)[1]
            if not TWITCH_LOGIN_RE.match(login):
                raise ConfigError(f"{where}.game_source: {login!r} is not a valid Twitch login")
        elif game_source != "title":
            raise ConfigError(f"{where}.game_source: must be 'twitch', 'twitch:<login>' or 'title'")
        streamers.append(Streamer(name, slug, primary, backup, game_source))

    tg = data.get("target_game") or {}
    cats = tuple(str(c) for c in tg.get("twitch_categories") or ())
    kws = tuple(str(k) for k in tg.get("title_keywords") or ())
    if not cats or not kws:
        raise ConfigError("target_game: needs twitch_categories and title_keywords")

    cfg = StreamersConfig(tuple(streamers), TargetGame(cats, kws))
    cfg.by_slug.update({s.slug: s for s in streamers})
    return cfg


def load(path: Path | str = DEFAULT_PATH) -> StreamersConfig:
    with open(path, encoding="utf-8") as f:
        return parse(yaml.safe_load(f))
