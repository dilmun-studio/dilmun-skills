# transcript-cut

Edit videos by their transcript, not their timeline. Transcribe once (whisperX, word-level), decide cuts as text, execute frame-accurate cuts with ffmpeg. Fully local — no API keys, no accounts. Arabic-first.

```
transcribe.py video.mp4 --language ar   # → transcripts/video.words.json
pack_transcript.py transcripts/video.words.json   # → video.packed.md (phrases + time ranges)
# mark keep/drop → cuts.json {"keep": [[s,e],...]}
cut.py video.mp4 cuts.json out.mp4 --margin 0.15
```

Requirements: `whisperx` (`uv tool install whisperx`) and `ffmpeg` on PATH. CPU is enough (`int8`).

Built by **دلمون (Dilmun)**, the team behind [Iraq Work Community](https://iqworkcommunity.com/?utm_source=github&utm_medium=readme&utm_campaign=transcript-cut) — the transcript-as-edit-surface idea exists in commercial tools (Descript) and key-gated skills (browser-use/video-use requires ElevenLabs); this is an independent key-free implementation. MIT licensed.
