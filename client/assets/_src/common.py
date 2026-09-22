"""Shared SVG helpers for the UniQCAI client flow document.

Every colour here is a value from docs/THEME.md. Nothing is invented.
The palette is declared twice inside each SVG so that a file embedded with
<img> still answers the reader's OS light/dark preference.
"""
import os

ROOT = "/media/ai-centre-01/DATA-4TB/SRHU/digitalUpshot-v2/uniqcai-starter/uniqcai"
OUT = os.path.join(ROOT, "docs/client/assets")
SCREENS = os.path.join(OUT, "screens")
os.makedirs(SCREENS, exist_ok=True)

STYLE = """<style>
svg{
 --bg:#ffffff;--app:#fafbfc;--panel:#f4f6f8;--line:#dde2e8;--line2:#c4ccd5;
 --text:#171b21;--muted:#4f5967;--primary:#2a45cc;--soft:#eef3ff;--sidebar:#0d1014;
 --ok:#15803d;--okbg:#dcfce7;--warn:#b45309;--warnbg:#fef3c7;--bad:#b91c1c;--badbg:#fee2e2;
 --info:#0369a1;--infobg:#e0f2fe;--otp:#7c3aed;--otpbg:#ede9fe;--dim:#97a2af;--dash:#c4ccd5;
}
@media (prefers-color-scheme: dark){svg{
 --bg:#171b21;--app:#0d1014;--panel:#262c35;--line:#262c35;--line2:#3a424e;
 --text:#f4f6f8;--muted:#97a2af;--primary:#3d5ce8;--soft:#1d2c69;--sidebar:#080a0d;
 --ok:#4ade80;--okbg:#052e16;--warn:#fbbf24;--warnbg:#451a03;--bad:#f87171;--badbg:#450a0a;
 --info:#38bdf8;--infobg:#082f49;--otp:#a78bfa;--otpbg:#2e1065;--dim:#97a2af;--dash:#3a424e;
}}
text{font-family:Inter,ui-sans-serif,system-ui,"Segoe UI",Roboto,sans-serif;font-size:14px;fill:var(--text)}
.sm{font-size:12.5px;fill:var(--muted)}
.sms{font-size:12.5px;fill:var(--text)}
.h1{font-size:22px;font-weight:600}
.h2{font-size:17px;font-weight:600}
.b{font-weight:500}
.bb{font-weight:600}
.mono{font-family:"JetBrains Mono",ui-monospace,SFMono-Regular,monospace;font-size:12.5px}
.card{fill:var(--bg);stroke:var(--line);stroke-width:1}
.sub{fill:var(--panel);stroke:var(--line);stroke-width:1}
.soft{fill:var(--soft);stroke:none}
.arw{stroke:var(--line2);fill:none;stroke-width:1.5}
.sep{stroke:var(--line);stroke-width:1}
</style>"""

# The same two palettes again, this time as classes rather than on the root.
# Custom properties inherit, so putting `.lt` or `.dk` on a <g> re-themes
# everything drawn inside it — which is how one file shows a screen in both
# themes at once. Class beats element selector, so these win over the `svg{}`
# rule above inside their own subtree, whatever the reader's OS is set to.
SPLIT_STYLE = """<style>
.lt{
 --bg:#ffffff;--app:#fafbfc;--panel:#f4f6f8;--line:#dde2e8;--line2:#c4ccd5;
 --text:#171b21;--muted:#4f5967;--primary:#2a45cc;--soft:#eef3ff;--sidebar:#0d1014;
 --ok:#15803d;--okbg:#dcfce7;--warn:#b45309;--warnbg:#fef3c7;--bad:#b91c1c;--badbg:#fee2e2;
 --info:#0369a1;--infobg:#e0f2fe;--otp:#7c3aed;--otpbg:#ede9fe;--dim:#97a2af;--dash:#c4ccd5;
}
.dk{
 --bg:#171b21;--app:#0d1014;--panel:#262c35;--line:#262c35;--line2:#3a424e;
 --text:#f4f6f8;--muted:#97a2af;--primary:#3d5ce8;--soft:#1d2c69;--sidebar:#080a0d;
 --ok:#4ade80;--okbg:#052e16;--warn:#fbbf24;--warnbg:#451a03;--bad:#f87171;--badbg:#450a0a;
 --info:#38bdf8;--infobg:#082f49;--otp:#a78bfa;--otpbg:#2e1065;--dim:#97a2af;--dash:#3a424e;
}
</style>"""

ARROW_DEF = """<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7"
 markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="var(--line2)"/></marker></defs>"""

