# -*- coding: utf-8 -*-
"""Bundle each client page into one self-contained .html that needs no network.

The published pages are fragments: the Artifact host wraps them in a document
and they pull Inter from Google Fonts and their diagrams from `assets/`. An
offline copy has to carry all three itself.

What this does, per page:
  * wraps the fragment in a real document, with the same small reset the host
    applies (margin, viewport, safe-area padding, img max-width);
  * drops the Google Fonts <link> and embeds Inter instead, subset to the
    characters the page actually uses — four weights come to about 40 KB;
  * inlines every `assets/*.svg` as a real <svg> element rather than an <img>;
  * adds a light / dark / match-my-device switch.

The switch is offline-only on purpose. On claude.ai the host stamps `data-theme`
on the root element itself when a viewer picks a theme, so a second control
setting the same attribute would fight it. With no host there is nothing to
follow, which is exactly when a reader needs the choice.

That last one matters more than it looks. An <img> is an isolated document and
cannot reach the page's @font-face, so the diagrams would fall back to whatever
sans the reader has — and their text is positioned by hand against Inter's
metrics, so a wider fallback overflows the boxes it was measured into.

    python3 docs/client/_tools/build_offline.py
"""
from __future__ import annotations

import base64
import io
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CLIENT = os.path.dirname(HERE)
OUT = os.path.join(CLIENT, "offline")

PAGES = ["architecture.html", "overview.html", "flow.html"]

# Inter ships as static OTFs on this machine; 650 in the CSS resolves to the
# nearest of these. JetBrains Mono is not installed, so the monospace role
# keeps its declared fallback stack — it is only used for small labels.
FONT_DIR = "/usr/share/fonts/opentype/inter"
WEIGHTS = {400: "Inter-Regular.otf", 500: "Inter-Medium.otf",
           600: "Inter-SemiBold.otf", 700: "Inter-Bold.otf"}

RESET = (
    ':root[data-theme="light"]{color-scheme:light}'
    ':root[data-theme="dark"]{color-scheme:dark}'
    ":root{color-scheme:light dark;"
    "padding-top:env(safe-area-inset-top,0px);"
    "padding-bottom:env(safe-area-inset-bottom,0px)}"
    "body{margin:0}img{max-width:100%}[hidden]{display:none!important}"
    # The inlined diagrams take the sizing the <img> rules used to give them.
    ".fig svg{display:block;width:100%;min-width:700px;max-width:100%;height:auto}"
    ".fig.screen svg{min-width:760px}"
)


# Bottom right rather than top right: flow.html already has a sticky bar with
# links in its top-right corner, and this has to sit in the same place on all
# three pages.
SWITCH_CSS = (
    ".theme-switch{position:fixed;right:16px;"
    "bottom:calc(16px + env(safe-area-inset-bottom,0px));z-index:60;"
    "display:flex;gap:2px;padding:4px;background:var(--surface);"
    "border:1px solid var(--rule);border-radius:999px;"
    "box-shadow:0 6px 20px rgb(0 0 0 / .18)}"
    ".theme-switch button{width:30px;height:30px;padding:0;display:grid;"
    "place-items:center;border:0;border-radius:999px;background:none;"
    "color:var(--ink-soft);cursor:pointer}"
    '.theme-switch button[aria-pressed="true"]{background:var(--accent-soft);'
    "color:var(--accent)}"
    ".theme-switch button:hover{color:var(--ink)}"
    ".theme-switch svg{width:15px;height:15px;fill:none;stroke:currentColor;"
    "stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}"
    "@media print{.theme-switch{display:none}}"
)

_AUTO = ('<circle cx="8" cy="8" r="6"/>'
         '<path d="M8 2a6 6 0 0 1 0 12z" fill="currentColor" stroke="none"/>')
_SUN = ('<circle cx="8" cy="8" r="3.2"/>'
        '<path d="M8 1v1.5M8 13.5V15M15 8h-1.5M2.5 8H1M12.9 3.1l-1 1'
        'M4.1 11.9l-1 1M12.9 12.9l-1-1M4.1 4.1l-1-1"/>')
_MOON = '<path d="M13.4 9.8A5.7 5.7 0 0 1 6.2 2.6a5.7 5.7 0 1 0 7.2 7.2z"/>'


def _btn(mode, label, icon):
    return ('<button type="button" data-mode="%s" aria-pressed="false" '
            'aria-label="%s" title="%s">'
            '<svg viewBox="0 0 16 16" aria-hidden="true">%s</svg></button>'
            % (mode, label, label, icon))


SWITCH_HTML = (
    '<div class="theme-switch" id="theme-switch" role="group" '
    'aria-label="Colour theme">'
    + _btn("auto", "Match my device", _AUTO)
    + _btn("light", "Light", _SUN)
    + _btn("dark", "Dark", _MOON)
    + "</div>"
)

# Runs in <head>, before anything paints, so a saved choice never flashes the
# other theme first.
SWITCH_BOOT = (
    "<script>(function(){try{var t=localStorage.getItem('uniqcai-theme');"
    "if(t==='light'||t==='dark')"
    "document.documentElement.setAttribute('data-theme',t);}catch(e){}})();</script>"
)

