#!/usr/bin/env python
"""pack_transcript.py — words JSON -> human-readable phrase lines for cut decisions.

Phrases break on inter-word silence >= --gap (default 0.5s) OR on sentence-ending
punctuation (. ؟ ! ?) — continuous TTS-like speech has no silences, punctuation still splits it.
Usage: python pack_transcript.py <name>.words.json [--gap 0.5]
Output: <name>.packed.md next to the input — lines like:  [12.40-15.82] النص هنا
"""
import argparse, json
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("words_json")
    p.add_argument("--gap", type=float, default=0.5)
    a = p.parse_args()

    src = Path(a.words_json)
    words = json.loads(src.read_text(encoding="utf-8"))["words"]

    phrases, cur = [], []
    for w in words:
        if cur and w["start"] - cur[-1]["end"] >= a.gap:
            phrases.append(cur)
            cur = []
        cur.append(w)
        if w["word"].rstrip().endswith((".", "؟", "!", "?", "؛")):
            phrases.append(cur)
            cur = []
    if cur:
        phrases.append(cur)

    lines = []
    for ph in phrases:
        text = " ".join(w["word"] for w in ph)
        lines.append(f"[{ph[0]['start']:.2f}-{ph[-1]['end']:.2f}] {text}")

    out = src.with_name(src.name.replace(".words.json", "") + ".packed.md")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"OK phrases={len(phrases)} -> {out}")


if __name__ == "__main__":
    main()
