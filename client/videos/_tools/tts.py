"""Voice lines for one video: <video>/source/narration.json → <video>/source/.work/narr/*.wav

    KOKORO_DIR=/path/to/model  <venv>/bin/python tts.py demo/admin-walkthrough [--voice af_heart]

Uses kokoro-onnx (pip install kokoro-onnx soundfile); KOKORO_DIR holds
kokoro-v1.0.onnx and voices-v1.0.bin (not committed). Runs locally: the text
never leaves the machine.
"""
import argparse, json, os, pathlib
import soundfile as sf
from kokoro_onnx import Kokoro

VIDEOS = pathlib.Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument("video", help="folder under videos/, e.g. demo/admin-walkthrough")
ap.add_argument("--voice", default="af_heart")
ap.add_argument("--speed", type=float, default=1.0)
a = ap.parse_args()

kdir = pathlib.Path(os.environ.get("KOKORO_DIR", pathlib.Path(__file__).parent / "kokoro"))
k = Kokoro(str(kdir / "kokoro-v1.0.onnx"), str(kdir / "voices-v1.0.bin"))
source = VIDEOS / a.video / "source"
out = source / ".work" / "narr"
out.mkdir(parents=True, exist_ok=True)
durs = {}
for key, text in json.loads((source / "narration.json").read_text()).items():
    samples, sr = k.create(text, voice=a.voice, speed=a.speed, lang="en-us")
    sf.write(out / f"{key}.wav", samples, sr)
    durs[key] = round(len(samples) / sr, 2)
    print(f"{key:>6}  {durs[key]:5.2f}s")
(out / "durations.json").write_text(json.dumps(durs, indent=1))
