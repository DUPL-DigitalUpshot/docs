"""Screen previews for the client flow document.

Brand names are deliberately invented placeholders. No real client brand,
login id or inbox from samples/ appears anywhere in these files.
"""
import os
from common import *   # noqa

W = 960
CX = 176                      # content left edge
CW = W - CX - 24              # content width (760)


# --- output settings, overridden by client.py -------------------------------
# The defaults reproduce the documents' own screen previews exactly. client.py
# flips them to draw the same screens with no status badge, split light|dark,
# into a different directory.
BADGE = True        # draw the Built / Designed corner label
MODE = "auto"       # "auto" follows the reader's OS; "stack" shows both themes
OUTDIR = None       # None -> SCREENS
SUFFIX = ""         # appended to the filename


def page(name, h, title, active, body, label, action=None, sub=None,
         nav=None, doc_title=None):
    total_h = h + 30
    fr, sb = frame(W, h, y0=30)
    out = [label_badge(W, label) if BADGE else "", fr, sidebar(30, active, nav),
           header(30, sb, W, title, action, sub), body]
    joined = "".join(out)
    name_ = doc_title or title
    art = (svg_stack(W, total_h, joined, name_) if MODE == "stack"
           else svg(W, total_h, joined, name_))
    write(os.path.join(OUTDIR or SCREENS, name + SUFFIX + ".svg"), art)


def tabs(x, y, items, active):
    out, cx = [], x
    for it in items:
        w = int(len(it) * 7) + 22
        if it == active:
            out.append(txt(cx + 11, y + 4, it, "b"))
            out.append(fill(cx, y + 12, w, 2, "var(--primary)", r=1))
        else:
            out.append(txt(cx + 11, y + 4, it, "", colour="var(--muted)"))
        cx += w
    out.append(line(x, y + 13, x + CW, y + 13))
    return "".join(out)


def table(x, y, w, cols, rows, rowh=34):
    """cols = [(label, width, align)]; rows = [[cell, ...]] where a cell is
    either a string or a callable (x, y, width) -> svg."""
    out = [fill(x, y, w, 30, "var(--panel)", r=6)]
    cx = x + 14
    for lab, cw, al in cols:
        ax = cx + cw - 14 if al == "end" else cx
        out.append(txt(ax, y + 20, lab, "sm b", anchor="end" if al == "end" else "start"))
        cx += cw
    ry = y + 30
    for r in rows:
        cx = x + 14
        for (lab, cw, al), cell in zip(cols, r):
            if callable(cell):
                out.append(cell(cx, ry + rowh / 2, cw))
            elif cell:
                ax = cx + cw - 14 if al == "end" else cx
                out.append(txt(ax, ry + rowh / 2 + 4.5, cell, "sm",
                               anchor="end" if al == "end" else "start"))
            cx += cw
        out.append(line(x, ry + rowh, x + w, ry + rowh))
        ry += rowh
    return "".join(out), ry


def btn(x, y, label, primary=False, w=None):
    w = w or pw(label, 14)
    if primary:
        return (fill(x, y, w, 28, "var(--primary)", r=8)
                + txt(x + w / 2, y + 18, label, "sm b", anchor="middle", colour="#ffffff"), w)
    return (rect(x, y, w, 28, cls="card", r=8)
            + txt(x + w / 2, y + 18, label, "sm b", anchor="middle"), w)


def field(x, y, w, label, value, h=30):
    return (txt(x, y - 6, label, "sm") + rect(x, y, w, h, cls="card", r=6)
            + txt(x + 12, y + h / 2 + 4.5, value, "sm"))


def checkbox(x, y, label, on=True, dim=False):
    c = "var(--primary)" if on else "var(--bg)"
    out = [rect(x, y, 15, 15, cls="card", r=4, extra='style="fill:%s"' % c)]
    if on:
        out.append(check(x + 7.5, y + 8, "#ffffff"))
    out.append(txt(x + 24, y + 12, label, "sm",
                   colour="var(--dim)" if dim else "var(--text)"))
    return "".join(out)


def radio(x, y, label, on=True):
    out = ['<circle cx="%s" cy="%s" r="7" fill="var(--bg)" stroke="%s" stroke-width="1.5"/>'
           % (x + 7, y + 7, "var(--primary)" if on else "var(--line2)")]
    if on:
        out.append(dot(x + 7, y + 7, "var(--primary)", r=3.5))
    out.append(txt(x + 24, y + 12, label, "sm"))
    return "".join(out)


def seg(x, y, items, active):
    out, cx = [rect(x, y, sum(pw(i, 12) for i in items), 28, cls="sub", r=8)], x
    for it in items:
        w = pw(it, 12)
        if it == active:
            out.append(fill(cx + 2, y + 2, w - 4, 24, "var(--bg)", r=6))
        out.append(txt(cx + w / 2, y + 18, it, "sm b" if it == active else "sm",
                       anchor="middle"))
        cx += w
    return "".join(out), cx - x


