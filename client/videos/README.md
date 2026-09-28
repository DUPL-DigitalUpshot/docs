# Client videos

Every video is one folder under its type. All folders have the same shape, so a
new video is a copy of `_template/` with its own media and a `video.json`.

```
videos/
  index.html              the /videos/ page, built from catalog.json
  catalog.json            which types exist and which videos to list, in order
  shared/                 watch.css + watch.js, used by every watch page
  _template/              copied by new_video.py for each new video
  _tools/                 recording kit, voice, build, scaffolding
  <type>/                 demo · training · release-notes · …  (kebab-case)
    <name>/               kebab-case, e.g. admin-walkthrough → /videos/<type>/<name>/
      index.html          identical in every folder: never edit, it reads video.json
      video.json          title, summary, card text, footer, chapters (steps)
      video.mp4           720p H.264, AAC narration
      poster.jpg          frame shown before play and on the index card
      captions.en.vtt     subtitles from the narration
      source/
        narration.json    voiceover script: title, s1 … sN, end
        record.py         the storyboard (what is clicked and captioned)
        .work/            recording scratch, git-ignored
```

**Anything the site needs must not start with `_`.** GitHub Pages builds with
Jekyll, which leaves out every `_folder`. That's why `shared/` has no underscore,
and why `_tools/` and `_template/` (which the site doesn't need) stay off the
public site.

The watch page and the index read JSON with `fetch()`, so they work when served
(GitHub Pages, any web server) but not when opened as a `file://` path.

## Add a video

```
cd docs/client/videos/_tools
python3 new_video.py demo brand-team-view "Brand team view"
#   → demo/brand-team-view/ from _template/, and listed in catalog.json
#   A new type works the same way: python3 new_video.py training add-a-mailbox "…" --type-label "Training"
```

Then, in the new folder:

1. `source/narration.json`: one line per step. Keys are `title`, `s1` … `sN`, `end`.
2. `source/record.py`: the storyboard. Each `d.cap(...)` is the next step (`s1`, `s2`, …)
   and starts that narration line. Put `await d.done()` before moving to the next
   screen, so the screen waits for the voice to finish.
3. `video.json`: title, summary, card text and one `steps` entry per narration key.
   Leave `t`, `duration` and `size_mb` alone: `build.py` fills them in.

Then produce it (the app must be running, frontend on :5174):

```
cd docs/client/videos/_tools
KOKORO_DIR=… $VENV/bin/python tts.py   demo/brand-team-view    # voice lines
DEMO_PASSWORD=… python3 ../demo/brand-team-view/source/record.py --shots   # dry pass: screenshots only
DEMO_PASSWORD=… python3 ../demo/brand-team-view/source/record.py           # the take, paced to the voice
python3 build.py demo/brand-team-view                                     # mp4, poster, captions, chapter times
```

Run `tts.py` again whenever the narration changes, then record and build again.
To re-record an existing video, run the last three commands for its folder.

## The kit (`_tools/`)

| File | Does |
|---|---|
| `demo_kit.py` | Browser and capture at 1280×720; `cap`, `card`, `click`, `point`, `type`, `scroll`, `done`, `shot` |
| `overlay.js` | Step caption, highlight ring and cursor, drawn inside the page |
| `tts.py` | Voice with [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx), voice `af_heart`, run locally. Needs `pip install kokoro-onnx soundfile` and the model files `kokoro-v1.0.onnx` and `voices-v1.0.bin` in `KOKORO_DIR` (not committed) |
| `build.py` | Standard library + ffmpeg: mixes the voice at the logged times, encodes, and writes the poster, subtitles and `video.json` times |
| `new_video.py` | Scaffolds a folder and registers it in `catalog.json` |

## Rules

- Storyboards only view screens. Open drawers and cancel them; never save or start
  a run on the live system for a recording.
- Passwords come from `DEMO_PASSWORD` and are never written to a file.
- Unlike the rest of `docs/client/`, which uses invented brand names, these
  recordings show the live console with real brands, logins and mailbox addresses.
  Check every video before publishing it anywhere public.
