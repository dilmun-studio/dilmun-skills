#!/usr/bin/env python
"""cut.py — execute word-boundary cuts with ffmpeg (frame-accurate re-encode).

cuts.json: {"keep": [[start, end], ...]}  (seconds, ascending)
Usage: python cut.py <video> <cuts.json> <out> [--margin 0.15] [--crf 18]
"""
import argparse, json, subprocess, sys
from pathlib import Path


def probe_duration(path):
    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("cuts_json")
    p.add_argument("out")
    p.add_argument("--margin", type=float, default=0.15)
    p.add_argument("--crf", type=int, default=18)
    a = p.parse_args()

    duration = probe_duration(a.video)
    keep = json.loads(Path(a.cuts_json).read_text(encoding="utf-8"))["keep"]
    if not keep:
        sys.exit("cuts.json has an empty keep list")

    # apply margins, clamp, and merge overlapping ranges
    spans = sorted([max(0.0, s - a.margin), min(duration, e + a.margin)] for s, e in keep)
    merged = [spans[0]]
    for s, e in spans[1:]:
        if s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])

    has_audio = subprocess.run(
        ["ffprobe", "-v", "quiet", "-select_streams", "a", "-show_entries", "stream=index",
         "-of", "csv=p=0", a.video], capture_output=True, text=True).stdout.strip() != ""

    # concat filter expects inputs INTERLEAVED per segment: [v0][a0][v1][a1]...
    parts, concat_in = [], ""
    for i, (s, e) in enumerate(merged):
        parts.append(f"[0:v]trim=start={s:.3f}:end={e:.3f},setpts=PTS-STARTPTS[v{i}]")
        concat_in += f"[v{i}]"
        if has_audio:
            parts.append(f"[0:a]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS[a{i}]")
            concat_in += f"[a{i}]"
    n = len(merged)
    if has_audio:
        parts.append(f"{concat_in}concat=n={n}:v=1:a=1[outv][outa]")
        maps = ["-map", "[outv]", "-map", "[outa]"]
    else:
        parts.append(f"{concat_in}concat=n={n}:v=1:a=0[outv]")
        maps = ["-map", "[outv]"]

    cmd = ["ffmpeg", "-y", "-i", a.video, "-filter_complex", ";".join(parts), *maps,
           "-c:v", "libx264", "-preset", "veryfast", "-crf", str(a.crf)]
    if has_audio:
        cmd += ["-c:a", "aac", "-b:a", "192k"]
    cmd.append(a.out)

    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-2000:])
        sys.exit(f"ffmpeg failed (exit {r.returncode})")

    kept = sum(e - s for s, e in merged)
    out_dur = probe_duration(a.out)
    print(f"OK segments={n} kept={kept:.1f}s of {duration:.1f}s -> {a.out} ({out_dur:.1f}s)")


if __name__ == "__main__":
    main()