# ============================================================ 1. Overview
def overview():
    h, y0 = 586, 30
    o = []
    kpis = [("Runs today", "42", ""), ("Success rate, 7 days", "96.4%", ""),
            ("Needs attention", "3", "2 logins, 1 connection"),
            ("Next scheduled", "06:00", "tomorrow, Northwind")]
    x, tw = CX, 181
    for lab, val, sub in kpis:
        o.append(rect(x, y0 + 96, tw, 78))
        o.append(txt(x + 16, y0 + 120, lab, "sm"))
        o.append(txt(x + 16, y0 + 150, val, "h1"))
        if sub:
            o.append(txt(x + 16, y0 + 166, sub, "sm"))
        x += tw + 12
    # health matrix
    o.append(rect(CX, y0 + 188, CW, 184))
    o.append(txt(CX + 16, y0 + 214, "Connection health", "b"))
    o.append(txt(CX + 150, y0 + 214, "A = Ads · S = Sales", "sm"))
    plats = ["Zepto", "Blinkit", "Instamart", "FK Minutes", "BigBasket"]
    px = CX + 190
    for p in plats:
        o.append(txt(px, y0 + 240, p, "sm b"))
        px += 114
    rows = [("Northwind Foods", [("o", "-"), ("o", "o"), ("o", "-"), ("w", "w"), None]),
            ("Saffron Kitchen", [("o", "-"), ("w", "o"), (None, None), (None, None), None]),
            ("Bluepeak Drinks", [(None, None), ("o", "o"), ("o", "-"), ("o", "o"), None])]
    ry = y0 + 268
    for brand, cells in rows:
        o.append(txt(CX + 16, ry + 4, brand, "sm"))
        px = CX + 190
        for cell in cells:
            if cell is None:
                o.append(txt(px, ry + 4, "soon", "sm", colour="var(--dim)"))
                px += 114
                continue
            for i, (kind, ) in enumerate([(cell[0], ), (cell[1], )]):
                lx = px + i * 34
                o.append(txt(lx, ry + 4, "AS"[i], "sm", colour="var(--muted)"))
                c = {"o": "var(--ok)", "w": "var(--warn)", "-": None}.get(kind)
                if kind == "-" or kind is None:
                    o.append(line(lx + 12, ry - 4, lx + 22, ry - 4,
                                  extra='style="stroke:var(--dash)"'))
                else:
                    o.append(dot(lx + 16, ry - 4, c))
            px += 114
        ry += 28
    lx = CX + 16
    for col, lab in (("var(--ok)", "healthy"), ("var(--warn)", "needs attention"),
                     (None, "not connected")):
        if col is None:
            o.append(line(lx, y0 + 348, lx + 10, y0 + 348,
                          extra='style="stroke:var(--dash)"'))
        else:
            o.append(dot(lx + 4, y0 + 348, col))
        o.append(txt(lx + 16, y0 + 352, lab, "sm"))
        lx += 26 + int(len(lab) * 6.6)
    # live now
    o.append(rect(CX, y0 + 384, CW, 86))
    o.append(txt(CX + 16, y0 + 410, "Live now", "b"))
    live = [("#1284", "Northwind Foods · Instamart", "Downloading By city", "01:12", "run"),
            ("#1285", "Saffron Kitchen · Zepto", "Waiting for OTP", "00:21", "otp")]
    ly = y0 + 434
    for rid, who, what, el, kind in live:
        o.append(txt(CX + 16, ly, rid, "mono"))
        o.append(txt(CX + 70, ly, who, "sm"))
        if kind == "otp":
            o.append(mail(CX + 268, ly - 4))
        else:
            o.append(spinner(CX + 268, ly - 4))
        o.append(txt(CX + 286, ly, what, "sm"))
        o.append(txt(CX + CW - 16, ly, el, "mono", anchor="end"))
        ly += 24
    # failures
    o.append(rect(CX, y0 + 482, CW, 74))
    o.append(txt(CX + 16, y0 + 508, "Needs a person", "b"))
    o.append(txt(CX + 16, y0 + 534, "#1279", "mono"))
    o.append(txt(CX + 70, y0 + 534, "Saffron Kitchen · Blinkit Ads", "sm"))
    o.append(status_pill(CX + 260, y0 + 522, "Failed"))
    o.append(txt(CX + 330, y0 + 534, "Wrong password — update the login", "sm"))
    b, bw_ = btn(CX + CW - 16 - 86, y0 + 520, "Open", w=86)
    o.append(b)
    page("overview", h, "Overview", "Overview", "".join(o),
         "Designed — not yet built", action="Run now")


