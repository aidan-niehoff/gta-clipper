#!/usr/bin/env bash
# Setup script for the "clipper" Claude cloud environment.
# Paste this into the environment's Setup script box. Its result is cached,
# so it does not re-run on every session.
set -euo pipefail

echo "== system packages"
if ! command -v ffmpeg >/dev/null 2>&1; then
  sudo apt-get update -y && sudo apt-get install -y --no-install-recommends ffmpeg
fi

echo "== python packages"
python3 -m pip install --upgrade --break-system-packages \
  yt-dlp faster-whisper pyyaml requests pytest

echo "== TwitchDownloaderCLI (chat replay downloads; optional until phase 4)"
# Best effort: the session's GitHub proxy can refuse third-party repos (403),
# and that must not stop the session from starting. cloud.doctor reports it.
install_twitchdownloader() {
  local url tmp
  url=$(curl -fsSL https://api.github.com/repos/lay295/TwitchDownloader/releases/latest \
        | python3 -c "import json,sys; a=json.load(sys.stdin)['assets']; print(next(x['browser_download_url'] for x in a if 'CLI' in x['name'] and 'Linux-x64' in x['name']))") || return 1
  tmp=$(mktemp -d) || return 1
  curl -fsSL "$url" -o "$tmp/cli.zip" || return 1
  python3 -m zipfile -e "$tmp/cli.zip" "$tmp/out" || return 1
  sudo install -m 0755 "$tmp/out/TwitchDownloaderCLI" /usr/local/bin/TwitchDownloaderCLI || return 1
  rm -rf "$tmp"
}
if ! command -v TwitchDownloaderCLI >/dev/null 2>&1; then
  install_twitchdownloader 2>&1 || echo "WARN: TwitchDownloaderCLI not installed (download refused); continuing"
fi

echo "== done"
ffmpeg -version | head -1
yt-dlp --version
