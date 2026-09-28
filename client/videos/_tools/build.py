"""Publish one video from its recording: stdlib + ffmpeg only.

    python3 build.py demo/admin-walkthrough

Reads  <video>/source/.work/{raw/*.webm, marks.json, narr/*.wav}
Writes <video>/video.mp4       720p H.264, narration mixed at the logged times, AAC
       <video>/poster.jpg
       <video>/captions.en.vtt narration.json split into sentence cues
       <video>/video.json      steps[].t, duration and size refreshed from the take
"""
import json, pathlib, re, subprocess, sys

VIDEOS = pathlib.Path(__file__).resolve().parents[1]
TRIM = 0.4    # the first frames of a Playwright take are blank
VOICE = 0.15  # voice starts just after its caption appears

video = VIDEOS / sys.argv[1]
work = video / "source" / ".work"
raw = sorted((work / "raw").glob("*.webm"))[-1]
marks = json.loads((work / "marks.json").read_text())
durs = json.loads((work / "narr" / "durations.json").read_text())
text = json.loads((video / "source" / "narration.json").read_text())


def probe(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "csv=p=0", str(path)])
    return float(out)


length = probe(raw) - 0.2 - TRIM
inputs, chains = ["-ss", str(TRIM), "-t", f"{length:.3f}", "-i", str(raw)], []
for i, m in enumerate(marks, start=1):
    inputs += ["-i", str(work / "narr" / f"{m['key']}.wav")]
    ms = max(0, int((m["t"] - TRIM + VOICE) * 1000))
    chains.append(f"[{i}:a]adelay={ms}:all=1[a{i}]")
mix = "".join(f"[a{i}]" for i in range(1, len(marks) + 1))
graph = ";".join([
    f"[0:v]fps=30,scale=1280:720:flags=lanczos,fade=t=in:st=0:d=0.6,"
    f"fade=t=out:st={length - 1.0:.2f}:d=0.8,format=yuv420p[v]",
    *chains,
    f"{mix}amix=inputs={len(marks)}:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11,"
    f"aresample=48000,apad,atrim=0:{length:.3f}[a]",
])
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex", graph,
                "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "20",
                "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(video / "video.mp4")],
               check=True)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "2.5", "-i", str(video / "video.mp4"),
                "-frames:v", "1", "-q:v", "3", str(video / "poster.jpg")], check=True)


def ts(t):
    return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{t % 60:06.3f}"


cues = ["WEBVTT", ""]
for m in marks:
    t, d = m["t"] - TRIM + VOICE, durs[m["key"]]
    parts = [p for p in re.split(r"(?<=[.?!])\s+", text[m["key"]]) if p]
    total = sum(map(len, parts))
    for p in parts:
        span = d * len(p) / total
        cues += [f"{ts(t)} --> {ts(t + span)}", p, ""]
        t += span
(video / "captions.en.vtt").write_text("\n".join(cues))

meta_path = video / "video.json"
meta = json.loads(meta_path.read_text())
at = {m["key"]: round(max(0.0, m["t"] - TRIM), 1) for m in marks}
for s in meta.get("steps", []):
    if s.get("key") in at:
        s["t"] = 0 if s.get("intro") else at[s["key"]]
secs = probe(video / "video.mp4")
meta["duration"] = f"{int(secs // 60)} min {round(secs % 60)} s"
meta["size_mb"] = round((video / "video.mp4").stat().st_size / 1e6, 1)
meta_path.write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n")
print(f"{video.name}: {meta['duration']}, {meta['size_mb']} MB, {len(marks)} narration lines")