# ======================================================== 2. Brand detail
def brand_detail():
    h, y0 = 500, 30
    o = [tabs(CX, y0 + 100, ["Connections", "Schedules", "Reports", "Runs", "Access"],
              "Connections")]
    b, bw_ = btn(CX + CW - 150, y0 + 128, "+ Connect platform", w=150)
    o.append(b)
    cards = [
        ("Blinkit", [("Ads", "Healthy", "reports@yourcompany.com", "2 reports", "today 06:02"),
                     ("Sales", "Healthy", "same login", "3 reports", "today 06:04")]),
        ("Zepto", [("Ads", "Healthy", "ads@yourcompany.com", "12 reports", "today 06:00"),
                   ("Sales", None, None, None, None)]),
    ]
    y = y0 + 170
    for plat, rows in cards:
        ch = 46 + len(rows) * 40
        o.append(rect(CX, y, CW, ch))
        c, _ = chip(CX + 16, y + 14, plat)
        o.append(c)
        ry = y + 52
        for cat, health, login, reports, last in rows:
            o.append(txt(CX + 16, ry + 22, cat, "sm b"))
            if health is None:
                o.append(line(CX + 78, ry + 18, CX + 90, ry + 18,
                              extra='style="stroke:var(--dash)"'))
                o.append(txt(CX + 98, ry + 22, "Not set up", "sm", colour="var(--muted)"))
                bb, _ = btn(CX + CW - 16 - 112, ry + 4, "+ Add Sales", w=112)
                o.append(bb)
            else:
                o.append(status_pill(CX + 78, ry + 8, health))
                o.append(txt(CX + 188, ry + 22, login, "sm"))
                o.append(txt(CX + 400, ry + 22, reports, "sm"))
                o.append(txt(CX + 490, ry + 22, "last run " + last, "sm"))
                bb, w2 = btn(CX + CW - 16 - 96, ry + 4, "Test login", w=96)
                o.append(bb)
            o.append(line(CX, ry + 40, CX + CW, ry + 40) if cat == "Ads" else "")
            ry += 40
        y += ch + 16
    page("brand-detail", h, "Northwind Foods", "Brands", "".join(o), "Built",
         action="Run now", sub="Connected to 2 platforms · last successful download today 06:04")


# ==================================================== 3. Wizard, step one
def stepper(x, y, active):
    steps = ["Platform & categories", "Login", "Verification", "Reports & test"]
    out, cx = [], x
    for i, s in enumerate(steps):
        done = i < active
        cur = i == active
        col = "var(--ok)" if done else ("var(--primary)" if cur else "var(--line2)")
        out.append('<circle cx="%s" cy="%s" r="11" fill="%s"/>'
                   % (cx + 11, y + 11, col if (done or cur) else "var(--panel)"))
        if done:
            out.append(check(cx + 11, y + 12, "#ffffff"))
        else:
            out.append(txt(cx + 11, y + 16, str(i + 1), "sm b", anchor="middle",
                           colour="#ffffff" if cur else "var(--muted)"))
        out.append(txt(cx + 30, y + 16, s, "sm b" if cur else "sm",
                       colour="var(--text)" if (cur or done) else "var(--muted)"))
        cx += 46 + int(len(s) * 6.6)
        if i < 3:
            out.append(line(cx - 30, y + 11, cx - 10, y + 11,
                            extra='stroke="var(--line2)"'))
    return "".join(out)


def wizard_1():
    h, y0 = 470, 30
    o = [stepper(CX, y0 + 96, 0)]
    o.append(txt(CX, y0 + 158, "Which platform?", "h2"))
    tiles = [("Zepto", True), ("Blinkit", True), ("Instamart", True),
             ("FK Minutes", True), ("BigBasket", False)]
    x = CX
    for name, on in tiles:
        tw = 146
        sel = name == "Blinkit"
        o.append(rect(x, y0 + 176, tw, 74, cls="card",
                      extra='style="stroke:var(--primary);stroke-width:1.5"' if sel else
                      ('opacity="0.55"' if not on else "")))
        o.append(dot(x + 18, y0 + 204, PLATFORM[name], r=6))
        o.append(txt(x + 32, y0 + 209, name, "b"))
        o.append(txt(x + 18, y0 + 232, "Coming soon" if not on else
                     ("Selected" if sel else "Available"), "sm"))
        x += tw + 7
    o.append(txt(CX, y0 + 288, "Which reports do you want from Blinkit?", "h2"))
    o.append(rect(CX, y0 + 304, CW, 86))
    o.append(checkbox(CX + 20, y0 + 326, "Ads — campaign and search reports", True))
    o.append(checkbox(CX + 20, y0 + 358,
                      "Sales — seller reports, exact list to be confirmed with you", True))
    o.append(txt(CX, y0 + 414, "Both use one login, so you only type it once on the next step.", "sm"))
    b, bw_ = btn(CX + CW - 90, y0 + 406, "Continue", True, w=90)
    o.append(b)
    page("wizard-1", h, "Connect a platform", "Brands", "".join(o), "Built")


