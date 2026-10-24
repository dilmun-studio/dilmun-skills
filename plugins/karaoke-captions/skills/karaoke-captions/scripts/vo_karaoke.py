#!/usr/bin/env python3
"""Dilmun karaoke-captions — VO + word-timed karaoke captions in one pass.

edge-tts streams WordBoundary events WHILE synthesizing, so word timing is free:
no ASR, no GPU, no API key. Outputs per scene:
  <name>.mp3            voiceover audio
  <name>.words.json     [{text,start,end}] seconds
  <name>.ass            karaoke subtitles (active word highlighted, RTL-safe) — burn: ffmpeg -vf "ass=<name>.ass"
  <name>.captions.json  Remotion-friendly lines [{text,start,end,words:[...]}]

Usage (no permanent install needed):
  uv run --with edge-tts python vo_karaoke.py --text "..." --out DIR --name scene1
  uv run --with edge-tts python vo_karaoke.py --text-file script.txt --voice ar-IQ-BasselNeural --out DIR
"""
import argparse, asyncio, json, re, sys
from pathlib import Path

TICKS = 10_000_000  # edge-tts offsets are 100ns ticks

DEF_VOICE = "ar-IQ-BasselNeural"  # Iraqi male; ar-IQ-RanaNeural female; ar-SA-HamedNeural fallback
MAX_LINE_CHARS = 28               # short lines read better on vertical video
MAX_LINE_WORDS = 4


async def synth(text: str, voice: str, mp3_path: Path, rate: str, pitch: str):
    import edge_tts
    words = []
    kw = {}
    if rate: kw["rate"] = rate
    if pitch: kw["pitch"] = pitch
    try:  # edge-tts >= 7.x defaults to SentenceBoundary; we need per-word events
        com = edge_tts.Communicate(text, voice, boundary="WordBoundary", **kw)
    except TypeError:  # older edge-tts (< 7) has no boundary param and emits WordBoundary anyway
        com = edge_tts.Communicate(text, voice, **kw)
    with open(mp3_path, "wb") as f:
        async for chunk in com.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({
                    "text": chunk["text"],
                    "start": chunk["offset"] / TICKS,
                    "end": (chunk["offset"] + chunk["duration"]) / TICKS,
                })
    return words


def group_lines(words):
    """Split word stream into caption lines: break on punctuation, char or word caps."""
    lines, cur = [], []
    for w in words:
        cur.append(w)
        chars = sum(len(x["text"]) + 1 for x in cur)
        endp = re.search(r"[.!؟?،,؛:]$", w["text"])
        if endp or chars >= MAX_LINE_CHARS or len(cur) >= MAX_LINE_WORDS:
            lines.append(cur); cur = []
    if cur:
        lines.append(cur)
    return [{
        "text": " ".join(w["text"] for w in ln),
        "start": ln[0]["start"],
        "end": ln[-1]["end"],
        "words": ln,
    } for ln in lines]


def fmt_ass_time(sec: float) -> str:
    h = int(sec // 3600); m = int(sec % 3600 // 60); s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def to_ass(lines, play_res=(1080, 1920)) -> str:
    """Karaoke ASS: one event per word, active word recolored; RTL-safe word order."""
    w, h = play_res
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Karaoke,Segoe UI,72,&H00FFFFFF,&H0000D7FF,&H00101010,&H96000000,-1,0,0,0,100,100,0,0,1,4,2,2,60,60,220,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    # RTL-safe karaoke: \k tags split the line into bidi runs that libass lays out in
    # logical order (reversing Arabic word order). Instead we emit ONE event per word:
    # the full line each time, with only the active word recolored. Any override tag
    # still splits runs, so for RTL lines the words are written in REVERSED logical
    # order — runs then concatenate left-to-right into the correct visual RTL reading.
    HI, WHITE = "{\\c&H00D7FF&}", "{\\c&HFFFFFF&}"  # gold highlight / base
    evs = []
    for ln in lines:
        rtl = bool(re.search(r"[؀-ۿ]", ln["text"]))
        n = len(ln["words"])
        for i, wd in enumerate(ln["words"]):
            start = wd["start"] if i else ln["start"]
            end = ln["words"][i + 1]["start"] if i + 1 < n else ln["end"] + 0.15
            order = range(n - 1, -1, -1) if rtl else range(n)
            # tag EVERY word so each is its own bidi run — runs concatenate LTR, and the
            # reversed logical order then yields stable, correct visual RTL on every event
            txt = " ".join(
                (HI if j == i else WHITE) + ln["words"][j]["text"]
                for j in order)
            evs.append(f"Dialogue: 0,{fmt_ass_time(start)},{fmt_ass_time(end)},Karaoke,,0,0,0,,{txt}")
    return head + "\n".join(evs) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text")
    ap.add_argument("--text-file")
    ap.add_argument("--voice", default=DEF_VOICE)
    ap.add_argument("--rate", default="")     # e.g. +8%
    ap.add_argument("--pitch", default="")    # e.g. -2Hz
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="vo")
    ap.add_argument("--res", default="1080x1920")
    a = ap.parse_args()

    text = a.text or Path(a.text_file).read_text(encoding="utf-8")
    if not text.strip():
        sys.exit("empty text")
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    res = tuple(int(x) for x in a.res.lower().split("x"))

    mp3 = out / f"{a.name}.mp3"
    words = asyncio.run(synth(text, a.voice, mp3, a.rate, a.pitch))
    if not words:
        sys.exit("edge-tts returned no WordBoundary events")
    # edge-tts can end the stream early yet leave a playable mp3 (seen in practice:
    # 2 of 30 words). A short word stream is a failure, not a result — retry upstream.
    if len(words) < 0.6 * len(text.split()):
        sys.exit(f"edge-tts truncated stream: {len(words)}/{len(text.split())} words — rerun")

    lines = group_lines(words)
    (out / f"{a.name}.words.json").write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / f"{a.name}.captions.json").write_text(json.dumps(lines, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / f"{a.name}.ass").write_text(to_ass(lines, res), encoding="utf-8-sig")
    print(f"OK {mp3.name}: {len(words)} words, {len(lines)} caption lines, "
          f"{words[-1]['end']:.2f}s. Burn: ffmpeg -i video.mp4 -vf \"ass={a.name}.ass\" out.mp4")


if __name__ == "__main__":
    main()
