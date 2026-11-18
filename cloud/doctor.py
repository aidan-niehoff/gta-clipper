"""Environment check: can this machine run the clipper?

Run:  python -m cloud.doctor          (prints a report, exit 0 only if all required checks pass)
      python -m cloud.doctor --json   (machine-readable)

Checks three things:
  1. tools     ffmpeg, ffprobe, yt-dlp (required); TwitchDownloaderCLI (needed from phase 4)
  2. python    faster_whisper, yaml, requests
  3. network   Twitch and YouTube hosts answer. Any HTTP status counts as reachable;
               a proxy refusal (403 with x-deny-reason) or connection error counts as blocked.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass

import requests

REQUIRED_TOOLS = ["ffmpeg", "ffprobe", "yt-dlp"]
OPTIONAL_TOOLS = ["TwitchDownloaderCLI"]
REQUIRED_MODULES = ["yaml", "requests"]
OPTIONAL_MODULES = ["faster_whisper"]

# Hosts the clipper talks to. Keep in sync with cloud/ALLOWED_DOMAINS.md.
HOSTS = {
    "twitch site": "https://www.twitch.tv/",
    "twitch api": "https://api.twitch.tv/helix/streams",
    "twitch auth": "https://id.twitch.tv/oauth2/validate",
    "twitch video": "https://usher.ttvnw.net/",
    "youtube site": "https://www.youtube.com/",
    "youtube api": "https://www.googleapis.com/youtube/v3/videos",
    "github api": "https://api.github.com/",
}


@dataclass
class Check:
    kind: str
    name: str
    ok: bool
    required: bool
    detail: str


def check_tool(name: str, required: bool, which=shutil.which, run=subprocess.run) -> Check:
    path = which(name)
    if not path:
        return Check("tool", name, False, required, "not installed")
    flag = "-version" if name in ("ffmpeg", "ffprobe") else "--version"
    try:
        out = run([path, flag], capture_output=True, text=True, timeout=20)
        first = (out.stdout or out.stderr).strip().splitlines()[:1]
        return Check("tool", name, out.returncode == 0, required, first[0] if first else path)
    except Exception as e:  # noqa: BLE001 - report anything
        return Check("tool", name, False, required, f"failed to run: {e}")


def check_module(name: str, required: bool, find=importlib.util.find_spec) -> Check:
    ok = find(name) is not None
    return Check("python", name, ok, required, "importable" if ok else "not installed")


def check_host(label: str, url: str, get=requests.get) -> Check:
    try:
        r = get(url, timeout=15, allow_redirects=False)
    except requests.RequestException as e:
        return Check("network", label, False, True, f"blocked or down: {type(e).__name__}")
    # Proxies report refusals in different headers; treat any of them as blocked.
    deny = r.headers.get("x-deny-reason") or r.headers.get("x-proxy-error")
    if deny:
        return Check("network", label, False, True, f"blocked by proxy: {deny}")
    return Check("network", label, True, True, f"HTTP {r.status_code}")


def run_all(which=shutil.which, run=subprocess.run, find=importlib.util.find_spec, get=requests.get) -> list[Check]:
    checks = [check_tool(t, True, which, run) for t in REQUIRED_TOOLS]
    checks += [check_tool(t, False, which, run) for t in OPTIONAL_TOOLS]
    checks += [check_module(m, True, find) for m in REQUIRED_MODULES]
    checks += [check_module(m, False, find) for m in OPTIONAL_MODULES]
    checks += [check_host(label, url, get) for label, url in HOSTS.items()]
    return checks


def passed(checks: list[Check]) -> bool:
    return all(c.ok for c in checks if c.required)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    checks = run_all()
    if args.json:
        print(json.dumps({"passed": passed(checks), "checks": [asdict(c) for c in checks]}, indent=2))
    else:
        for c in checks:
            mark = "PASS" if c.ok else ("FAIL" if c.required else "warn")
            print(f"[{mark}] {c.kind:<8} {c.name:<22} {c.detail}")
        print("\nRESULT:", "ready" if passed(checks) else "NOT ready")
    return 0 if passed(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