# ================================================== 4. Wizard, step three
def wizard_3():
    h, y0 = 470, 30
    o = [stepper(CX, y0 + 96, 2)]
    o.append(txt(CX, y0 + 158, "Where do this login's sign-in codes arrive?", "h2"))
    o.append(field(CX, y0 + 190, 340, "Verification inbox",
                   "reports-inbox@yourcompany.com"))
    o.append(txt(CX + 356, y0 + 184, "Direct inbox", "sm b"))
    o.append(txt(CX + 356, y0 + 202, "The portal emails this address itself.", "sm"))
    o.append(txt(CX + 356, y0 + 220, "A forwarded inbox works too — you then", "sm"))
    o.append(txt(CX + 356, y0 + 238, "confirm which address it forwards for.", "sm"))

    o.append(rect(CX, y0 + 256, CW, 130, cls="sub"))
    o.append(txt(CX + 16, y0 + 282, "Which message counts as the code", "b"))
    o.append(txt(CX + 16, y0 + 302, "Supplied for each portal. You can change it, and test it "
                                    "before saving.", "sm"))
    o.append(txt(CX + 16, y0 + 330, "From", "sm"))
    o.append(txt(CX + 70, y0 + 330, "brands@blinkit.com", "mono"))
    o.append(txt(CX + 250, y0 + 330, "Subject contains", "sm"))
    o.append(txt(CX + 358, y0 + 330, "sign in", "mono"))
    o.append(txt(CX + 16, y0 + 354, "Code", "sm"))
    o.append(txt(CX + 70, y0 + 354, "a 6-digit number, or a one-time link", "mono"))
    bb, _ = btn(CX + CW - 16 - 96, y0 + 340, "Test rule", w=96)
    o.append(bb)
    o.append(check(CX + 22, y0 + 376, "var(--ok)"))
    o.append(txt(CX + 36, y0 + 380, "Matched a message received 10:42 · code found",
                 "sm", colour="var(--ok)"))
    b, _ = btn(CX + CW - 90, y0 + 410, "Continue", True, w=90)
    o.append(b)
    bk, _ = btn(CX + CW - 170, y0 + 410, "Back", w=74)
    o.append(bk)
    page("wizard-3", h, "Connect a platform", "Brands", "".join(o), "Built")


# =================================================== 5. Wizard, step four
def wizard_4():
    h, y0 = 500, 30
    o = [stepper(CX, y0 + 96, 3)]
    o.append(txt(CX, y0 + 158, "Reports to collect by default", "h2"))
    o.append(rect(CX, y0 + 174, 360, 150))
    o.append(txt(CX + 16, y0 + 198, "Blinkit · Ads", "sm b"))
    o.append(checkbox(CX + 16, y0 + 210, "MTD search report", True))
    o.append(checkbox(CX + 16, y0 + 238, "Dashboard export", True))
    o.append(txt(CX + 16, y0 + 288, "Blinkit · Sales", "sm b"))
    o.append(checkbox(CX + 16, y0 + 300, "Seller reports — to be confirmed", False, dim=True))

    o.append(rect(CX + 376, y0 + 174, CW - 376, 150, cls="sub"))
    o.append(txt(CX + 392, y0 + 198, "Test sign-in", "b"))
    steps = [("Browser started", "0:02", "ok"),
             ("Opened the Blinkit sign-in page", "0:05", "ok"),
             ("Login entered", "0:07", "ok"),
             ("Waiting for the code in reports-inbox…", "0:19", "otp"),
             ("Signed in", "", "todo"),
             ("Business confirmed", "", "todo")]
    sy = y0 + 220
    for label, el, kind in steps:
        ix = CX + 398
        if kind == "ok":
            o.append(check(ix, sy - 4))
        elif kind == "otp":
            o.append(mail(ix, sy - 4))
        else:
            o.append(ring(ix, sy - 4))
        o.append(txt(ix + 16, sy, label, "sm",
                     colour="var(--muted)" if kind == "todo" else "var(--text)"))
        if el:
            o.append(txt(CX + CW - 16, sy, el, "mono", anchor="end"))
        sy += 17
    o.append(txt(CX, y0 + 348, "Saving is enabled once the test passes. You may save without "
                               "testing — the login is then marked Untested.", "sm"))
    b, _ = btn(CX + CW - 150, y0 + 376, "Save connection", True, w=150)
    o.append(b)
    page("wizard-4", h, "Connect a platform", "Brands", "".join(o), "Built")


