# gta-clipper

Turns finished GTA 6 streams into 60-second vertical clips.

1. **Checker** (GitHub Actions, every 10 min) notices when a tracked streamer ends a stream that included GTA 6.
2. **Alert task** (a Claude scheduled task) pushes the VOD link to your phone.
3. **Clip skill** (`/gta-clip <link>`) picks 4 moments + 2 backups and renders them in Claude's cloud.
4. **Clips** land on a GitHub release in this repo.

The skill also works on any YouTube video link, e.g. a Sidemen GTA 6 upload.

## Edit what it tracks

- Streamers: [`config/streamers.yaml`](config/streamers.yaml)
- Clip rules: [`config/rules.yaml`](config/rules.yaml)

## Build status

| Phase | Status |
| --- | --- |
| 0. Repo + cloud environment | in progress |
| 1. Checker: Twitch | |
| 2. Checker: YouTube | |
| 3. Alert task | |
| 4. Signals | |
| 5. Select + cut + render | |
| 6. Skill + release | |
| 7. Hardening | |

## Developing

```
pip install -r requirements-dev.txt
pytest                 # unit + integration
python -m cloud.doctor # can this machine run the clipper?
```

Secrets live in **Settings → Secrets and variables → Actions**. Never commit them.
