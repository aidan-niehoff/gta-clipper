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

echo "== TwitchDownloaderCLI (chat replay downloads)"
if ! command -v TwitchDownloaderCLI >/dev/null 2>&1; then
  url=$(curl -fsSL https://api.github.com/repos/lay295/TwitchDownloader/releases/latest \
        | python3 -c "import json,sys; a=json.load(sys.stdin)['assets']; print(next(x['browser_download_url'] for x in a if 'CLI' in x['name'] and 'Linux-x64' in x['name']))")
  tmp=$(mktemp -d)
  curl -fsSL "$url" -o "$tmp/cli.zip"
  python3 -m zipfile -e "$tmp/cli.zip" "$tmp/out"
  sudo install -m 0755 "$tmp/out/TwitchDownloaderCLI" /usr/local/bin/TwitchDownloaderCLI
  rm -rf "$tmp"
fi

echo "== done"
ffmpeg -version | head -1
yt-dlp --version