# ========================================================= 6. Run now drawer
def run_now():
    h, y0 = 520, 30
    o = [tabs(CX, y0 + 100, ["Connections", "Schedules", "Reports", "Runs", "Access"],
              "Connections")]
    o.append('<rect x="0" y="%s" width="%s" height="%s" rx="12" fill="#0d1014" '
             'opacity="0.42"/>' % (y0, W, h))
    dx, dw = W - 396, 396
    o.append('<path d="M%s %s h%s v%s h-%s z" fill="var(--bg)" stroke="var(--line)"/>'
             % (dx, y0, dw - 12, h, dw - 12))
    o.append(txt(dx + 24, y0 + 44, "Run now", "h1"))
    o.append(txt(dx + 24, y0 + 64, "Northwind Foods", "sm"))
    o.append(line(dx, y0 + 82, W, y0 + 82))

    o.append(txt(dx + 24, y0 + 108, "Reports", "sm b"))
    y = y0 + 122
    tree = [("Zepto", True, ["Sponsored Products — Campaign", "Sponsored Products — Keyword",
                             "Sponsored Brands — Campaign"]),
            ("Blinkit", True, ["MTD search report", "Dashboard export"]),
            ("Swiggy Instamart", False, [])]
    for plat, on, kids in tree:
        o.append(checkbox(dx + 24, y, "", on))
        c, _ = chip(dx + 46, y - 3, plat)
        o.append(c)
        y += 26
        for k in kids:
            o.append(checkbox(dx + 48, y, k, True))
            y += 24
        y += 4
    o.append(txt(dx + 24, y + 8, "Dates", "sm b"))
    s, _ = seg(dx + 24, y + 18, ["Yesterday", "Last 7 days", "This month", "Custom"],
               "Last 7 days")
    o.append(s)
    o.append(txt(dx + 24, y + 70, "14 Sep 2026 → 20 Sep 2026", "sm b"))
    o.append(txt(dx + 200, y + 70, "India Standard Time", "sm"))
    o.append(fill(dx + 24, y + 86, dw - 60, 40, "var(--warnbg)", r=8))
    o.append(txt(dx + 38, y + 111, "Zepto files carry no dates inside them — "
                                   "split by day?", "sm", colour="var(--warn)"))
    b, _ = btn(W - 24 - 112, y0 + h - 48, "Start run", True, w=112)
    o.append(b)
    bc, _ = btn(W - 24 - 190, y0 + h - 48, "Cancel", w=70)
    o.append(bc)
    page("run-now", h, "Northwind Foods", "Brands", "".join(o), "Built", action="Run now")


# ============================================================ 7. Live run
def live_run():
    h, y0 = 540, 30
    o = []
    o.append(txt(CX, y0 + 116, "Manual, started by you · 14–20 Sep 2026", "sm"))
    o.append(status_pill(CX, y0 + 130, "Running"))
    o.append(fill(CX + 90, y0 + 136, 300, 8, "var(--panel)", r=4))
    o.append(fill(CX + 90, y0 + 136, 188, 8, "var(--primary)", r=4))
    o.append(txt(CX + 402, y0 + 144, "5 of 8 reports", "sm"))
    bc, _ = btn(CX + CW - 84, y0 + 128, "Cancel", w=84)
    o.append(bc)

    groups = [
        ("Zepto", "Ads", "done", "2:41", [
            ("Signed in — session reused, no code needed", "", "ok"),
            ("Business confirmed: Northwind Foods", "", "ok"),
            ("Sponsored Products — Campaign", "24 KB", "ok"),
            ("Sponsored Products — Keyword", "310 KB", "warn")]),
        ("Blinkit", "Ads", "run", "1:05", [
            ("Signed in with a code from reports-inbox (0:26)", "", "ok"),
            ("MTD search report", "downloading…", "run"),
            ("Dashboard export", "", "todo")]),
        ("Blinkit", "Sales", "queued", "", [
            ("Same login — waits for Ads to finish", "", "todo")]),
    ]
    y = y0 + 170
    for plat, cat, state, el, rows in groups:
        gh = 44 + len(rows) * 22
        o.append(rect(CX, y, CW, gh))
        c, cw = chip(CX + 16, y + 12, plat, cat)
        o.append(c)
        if state == "done":
            o.append(check(CX + cw + 34, y + 23))
            o.append(txt(CX + cw + 48, y + 27, "done", "sm", colour="var(--ok)"))
        elif state == "run":
            o.append(spinner(CX + cw + 34, y + 23))
            o.append(txt(CX + cw + 48, y + 27, "running", "sm", colour="var(--info)"))
        else:
            o.append(ring(CX + cw + 34, y + 23))
            o.append(txt(CX + cw + 48, y + 27, "queued", "sm", colour="var(--muted)"))
        if el:
            o.append(txt(CX + CW - 16, y + 27, el, "mono", anchor="end"))
        ry = y + 52
        for label, meta, kind in rows:
            ix = CX + 34
            if kind in ("ok", "warn"):
                o.append(check(ix, ry - 4))
            elif kind == "run":
                o.append(spinner(ix, ry - 4))
            else:
                o.append(ring(ix, ry - 4))
            o.append(txt(ix + 16, ry, label, "sm",
                         colour="var(--muted)" if kind == "todo" else "var(--text)"))
            if kind == "warn":
                o.append(status_pill(CX + 420, ry - 14, "Columns changed"))
            if meta:
                o.append(txt(CX + CW - 52, ry, meta, "sm", anchor="end"))
            if kind in ("ok", "warn") and meta:
                o.append(txt(CX + CW - 22, ry, "↓", "sm b", anchor="end",
                             colour="var(--primary)"))
            ry += 22
        y += gh + 12
    o.append(txt(CX, y + 16, "The page updates itself. Nothing here needs refreshing.", "sm"))
    page("live-run", h, "Run #1286 · Northwind Foods", "Runs", "".join(o), "Built")


