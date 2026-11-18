import copy

import pytest

from clipper import rules
from clipper.rules import RulesError


def test_repo_rules_match_what_was_approved():
    r = rules.load()
    assert r.clip_seconds == 60
    assert r.clips_per_vod == 4 and r.backups == 2
    assert r.min_spacing_minutes == 10 and r.spacing_exempt_under_minutes == 60
    assert r.max_per_segment == 2
    assert r.aspect == "9:16" and r.burn_captions
    assert "rage moments" in r.wanted
    assert any("sponsor" in s for s in r.skip)


@pytest.mark.parametrize(
    "video_minutes,expected_gap_seconds",
    [
        (10, 0),       # short upload: no spacing rule
        (59.9, 0),     # just under an hour: still exempt
        (60, 600),     # an hour: 10-minute rule applies
        (11 * 60, 600),  # long VOD part
    ],
)
def test_spacing_rule_exemption(video_minutes, expected_gap_seconds):
    assert rules.load().spacing_seconds_for(video_minutes * 60) == expected_gap_seconds


def _raw():
    import yaml

    with open(rules.DEFAULT_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.mark.parametrize(
    "mutator,needle",
    [
        (lambda d: d["clip"].update(seconds=5), "clip.seconds"),
        (lambda d: d["clip"].update(seconds="60"), "clip.seconds"),
        (lambda d: d["clip"].update(buildup_seconds=40, aftermath_seconds=30), "less than"),
        (lambda d: d["clip"].update(aspect="4:3"), "aspect"),
        (lambda d: d["selection"].update(clips_per_vod=0), "clips_per_vod"),
        (lambda d: d["selection"].update(max_per_segment=True), "max_per_segment"),
        (lambda d: d.update(chat_signals=[]), "chat_signals"),
        (lambda d: d.clear(), "clip.seconds"),
    ],
)
def test_rules_reject_bad_values(mutator, needle):
    d = copy.deepcopy(_raw())
    mutator(d)
    with pytest.raises(RulesError, match=needle):
        rules.parse(d)