SWITCH_JS = """<script>
(function () {
  var KEY = "uniqcai-theme", root = document.documentElement,
      box = document.getElementById("theme-switch");
  if (!box) return;
  var buttons = Array.prototype.slice.call(box.querySelectorAll("button"));
  function apply(mode) {
    if (mode === "dark" || mode === "light") root.setAttribute("data-theme", mode);
    else { root.removeAttribute("data-theme"); mode = "auto"; }
    // file:// can refuse storage outright; the switch still works, it just
    // will not be remembered.
    try {
      if (mode === "auto") localStorage.removeItem(KEY);
      else localStorage.setItem(KEY, mode);
    } catch (e) {}
    buttons.forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-mode") === mode));
    });
  }
  buttons.forEach(function (b) {
    b.addEventListener("click", function () { apply(b.getAttribute("data-mode")); });
  });
  apply(root.getAttribute("data-theme") || "auto");
})();
</script>"""


def read(path):
    return io.open(path, encoding="utf-8").read()


def charset_of(pages):
    """Every character any page or diagram can render, plus plain ASCII."""
    chars = set(chr(c) for c in range(32, 127))
    for p in pages:
        chars |= set(read(os.path.join(CLIENT, p)))
    assets = os.path.join(CLIENT, "assets")
    for root, _dirs, files in os.walk(assets):
        if "_src" in root:
            continue
        for f in files:
            if f.endswith(".svg"):
                chars |= set(read(os.path.join(root, f)))
    return "".join(sorted(chars))


def subset_font(src, text):
    """Subset one OTF to `text` and return it as woff2 bytes."""
    with tempfile.TemporaryDirectory() as tmp:
        txt = os.path.join(tmp, "chars.txt")
        io.open(txt, "w", encoding="utf-8").write(text)
        dst = os.path.join(tmp, "out.woff2")
        subprocess.run(
            [sys.executable, "-m", "fontTools.subset", src,
             "--text-file=" + txt, "--flavor=woff2", "--output-file=" + dst,
             "--layout-features=kern,liga,calt,tnum", "--no-hinting",
             "--desubroutinize", "--drop-tables+=DSIG"],
            check=True, capture_output=True)
        return io.open(dst, "rb").read()


def font_face_css(text):
    out = []
    for weight, name in sorted(WEIGHTS.items()):
        src = os.path.join(FONT_DIR, name)
        if not os.path.exists(src):
            print("  ! missing %s — that weight will fall back" % name)
            continue
        data = subset_font(src, text)
        b64 = base64.b64encode(data).decode("ascii")
        out.append(
            '@font-face{font-family:"Inter";font-style:normal;'
            'font-weight:%d;font-display:swap;'
            'src:url(data:font/woff2;base64,%s) format("woff2")}' % (weight, b64))
        print("  Inter %d -> %5.1f KB" % (weight, len(data) / 1024.0))
    return "".join(out)


IMG = re.compile(r'<img\s+src="(assets/[^"]+\.svg)"\s*\n?\s*alt="([^"]*)"\s*>',
                 re.S)


def inline_svgs(html):
    """Replace <img src="assets/…"> with the file's own <svg> element."""
    count = [0]

    def repl(m):
        path, alt = m.group(1), m.group(2)
        svg = read(os.path.join(CLIENT, path))
        svg = re.sub(r"<\?xml[^>]*\?>\s*", "", svg)
        # Drop the intrinsic size so the CSS above controls it, and carry the
        # alt text over as the accessible name.
        svg = re.sub(r'(<svg\b[^>]*?)\s+width="[\d.]+"\s+height="[\d.]+"',
                     r"\1", svg, count=1)
        svg = re.sub(r'(<svg\b[^>]*?)aria-label="[^"]*"',
                     lambda s: s.group(1) + 'aria-label="%s"' % alt.replace("\n", " "),
                     svg, count=1)
        count[0] += 1
        return svg.strip()

    html = IMG.sub(repl, html)
    return html, count[0]


def build(page, fonts):
    src = read(os.path.join(CLIENT, page))

    # Strip the network font links; the embedded faces replace them.
    src = re.sub(r'<link rel="preconnect"[^>]*>\s*', "", src)
    src = re.sub(r'<link rel="stylesheet"\s+href="https://fonts\.googleapis[^>]*>\s*',
                 "", src)

    src, n = inline_svgs(src)

    # Split at the end of the page's own stylesheet: everything before it
    # belongs in <head>, the markup after it in <body>.
    cut = src.index("</style>") + len("</style>")
    head, body = src[:cut], src[cut:]

    doc = (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, "
        "viewport-fit=cover\">\n"
        "<style>" + RESET + SWITCH_CSS + "</style>\n"
        "<style>" + fonts + "</style>\n"
        + SWITCH_BOOT + "\n"
        + head + "\n</head>\n<body>\n"
        + SWITCH_HTML + "\n" + body.strip() + "\n"
        + SWITCH_JS + "\n</body>\n</html>\n"
    )
    dst = os.path.join(OUT, page)
    io.open(dst, "w", encoding="utf-8").write(doc)
    print("  %-22s %6.0f KB   %d diagram%s inlined"
          % (page, len(doc.encode("utf-8")) / 1024.0, n, "" if n == 1 else "s"))


def main():
    os.makedirs(OUT, exist_ok=True)
    print("subsetting Inter:")
    fonts = font_face_css(charset_of(PAGES))
    print("bundling:")
    for p in PAGES:
        build(p, fonts)
    print("\nwritten to docs/client/offline/ — open any of them with no network.")


if __name__ == "__main__":
    main()