# ======================================================= 8. Runs history
def runs():
    h, y0 = 470, 30
    o = [rect(CX, y0 + 96, CW, 40, cls="sub")]
    for i, f in enumerate(["Brand: all", "Platform: all", "Status: all", "Trigger: all",
                           "Last 30 days"]):
        o.append(rect(CX + 14 + i * 150, y0 + 104, 138, 24, cls="card", r=6))
        o.append(txt(CX + 26 + i * 150, y0 + 120, f, "sm"))
    cols = [("Run", 60, "s"), ("Brand", 150, "s"), ("Platforms", 150, "s"),
            ("Dates", 130, "s"), ("Status", 130, "s"), ("Files", 60, "end"),
            ("Took", 70, "end")]
    def sp(name):
        return lambda x, y, w: status_pill(x, y - 10, name)
    rows = [
        ["#1286", "Northwind Foods", "Zepto, Blinkit", "14–20 Sep", sp("Running"), "5", "3:46"],
        ["#1285", "Saffron Kitchen", "Zepto", "19 Sep", sp("Succeeded"), "12", "4:02"],
        ["#1284", "Northwind Foods", "Instamart", "01–19 Sep", sp("Partially succeeded"), "6", "7:18"],
        ["#1283", "Bluepeak Drinks", "Blinkit", "19 Sep", sp("Succeeded"), "5", "2:55"],
        ["#1279", "Saffron Kitchen", "Blinkit", "18 Sep", sp("Failed"), "0", "0:48"],
        ["#1278", "Northwind Foods", "Zepto, Blinkit", "18 Sep", sp("Succeeded"), "17", "6:30"],
    ]
    t, ry = table(CX, y0 + 152, CW, cols, rows)
    o.append(t)
    o.append(txt(CX, ry + 26, "Every run keeps its full step-by-step log. Opening a finished "
                              "run shows exactly what it did.", "sm"))
    page("runs", h, "Runs", "Runs", "".join(o), "Built")


# ========================================================== 9. Schedules
def schedules():
    h, y0 = 520, 30
    o = []
    cols = [("Name", 190, "s"), ("Brand", 150, "s"), ("When", 130, "s"),
            ("Dates it pulls", 150, "s"), ("Next run", 140, "end")]
    rows = [["Morning pull", "Northwind Foods", "Daily 06:00", "Last 3 days", "tomorrow 06:00"],
            ["Weekly wrap", "Bluepeak Drinks", "Mon 07:00", "Last 7 days", "Mon 07:00"],
            ["Month end", "Saffron Kitchen", "1st 08:00", "Previous month", "1 Oct 08:00"]]
    t, ry = table(CX, y0 + 96, CW, cols, rows)
    o.append(t)
    o.append(rect(CX, ry + 24, CW, 236))
    o.append(txt(CX + 20, ry + 52, "Morning pull", "h2"))
    o.append(txt(CX + 20, ry + 84, "How often", "sm"))
    s, _ = seg(CX + 20, ry + 94, ["Daily", "Weekly", "Monthly"], "Daily")
    o.append(s)
    o.append(txt(CX + 250, ry + 114, "at 06:00 India Standard Time", "sm"))
    o.append(txt(CX + 20, ry + 152, "Which dates each run should pull", "sm"))
    o.append(radio(CX + 20, ry + 162, "A rolling window", True))
    o.append(rect(CX + 170, ry + 158, 120, 26, cls="card", r=6))
    o.append(txt(CX + 182, ry + 176, "last 3 days", "sm"))
    o.append(radio(CX + 310, ry + 162, "Fixed dates", False))
    o.append(fill(CX + 20, ry + 196, CW - 40, 26, "var(--soft)", r=6))
    o.append(txt(CX + 34, ry + 213, "Next runs: Tue 23 Sep 06:00 pulls 20–22 Sep  ·  "
                                    "Wed 24 Sep 06:00 pulls 21–23 Sep", "sm",
                 colour="var(--primary)"))
    o.append(txt(CX, ry + 286, "The preview spells out the dates each run will ask for, "
                               "which is where most scheduling mistakes show up.", "sm"))
    page("schedules", h, "Schedules", "Schedules", "".join(o), "Built", action="New schedule")


