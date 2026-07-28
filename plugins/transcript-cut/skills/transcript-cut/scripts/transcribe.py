#!/usr/bin/env python
"""transcribe.py — word-level transcription via whisperX CLI (local, key-free).

Usage: python transcribe.py <media> [--language ar] [--model small] [--outdir transcripts]
Output: <outdir>/<name>.words.json  ->  {"words": [{"word","start","end"}...], "language": "..."}
"""
import argparse, json, subprocess, sys, tempfile
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("media")
    p.add_argument("--language", default=None, help="e.g. ar — skip auto-detect")
    p.add_argument("--model", default="small")
    p.add_argument("--outdir", default="transcripts")
    a = p.parse_args()

    media = Path(a.media)
    outdir = Path(a.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        cmd = [
            "whisperx", str(media),
            "--model", a.model,
            "--compute_type", "int8",          # CPU-safe
            "--output_format", "json",
            "--output_dir", td,
        ]
        if a.language:
            cmd += ["--language", a.language]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            sys.stderr.write(r.stderr[-2000:])
            sys.exit(f"whisperx failed (exit {r.returncode})")

        src = next(Path(td).glob("*.json"), None)
        if not src:
            sys.exit("whisperx produced no JSON output")
        data = json.loads(src.read_text(encoding="utf-8"))

    words = []
    for seg in data.get("segments", []):
        for w in seg.get("words", []):
            if "start" in w and "end" in w:
                words.append({"word": w["word"].strip(), "start": round(w["start"], 3), "end": round(w["end"], 3)})

    out = outdir / f"{media.stem}.words.json"
    out.write_text(json.dumps({"language": data.get("language"), "words": words},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    total = words[-1]["end"] - words[0]["start"] if words else 0.0
    print(f"OK words={len(words)} span={total:.1f}s -> {out}")


if __name__ == "__main__":
    main()
