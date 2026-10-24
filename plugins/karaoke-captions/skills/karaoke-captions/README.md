# karaoke-captions

Arabic-first karaoke captions with word-level timing, generated together with the voiceover. edge-tts reports
each word's start and end while it speaks, so you get exact timing with no speech recognition, no GPU and no
API key. The `.ass` output keeps Arabic words in the correct right-to-left order, which plain libass
karaoke tags get wrong.

```
uv run --with edge-tts python scripts/vo_karaoke.py --text "مرحبا بكم في القناة" --out ./out --name intro
ffmpeg -i video.mp4 -vf "ass=intro.ass" out.mp4      # run from ./out
```

Outputs: `intro.mp3`, `intro.words.json`, `intro.ass`, `intro.captions.json` (for Remotion).
Recorded voice instead? See Path B in `SKILL.md` (faster-whisper on CPU).

Requirements: [uv](https://docs.astral.sh/uv/), `ffmpeg` on PATH for burning, and internet (edge-tts uses
Microsoft Edge's online read-aloud service, which can change without notice). edge-tts is LGPLv3 and is
called as a separate package, not bundled.

Built by **دلمون (Dilmun)**, the team behind [Iraq Work Community](https://iqworkcommunity.com/?utm_source=github&utm_medium=readme&utm_campaign=karaoke-captions). MIT licensed.
