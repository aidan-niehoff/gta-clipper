# Network access for the "clipper" cloud environment

Set **Network access → Custom**, tick **Also include default list of common package managers**, and add these domains. If something still gets blocked, switch to **Full** temporarily and run `python -m cloud.doctor` to see which host failed.

```
twitch.tv
*.twitch.tv
*.ttvnw.net
*.jtvnw.net
*.twitchcdn.net
youtube.com
*.youtube.com
*.googlevideo.com
*.ytimg.com
www.googleapis.com
youtubei.googleapis.com
github.com
api.github.com
uploads.github.com
objects.githubusercontent.com
huggingface.co
*.huggingface.co
*.hf.co
```

Why each group: Twitch API, chat and video; YouTube pages, API and video; GitHub releases (where clips land) and the TwitchDownloader release; Hugging Face for the speech-to-text model download.