# ===================================================== 10. Report library
def library():
    h, y0 = 500, 30
    o = [tabs(CX, y0 + 100, ["Ads", "Sales"], "Ads")]
    o.append(rect(CX, y0 + 126, CW, 40, cls="sub"))
    for i, f in enumerate(["Brand: Northwind", "Platform: all", "Report: all", "Sep 2026"]):
        o.append(rect(CX + 14 + i * 150, y0 + 134, 138, 24, cls="card", r=6))
        o.append(txt(CX + 26 + i * 150, y0 + 150, f, "sm"))
    o.append(checkbox(CX + 626, y0 + 138, "Latest only", True))
    # The File column has to clear the longest generated filename, or the name
    # — which is the whole point of this screen — runs under the platform chip.
    cols = [("File", 392, "s"), ("Platform", 104, "s"), ("Period", 92, "s"),
            ("Collected", 92, "s"), ("Size", 52, "end"), ("", 28, "end")]

    def pc(plat):
        return lambda x, y, w: chip(x, y - 11, plat)[0]

    def dl(x, y, w):
        return txt(x + w - 14, y + 4.5, "↓", "sm b", anchor="end",
                   colour="var(--primary)")

    rows = [
        ["northwind_zepto_ads_sp-campaign_2026-09-14_2026-09-20.xlsx", pc("Zepto"),
         "14–20 Sep", "today 06:00", "24 KB", dl],
        ["northwind_zepto_ads_sp-keyword_2026-09-14_2026-09-20.xlsx", pc("Zepto"),
         "14–20 Sep", "today 06:00", "310 KB", dl],
        ["northwind_blinkit_ads_mtd-search_2026-09-14_2026-09-20.xlsx", pc("Blinkit"),
         "14–20 Sep", "today 06:02", "88 KB", dl],
        ["northwind_blinkit_ads_dashboard_2026-09-14_2026-09-20.xlsx", pc("Blinkit"),
         "14–20 Sep", "today 06:02", "41 KB", dl],
    ]
    t, ry = table(CX, y0 + 176, CW, cols, rows, rowh=32)
    o.append(t)
    b, _ = btn(CX, ry + 22, "Download 4 files as a zip", w=210)
    o.append(b)
    o.append(txt(CX, ry + 84, "The file you get is exactly what the portal produced. Only the "
                              "name is ours, so the brand,", "sm"))
    o.append(txt(CX, ry + 102, "platform, report and period are readable without opening it.", "sm"))
    page("library", h, "Report library", "Report library", "".join(o), "Built")


# ==================================================== 11. Platform accounts
def accounts():
    h, y0 = 452, 30
    o = []
    cols = [("Login", 224, "s"), ("Platform", 146, "s"), ("Used for", 110, "s"),
            ("Brands", 74, "s"), ("Ads", 96, "s"), ("Sales", 110, "s")]

    def pc(plat):
        return lambda x, y, w: chip(x, y - 11, plat)[0]

    def sp(name):
        return lambda x, y, w: status_pill(x, y - 10, name)

    rows = [
        ["ads@yourcompany.com", pc("Zepto"), "Ads and Sales", "2", sp("Healthy"), sp("Untested")],
        ["reports@yourcompany.com", pc("Blinkit"), "Ads and Sales", "3", sp("Healthy"), sp("Healthy")],
        ["media@agency.example", pc("Instamart"), "Ads only", "3", sp("Needs attention"), None],
    ]
    t, ry = table(CX, y0 + 96, CW, cols, rows, rowh=40)
    o.append(t)
    o.append(rect(CX, ry + 24, CW, 96, cls="sub"))
    o.append(txt(CX + 20, ry + 50, "Passwords are write-only", "b"))
    o.append(txt(CX + 20, ry + 74, "Once saved, a password can be replaced but never read back "
                                   "— not by an administrator,", "sm"))
    o.append(txt(CX + 20, ry + 94, "not through the interface, and not in any log or export.", "sm"))
    o.append(txt(CX + CW - 150, ry + 62, "••••••••", "mono"))
    bb, _ = btn(CX + CW - 150, ry + 72, "Change", w=90)
    o.append(bb)
    page("accounts", h, "Platform logins", "Platform accounts", "".join(o), "Built",
         action="Add a login")


# ========================================================== 12. Mailboxes
def mailboxes():
    h, y0 = 470, 30
    o = [tabs(CX, y0 + 100, ["Inboxes", "Code rules"], "Code rules")]
    o.append(txt(CX, y0 + 154, "Which message counts as a sign-in code", "h2"))
    o.append(field(CX, y0 + 186, 220, "Portal", "Zepto Ads"))
    o.append(txt(CX + 244, y0 + 180, "Applies to", "sm"))
    o.append(radio(CX + 244, y0 + 190, "Every login on this portal", True))
    o.append(radio(CX + 244, y0 + 214, "Just one login", False))
    o.append(rect(CX, y0 + 248, CW, 92, cls="sub"))
    o.append(txt(CX + 16, y0 + 274, "From", "sm"))
    o.append(txt(CX + 70, y0 + 274, "mailer@zeptonow.com", "mono"))
    o.append(txt(CX + 300, y0 + 274, "Subject contains", "sm"))
    o.append(txt(CX + 410, y0 + 274, "OTP", "mono"))
    o.append(txt(CX + 16, y0 + 300, "Code", "sm"))
    o.append(txt(CX + 70, y0 + 300, "the 4 to 8 digits after “otp code is”", "mono"))
    o.append(txt(CX + 16, y0 + 326, "Test against", "sm"))
    o.append(txt(CX + 110, y0 + 326, "the latest messages in reports-inbox", "sm"))
    bb, _ = btn(CX + CW - 16 - 96, y0 + 312, "Test", w=96)
    o.append(bb)
    o.append(fill(CX, y0 + 352, CW, 34, "var(--okbg)", r=8))
    o.append(check(CX + 22, y0 + 370))
    o.append(txt(CX + 38, y0 + 374, "Matched a message received 10:42 · a code was found "
                                    "and read correctly", "sm", colour="var(--ok)"))
    o.append(txt(CX, y0 + 414, "The code itself is never shown here, stored, or written to any "
                               "log.", "sm"))
    b, _ = btn(CX + CW - 80, y0 + 406, "Save", True, w=80)
    o.append(b)
    page("mailboxes", h, "Inboxes and code rules", "Mailboxes", "".join(o), "Built")


