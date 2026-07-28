---
name: transcript-cut
description: This skill should be used when editing raw talking-video or voice-over footage by its transcript — cutting filler words, silences, retakes, and off-script segments at word-boundary precision. Fully local and key-free (whisperX + ffmpeg), Arabic-aware. Triggers: "قص حسب الترانسكربت", "مونتاج بالنص", "transcript cut", "remove fillers", "قص الحشو", "نظف التسجيل".
version: 1.0.0
author: Dilmun (دلمون)
license: MIT
---

# transcript-cut — مونتاج يقوده الترانسكربت، محلي بلا مفاتيح

## Purpose

Edit raw footage (screen recordings, VO takes, talking-head) by reading its transcript instead of scrubbing a timeline: transcribe once with word-level timestamps, decide cuts as text (keep/drop phrases), then execute frame-accurate cuts with ffmpeg. The whole chain is local — whisperX (BSD-2) + ffmpeg — no API keys, no accounts.

## When to use

- Raw take has filler words (آآ، يعني، امم / uh, um), dead air, or repeated retakes.
- A long recording must be tightened to a target duration before Remotion composition.
- The user asks to cut a video "by what was said" rather than by visual timeline.

Do NOT use for videos without speech (use `auto-editor` for pure silence-cutting) or when burned captions are the goal (that is `karaoke-captions`).

## Hard rules

1. **Word-level or nothing.** Always transcribe with whisperX word timestamps (`--language ar` for Arabic). Segment-level SRT loses the sub-second gaps the cuts depend on.
2. **Never cut mid-word.** Cut points snap to word boundaries with a breathing margin (default 0.15s each side).
3. **Ground truth stays with the user.** whisper mishears; before cutting, show the packed transcript and get the keep/drop decision approved. Never publish whisper's text as captions — that is karaoke-captions' alignment job.
4. **Retakes: keep the LAST take** of a repeated phrase unless told otherwise (speakers re-record until satisfied).
5. **Re-encode at cut points.** Stream-copy is only keyframe-accurate; word cuts need `-c:v libx264 -preset veryfast -crf 18` (or the project's codec) to be frame-accurate.
6. **QC gate:** after cutting, report kept/total duration and phrase count; spot-check the first and last cut audibly before declaring done.

## Workflow

```
1. transcribe  →  python scripts/transcribe.py <video> [--language ar] [--model small]
                  outputs transcripts/<name>.words.json (word-level)
2. pack        →  python scripts/pack_transcript.py transcripts/<name>.words.json
                  outputs transcripts/<name>.packed.md — one phrase per line:
                  [12.40-15.82] النص هنا…   (phrases break on silence ≥0.5s)
3. decide      →  read the packed file; build cuts JSON: {"keep": [[start,end],…]}
                  drop fillers/retakes/dead-air; present the decision to the user
4. cut         →  python scripts/cut.py <video> <cuts.json> <out.mp4> [--margin 0.15]
5. QC          →  report durations; play first/last boundary
```

All scripts live in `scripts/` beside this file and print machine-readable summaries.

## Environment

- `whisperx` on PATH (installed via `uv tool install whisperx`) — CPU works (`--compute_type int8`).
- `ffmpeg`/`ffprobe` on PATH.
- Arabic: pass `--language ar` to skip flaky auto-detect; models `tiny`→fast draft, `small`→default, `large-v3`→best (slow on CPU).

## Notes

- The transcript-as-edit-surface idea is common in commercial tools (Descript, browser-use/video-use); this skill is Dilmun's independent key-free implementation on whisperX.
- Pairs with: `auto-editor` (pre-pass dead-air trim), `karaoke-captions` (burned captions AFTER the cut), Remotion (composition after tightening).
