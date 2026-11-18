import copy

import pytest

from checker import config
from checker.config import ConfigError

VALID = {
    "streamers": [
        {"name": "A", "slug": "a", "primary": {"platform": "twitch", "login": "alpha_1"}, "game_source": "twitch"},
        {
            "name": "B",
            "slug": "b",
            "primary": {"platform": "youtube", "handle": "@BeeLive"},
            "backup": {"platform": "twitch", "login": "bee"},
            "game_source": "twitch:bee",
        },
        {"name": "C", "slug": "c", "primary": {"platform": "youtube", "handle": "@Cee"}, "game_source": "title"},
    ],
    "target_game": {"twitch_categories": ["Grand Theft Auto VI"], "title_keywords": ["gta 6", "gta vi"]},
}


def bad(mutator):
    d = copy.deepcopy(VALID)
    mutator(d)
    return d


def test_repo_config_is_valid():
    cfg = config.load()
    slugs = [s.slug for s in cfg.streamers]
    assert slugs == ["kai-cenat", "ishowspeed", "jynxzi", "caseoh"]


def test_repo_config_platform_choices():
    cfg = config.load()
    kai = cfg.by_slug["kai-cenat"]
    assert kai.primary.platform == "youtube" and kai.backup.id == "kaicenat"
    assert kai.game_twitch_login == "kaicenat"
    assert cfg.by_slug["ishowspeed"].game_twitch_login is None
    assert cfg.by_slug["caseoh"].primary.url == "https://www.twitch.tv/caseoh_"
    assert cfg.by_slug["jynxzi"].game_twitch_login == "jynxzi"


def test_parse_valid():
    cfg = config.parse(VALID)
    assert len(cfg.streamers) == 3
    assert cfg.by_slug["b"].primary.url == "https://www.youtube.com/@BeeLive"


def test_twitch_login_is_lowercased():
    d = bad(lambda d: d["streamers"][0]["primary"].update(login="Alpha_1"))
    assert config.parse(d).streamers[0].primary.id == "alpha_1"


@pytest.mark.parametrize(
    "mutator,needle",
    [
        (lambda d: d.update(streamers=[]), "non-empty"),
        (lambda d: d["streamers"][0].update(name=""), "name"),
        (lambda d: d["streamers"][0].update(slug="Bad Slug"), "slug"),
        (lambda d: d["streamers"][1].update(slug="a"), "duplicate"),
        (lambda d: d["streamers"][0]["primary"].update(platform="kick"), "platform"),
        (lambda d: d["streamers"][0]["primary"].update(login="no spaces"), "Twitch login"),
        (lambda d: d["streamers"][1]["primary"].update(handle="BeeLive"), "@ChannelName"),
        (lambda d: d["streamers"][1].update(game_source="twitch"), "Twitch primary"),
        (lambda d: d["streamers"][1].update(game_source="twitch:Bad Login"), "valid Twitch login"),
        (lambda d: d["streamers"][2].update(game_source="vibes"), "game_source"),
        (lambda d: d.update(target_game={}), "target_game"),
    ],
)
def test_parse_rejects(mutator, needle):
    with pytest.raises(ConfigError, match=needle):
        config.parse(bad(mutator))


@pytest.mark.parametrize(
    "title,expected",
    [
        ("GTA 6 DAY 3 | police chases all night", True),
        ("first time playing gta vi!!", True),
        ("GTA6 RP", True),
        ("Grand Theft Auto VI with the boys", True),
        ("GTA 5 RP", False),
        ("Fortnite then gta later?", False),
        ("", False),
        (None, False),
    ],
)
def test_title_matching(title, expected):
    assert config.load().target_game.matches_title(title) is expected


@pytest.mark.parametrize(
    "category,expected",
    [("Grand Theft Auto VI", True), ("grand theft auto vi ", True), ("Grand Theft Auto V", False), (None, False)],
)
def test_category_matching(category, expected):
    assert config.load().target_game.matches_category(category) is expected