# ====================================================== 13. Users & access
def users():
    h, y0 = 452, 30
    o = []
    cols = [("Person", 250, "s"), ("Role", 130, "s"), ("Brands they can see", 380, "s")]

    def grants(items):
        def draw(x, y, w):
            out, cx = [], x
            for brand, level in items:
                lab = "%s · %s" % (brand, level)
                gw = pw(lab, 10)
                col = "var(--soft)" if level == "Manager" else "var(--panel)"
                out.append(fill(cx, y - 11, gw, 22, col, r=11))
                out.append(txt(cx + 10, y + 4, lab, "sm"))
                cx += gw + 8
            return "".join(out)
        return draw

    rows = [
        ["you@digitalupshot.com", "Super admin", "All brands"],
        ["ops@digitalupshot.com", "Admin", "All brands"],
        ["anita@northwind.example", "Member",
         grants([("Northwind Foods", "Manager")])],
        ["ravi@bluepeak.example", "Member",
         grants([("Bluepeak Drinks", "Executive"), ("Saffron Kitchen", "Executive")])],
    ]
    t, ry = table(CX, y0 + 96, CW, cols, rows, rowh=38)
    o.append(t)
    o.append(rect(CX, ry + 24, CW, 118, cls="sub"))
    o.append(txt(CX + 20, ry + 50, "Two levels on a brand", "b"))
    o.append(txt(CX + 20, ry + 76, "Manager", "sm b"))
    o.append(txt(CX + 100, ry + 76, "enters logins, edits schedules, starts runs, "
                                    "downloads everything.", "sm"))
    o.append(txt(CX + 20, ry + 100, "Executive", "sm b"))
    o.append(txt(CX + 100, ry + 100, "sees and downloads reports. Starting a run is a separate "
                                     "tick you grant", "sm"))
    o.append(txt(CX + 100, ry + 118, "per person, and it is off unless you turn it on.", "sm"))
    page("users", h, "People and access", "Users & access", "".join(o), "Built",
         action="Invite someone")


# =========================================================== 14. SPOC home
def spoc():
    h, y0 = 470, 30
    nav = ["Home", "Reports", "Run history"]
    o = []
    s, _ = seg(CX, y0 + 96, ["Ads", "Sales"], "Ads")
    o.append(s)
    cards = [("Zepto", "today", "12 reports", "var(--ok)"),
             ("Blinkit", "today", "2 reports", "var(--ok)"),
             ("Swiggy Instamart", "3 days ago", "7 reports", "var(--warn)")]
    x = CX
    for plat, fresh, n, col in cards:
        o.append(rect(x, y0 + 140, 246, 86))
        c, _ = chip(x + 16, y0 + 160, plat)
        o.append(c)
        o.append(dot(x + 18, y0 + 200, col))
        o.append(txt(x + 32, y0 + 205, fresh, "sm b"))
        o.append(txt(x + 130, y0 + 205, n, "sm"))
        x += 257
    o.append(txt(CX, y0 + 262, "Latest Ads files", "h2"))
    b, bwid = btn(CX + CW - 226, y0 + 246, "Download all latest as a zip", w=226)
    o.append(b)
    cols = [("File", 420, "s"), ("Period", 140, "s"), ("Collected", 140, "s"), ("", 40, "end")]

    def dl(x, y, w):
        return txt(x + w - 14, y + 4.5, "↓", "sm b", anchor="end", colour="var(--primary)")

    rows = [["northwind_zepto_ads_sp-campaign_2026-09-14_2026-09-20.xlsx", "14–20 Sep",
             "today 06:00", dl],
            ["northwind_blinkit_ads_mtd-search_2026-09-14_2026-09-20.xlsx", "14–20 Sep",
             "today 06:02", dl]]
    t, ry = table(CX, y0 + 280, CW, cols, rows, rowh=32)
    o.append(t)
    o.append(txt(CX, ry + 30, "A brand contact sees only their own brand, and only what has "
                              "finished downloading.", "sm"))
    page("spoc", h, "Northwind Foods", "Home", "".join(o),
         "Designed — not yet built", nav=nav, doc_title="Brand contact home",
         sub="Everything we have collected for you · last updated 06:14 today")


ALL = (overview, brand_detail, wizard_1, wizard_3, wizard_4, run_now, live_run,
       runs, schedules, library, accounts, mailboxes, users, spoc)

if __name__ == "__main__":
    for fn in ALL:
        fn()
