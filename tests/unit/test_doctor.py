import subprocess

import requests

from cloud import doctor


class FakeResp:
    def __init__(self, status=200, headers=None):
        self.status_code = status
        # requests uses case-insensitive headers; mirror that.
        self.headers = requests.structures.CaseInsensitiveDict(headers or {})


def fake_run_ok(args, **kw):
    return subprocess.CompletedProcess(args, 0, stdout=f"{args[0]} version 1.0\n", stderr="")


def test_missing_required_tool_fails():
    c = doctor.check_tool("ffmpeg", True, which=lambda n: None)
    assert not c.ok and c.required and c.detail == "not installed"


def test_tool_reports_version_line():
    c = doctor.check_tool("yt-dlp", True, which=lambda n: "/usr/bin/yt-dlp", run=fake_run_ok)
    assert c.ok and "version 1.0" in c.detail


def test_tool_nonzero_exit_fails():
    def run(args, **kw):
        return subprocess.CompletedProcess(args, 1, stdout="", stderr="boom")

    assert not doctor.check_tool("ffmpeg", True, which=lambda n: "/x/ffmpeg", run=run).ok


def test_any_http_status_counts_as_reachable():
    # The Twitch API answers 401 without a token: that still proves the host is reachable.
    c = doctor.check_host("twitch api", "https://api.twitch.tv/helix/streams", get=lambda *a, **k: FakeResp(401))
    assert c.ok and c.detail == "HTTP 401"


def test_proxy_refusal_counts_as_blocked():
    resp = FakeResp(403, {"x-deny-reason": "host_not_allowed"})
    c = doctor.check_host("youtube site", "https://www.youtube.com/", get=lambda *a, **k: resp)
    assert not c.ok and "host_not_allowed" in c.detail


def test_proxy_error_header_counts_as_blocked():
    # Seen for real: a 403 that looks like Google's but comes from the proxy.
    resp = FakeResp(403, {"X-Proxy-Error": 'request blocked: no rule allows host "www.googleapis.com"'})
    c = doctor.check_host("youtube api", "https://www.googleapis.com/youtube/v3/videos", get=lambda *a, **k: resp)
    assert not c.ok and "no rule allows" in c.detail


def test_connection_error_counts_as_blocked():
    def get(*a, **k):
        raise requests.ConnectionError("nope")

    assert not doctor.check_host("x", "https://x", get=get).ok


def test_optional_failures_do_not_fail_the_run():
    checks = doctor.run_all(
        which=lambda n: None if n == "TwitchDownloaderCLI" else f"/usr/bin/{n}",
        run=fake_run_ok,
        find=lambda m: None if m == "faster_whisper" else object(),
        get=lambda *a, **k: FakeResp(200),
    )
    assert doctor.passed(checks)
    assert any(not c.ok and not c.required for c in checks)


def test_one_blocked_host_fails_the_run():
    def get(url, **k):
        return FakeResp(403, {"x-deny-reason": "host_not_allowed"}) if "googlevideo" in url or "youtube.com" in url else FakeResp(200)

    checks = doctor.run_all(which=lambda n: f"/usr/bin/{n}", run=fake_run_ok, find=lambda m: object(), get=get)
    assert not doctor.passed(checks)
