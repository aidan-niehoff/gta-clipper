# CLAUDE.md — gta-clipper

Handoff notes for Claude Code sessions working in this repo. Read fully before starting.

## What this is

An on-demand clipper for **GTA 6 streams only**:

1. **Checker** (GitHub Actions cron, every 10 min, public repo so minutes are free) notices when a tracked streamer ends a stream that included GTA 6, finds the VOD link, and records a game timeline in `state/streams.json`.
2. **Alert task**: a Claude scheduled task with an **API trigger only**. The checker POSTs to its `/fire` URL with the streamer, GTA 6 minutes and VOD link as `text`. The task pushes a notification to the owner's phone (Claude app) and waits in that session.
3. **Clip skill** `/gta-clip <link>`: the owner says go in that session (or runs it by hand on any YouTube link, e.g. a Sidemen GTA 6 upload). It picks 4 clips + 2 backups and renders them in the cloud.
4. **Output**: a GitHub release per run with the MP4s and a short list (title, original timestamp, why picked).

No Discord. No VPS. No live recording. TikTok upload comes later (not in scope yet).

Plan doc (source of truth for design): https://claude.ai/artifact/NNK2pjmSB7S9bodRAHpa7h

## Owner preferences

- Short, segmented responses. Lead with the answer.
- Never ask for secrets in chat. Owner pastes them into GitHub repo secrets / cloud environment secrets.
- At each phase gate, report what was checked and the result before moving on.
- Owner is on Claude Pro; watch usage.

## Streamers (config/streamers.yaml)

| Streamer | Tracked on | Backup | GTA 6 detection |
| --- | --- | --- | --- |
| Kai Cenat | YouTube @KaiCenatLive (24h+ streams split into <12h parts) | Twitch kaicenat | His Twitch category log (simulcast) |
| IShowSpeed | YouTube @IShowSpeed | — | Stream title keywords; skill confirms from transcript |
| Jynxzi | Twitch jynxzi | YouTube @Jynxzi | Twitch category |
| CaseOh | Twitch caseoh_ | — | Twitch category |

No GTA 6 in a stream → no alert. Mixed streams → alert gives GTA time; clips only from GTA stretches.

## Clip rules (config/rules.yaml, approved)

- Exactly 60 s: ~20 s build-up, peak, ~10 s reaction; snap to sentence breaks; 9:16 with burned captions.
- Signals, strongest first: Twitch viewer clips (most viewed) / YouTube "most replayed"; chat spikes; audio spikes; transcript.
- Wanted: rage moments, yelling, hype reactions; standalone; one clear payoff; streamer's face/voice carries it. **No per-streamer rules.**
- 4 clips per VOD (or per split part) + 2 backups; ≥10 min apart (**exempt if video < 1 hour**); ≤2 per segment.
- Skip: sponsor reads/ads; copyrighted music; dead air/AFK; slurs, nudity, anyone who looks underage; context-dependent moments.
- YouTube uploads have no chat/game log: use most-replayed + audio + transcript; treat whole video as GTA 6.
- Download only what's needed: chat, viewer clips, heatmap, low-bitrate audio first; then only the chosen sections. Never the full VOD.

## Build phases (each has a gate; don't start the next until it's green)

| Phase | Gate |
| --- | --- |
| 0. Repo + cloud environment | CI green; `python -m cloud.doctor` passes inside the "clipper" cloud environment |
| 1. Checker: Twitch | A real Twitch stream end recorded with correct VOD link + GTA 6 minutes within 20 min |
| 2. Checker: YouTube | A real YouTube stream end recorded with VOD link; quota < 1,000 units/day |
| 3. Alert task | Test fire reaches owner's phone < 1 min; then a real GTA 6 stream end does too |
| 4. Signals | On 2 owner-labelled VODs, ≥ half of top-6 shortlisted moments are postable |
| 5. Select + cut + render | ffprobe checks pass; owner signs off on 3 clips |
| 6. Skill + release | End to end from phone on a Twitch VOD, a split Kai part, and a Sidemen video |
| 7. Hardening | E2E green; one week of real alerts, no missed GTA 6 stream |

Testing pyramid: ~70% unit, ~20% integration (recorded cassettes, real ffmpeg on fixtures), ~10% E2E. Every bug becomes a test at the lowest layer.

## Current status

- Phase 0: code pushed (config + validation, rules + validation, `cloud/doctor.py`, `cloud/setup.sh`, `cloud/ALLOWED_DOMAINS.md`, CI). 50 tests passing.
- Phase 0 gate: `python -m cloud.doctor` → RESULT: ready inside "clipper" (all required checks pass; TwitchDownloaderCLI = warn). CI: see latest Actions run.
- Known: the session GitHub proxy returns 403 for repos outside the session's scope, so the TwitchDownloaderCLI download (lay295/TwitchDownloader) is refused. `cloud/setup.sh` now skips it with a warning. **Phase 4 must solve chat download** another way (e.g. yt-dlp Twitch `rechat` subtitles, or direct Twitch GQL) or add that repo to the environment.
- **Next:** phase 1 — owner creates a Twitch app at dev.twitch.tv/console → GitHub repo secrets `TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`.

## Secrets (names only)

`TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`, `YOUTUBE_API_KEY`, `CLAUDE_FIRE_URL`, `CLAUDE_FIRE_TOKEN`.

## Commands

```
pip install -r requirements-dev.txt
pytest                  # unit + integration
python -m cloud.doctor  # environment check
```