PLATFORM = {"Zepto": "#5b21b6", "Blinkit": "#f5c518", "Swiggy Instamart": "#fc8019",
            "Instamart": "#fc8019", "Flipkart Minutes": "#2874f0",
            "FK Minutes": "#2874f0", "BigBasket": "#84c225"}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg(w, h, body, title):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" '
            'height="%d" role="img" aria-label="%s">\n<title>%s</title>\n%s\n%s\n'
            '<rect width="%d" height="%d" fill="var(--app)"/>\n%s\n</svg>\n'
            % (w, h, w, h, esc(title), esc(title), STYLE, ARROW_DEF, w, h, body))


def svg_stack(w, h, body, title, gap=20, labels=("Light", "Dark")):
    """One drawing rendered twice, light above dark.

    Side by side was the obvious idea and it does not work: two half-width
    copies scale the 12.5px interface text under 7px, and splitting one image
    down the middle leaves the dark half nearly empty, because these screens
    carry their content on the left. Stacking keeps both copies full size.

    `body` is reused verbatim, which is only safe because nothing in it defines
    an id — the one id in the file, the arrowhead marker, lives in ARROW_DEF.
    """
    total = h * 2 + gap
    pane = ('<g class="%s"%s><rect width="%d" height="%d" fill="var(--app)"/>%s'
            '<text x="14" y="19" class="sm">%s</text></g>')
    top = pane % ("lt", "", w, h, body, esc(labels[0]))
    bottom = pane % ("dk", ' transform="translate(0,%d)"' % (h + gap), w, h, body,
                     esc(labels[1]))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" '
            'height="%d" role="img" aria-label="%s">\n<title>%s</title>\n%s\n%s\n%s\n'
            '%s%s\n</svg>\n'
            % (w, total, w, total, esc(title), esc(title), STYLE, SPLIT_STYLE,
               ARROW_DEF, top, bottom))


def rect(x, y, w, h, cls="card", r=8, extra=""):
    return ('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" class="%s" %s/>'
            % (x, y, w, h, r, cls, extra))


def fill(x, y, w, h, colour, r=8):
    return '<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"/>' % (x, y, w, h, r, colour)


def txt(x, y, s, cls="", anchor="start", colour=None):
    # An inline style, not a fill attribute: the .sm / .b class rules carry
    # higher specificity than a presentation attribute and would win.
    f = ' style="fill:%s"' % colour if colour else ""
    return ('<text x="%s" y="%s" class="%s" text-anchor="%s"%s>%s</text>'
            % (x, y, cls, anchor, f, esc(s)))


def pw(label, pad=9):
    """Width a pill needs for its label."""
    return int(len(label) * 6.5) + pad * 2


def pill(x, y, label, fg, bg, h=20, pad=9):
    w = pw(label, pad)
    return ('%s%s' % (fill(x, y, w, h, bg, r=10),
                      txt(x + pad, y + h / 2 + 4.5, label, "sm", colour=fg)))


def dot(cx, cy, colour, r=4.5, hollow=False):
    if hollow:
        return ('<circle cx="%s" cy="%s" r="%s" fill="none" stroke="%s" stroke-width="1.5"/>'
                % (cx, cy, r, colour))
    return '<circle cx="%s" cy="%s" r="%s" fill="%s"/>' % (cx, cy, r, colour)


def line(x1, y1, x2, y2, cls="sep", extra=""):
    return '<line x1="%s" y1="%s" x2="%s" y2="%s" class="%s" %s/>' % (x1, y1, x2, y2, cls, extra)


def arrow(x1, y1, x2, y2):
    return '<path d="M%s %s L%s %s" class="arw" marker-end="url(#a)"/>' % (x1, y1, x2, y2)


def check(cx, cy, colour="var(--ok)"):
    return ('<path d="M%s %s l2.6 2.8 L%s %s" fill="none" stroke="%s" stroke-width="1.8" '
            'stroke-linecap="round" stroke-linejoin="round"/>'
            % (cx - 4, cy, cx + 4.5, cy - 4, colour))


def cross(cx, cy, colour="var(--bad)"):
    return ('<path d="M%s %s l7 7 M%s %s l-7 7" stroke="%s" stroke-width="1.8" '
            'stroke-linecap="round"/>' % (cx - 3.5, cy - 3.5, cx + 3.5, cy - 3.5, colour))


def spinner(cx, cy, colour="var(--info)"):
    return ('<path d="M%s %s a5 5 0 1 1 -3.5 1.5" fill="none" stroke="%s" stroke-width="1.8" '
            'stroke-linecap="round"/>' % (cx + 5, cy, colour))


def ring(cx, cy, colour="var(--dim)"):
    return ('<circle cx="%s" cy="%s" r="4.5" fill="none" stroke="%s" stroke-width="1.5"/>'
            % (cx, cy, colour))


