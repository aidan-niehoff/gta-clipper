"""Load and validate config/rules.yaml (the approved clip rules)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATH = ROOT / "config" / "rules.yaml"


class RulesError(ValueError):
    """rules.yaml is missing a field or has a bad value."""


@dataclass(frozen=True)
class Rules:
    clip_seconds: int
    buildup_seconds: int
    aftermath_seconds: int
    snap_to_sentences: bool
    aspect: str
    burn_captions: bool
    clips_per_vod: int
    backups: int
    min_spacing_minutes: int
    spacing_exempt_under_minutes: int
    max_per_segment: int
    wanted: tuple[str, ...]
    chat_signals: tuple[str, ...]
    skip: tuple[str, ...]

    def spacing_seconds_for(self, video_seconds: float) -> int:
        """Minimum gap between clips for a video of this length.

        Videos shorter than the exemption (e.g. a 40-minute Sidemen upload)
        have no spacing rule beyond 'clips must not overlap'.
        """
        if video_seconds < self.spacing_exempt_under_minutes * 60:
            return 0
        return self.min_spacing_minutes * 60


def _int(section: dict, key: str, where: str, lo: int, hi: int) -> int:
    v = section.get(key)
    if not isinstance(v, int) or isinstance(v, bool) or not lo <= v <= hi:
        raise RulesError(f"{where}.{key}: must be a whole number from {lo} to {hi}, got {v!r}")
    return v


def parse(data) -> Rules:
    if not isinstance(data, dict):
        raise RulesError("rules.yaml: top level must be a mapping")
    clip = data.get("clip") or {}
    sel = data.get("selection") or {}

    r = Rules(
        clip_seconds=_int(clip, "seconds", "clip", 10, 180),
        buildup_seconds=_int(clip, "buildup_seconds", "clip", 0, 120),
        aftermath_seconds=_int(clip, "aftermath_seconds", "clip", 0, 120),
        snap_to_sentences=bool(clip.get("snap_to_sentences", True)),
        aspect=str(clip.get("aspect", "9:16")),
        burn_captions=bool(clip.get("burn_captions", True)),
        clips_per_vod=_int(sel, "clips_per_vod", "selection", 1, 20),
        backups=_int(sel, "backups", "selection", 0, 10),
        min_spacing_minutes=_int(sel, "min_spacing_minutes", "selection", 0, 120),
        spacing_exempt_under_minutes=_int(sel, "spacing_exempt_under_minutes", "selection", 0, 600),
        max_per_segment=_int(sel, "max_per_segment", "selection", 1, 20),
        wanted=tuple(str(x) for x in data.get("wanted") or ()),
        chat_signals=tuple(str(x) for x in data.get("chat_signals") or ()),
        skip=tuple(str(x) for x in data.get("skip") or ()),
    )
    if r.buildup_seconds + r.aftermath_seconds >= r.clip_seconds:
        raise RulesError("clip: buildup_seconds + aftermath_seconds must be less than seconds")
    if r.aspect not in {"9:16", "16:9", "1:1"}:
        raise RulesError(f"clip.aspect: {r.aspect!r} not supported")
    if not r.chat_signals:
        raise RulesError("chat_signals: list at least one")
    return r


def load(path: Path | str = DEFAULT_PATH) -> Rules:
    with open(path, encoding="utf-8") as f:
        return parse(yaml.safe_load(f))