def mail(cx, cy, colour="var(--otp)"):
    return ('<g stroke="%s" stroke-width="1.5" fill="none"><rect x="%s" y="%s" width="12" '
            'height="9" rx="1.5"/><path d="M%s %s l6 4 l6 -4"/></g>'
            % (colour, cx - 6, cy - 4.5, cx - 6, cy - 3.5))


def status_pill(x, y, name):
    """The exact status vocabulary and colours from THEME.md section 5."""
    m = {
        "Queued": ("var(--muted)", "var(--panel)"),
        "Running": ("var(--info)", "var(--infobg)"),
        "Waiting for code": ("var(--otp)", "var(--otpbg)"),
        "Waiting for OTP": ("var(--otp)", "var(--otpbg)"),
        "Succeeded": ("var(--ok)", "var(--okbg)"),
        "Partially succeeded": ("var(--warn)", "var(--warnbg)"),
        "Partial": ("var(--warn)", "var(--warnbg)"),
        "Failed": ("var(--bad)", "var(--badbg)"),
        "Cancelled": ("var(--muted)", "var(--panel)"),
        "Healthy": ("var(--ok)", "var(--okbg)"),
        "Needs attention": ("var(--warn)", "var(--warnbg)"),
        "Untested": ("var(--muted)", "var(--panel)"),
        "Latest": ("var(--ok)", "var(--okbg)"),
        "Columns changed": ("var(--warn)", "var(--warnbg)"),
        "Working today": ("var(--ok)", "var(--okbg)"),
        "In build": ("var(--info)", "var(--infobg)"),
        "Scheduled": ("var(--muted)", "var(--panel)"),
        "On hold": ("var(--warn)", "var(--warnbg)"),
        "Built": ("var(--ok)", "var(--okbg)"),
        "Designed — not yet built": ("var(--warn)", "var(--warnbg)"),
    }
    fg, bg = m[name]
    return pill(x, y, name, fg, bg)


def chip(x, y, platform, suffix=""):
    """PlatformChip: a colour dot plus the platform name, category as a suffix."""
    label = platform + (" · " + suffix if suffix else "")
    w = int(len(label) * 6.4) + 30
    out = [fill(x, y, w, 22, "var(--panel)", r=11),
           dot(x + 11, y + 11, PLATFORM[platform], r=4),
           txt(x + 21, y + 15, label, "sm", colour="var(--text)")]
    return "".join(out), w


def frame(w, h, y0=0):
    """The app window: dark sidebar, content surface."""
    sb = 152
    out = [rect(0, y0, w, h, cls="card", r=12),
           fill(0, y0, sb, h, "var(--sidebar)", r=12),
           fill(sb - 14, y0, 14, h, "var(--sidebar)", r=0)]
    return "".join(out), sb


NAV = ["Overview", "Brands", "Runs", "Schedules", "Report library",
       "— Setup —", "Platform accounts", "Mailboxes", "Users & access",
       "Settings", "Audit log"]


def sidebar(y0, active, items=None, sb=152):
    items = items or NAV
    out = [txt(20, y0 + 34, "UniQCAI", "bb", colour="#ffffff"),
           txt(20, y0 + 50, "by Digital Upshot", "sm", colour="#97a2af")]
    y = y0 + 78
    for it in items:
        if it.startswith("—"):
            out.append(txt(20, y + 12, it.strip("— "), "sm", colour="#6b7684"))
            y += 26
            continue
        if it == active:
            out.append(fill(8, y - 2, sb - 22, 28, "#262c35", r=6))
            out.append(fill(8, y - 2, 3, 28, "#3d5ce8", r=2))
            out.append(txt(22, y + 16, it, "b", colour="#ffffff"))
        else:
            out.append(txt(22, y + 16, it, "", colour="#97a2af"))
        y += 32
    return "".join(out)


def header(y0, sb, w, title, action=None, sub=None):
    out = [txt(sb + 24, y0 + 38, title, "h1")]
    if sub:
        out.append(txt(sb + 24, y0 + 58, sub, "sm"))
    if action:
        bw = pw(action, 14)
        out.append(fill(w - 24 - bw, y0 + 20, bw, 30, "var(--primary)", r=8))
        out.append(txt(w - 24 - bw / 2, y0 + 40, action, "b", anchor="middle", colour="#ffffff"))
    out.append(line(sb, y0 + 72, w, y0 + 72))
    return "".join(out)


def label_badge(w, name):
    """The corner label that says whether a screen exists yet."""
    p = status_pill(0, 0, name)
    width = pw(name)
    return '<g transform="translate(%s,4)">%s</g>' % (w - width - 4, p)


def write(path, content):
    with open(path, "w") as fh:
        fh.write(content)
    print("wrote", os.path.relpath(path, ROOT), len(content), "bytes")
