import os
from common import *   # noqa

# ---------------------------------------------------------------- 1. journey
def journey():
    W, H = 1040, 248
    stages = [
        ("1", "Connect once", ["Add the brand, the platform", "login, and the inbox that", "receives its sign-in codes."]),
        ("2", "Ask for reports", ["Press Run now, or set a", "timetable and forget it."]),
        ("3", "UniQCAI collects", ["Signs in, checks it is on the", "right business, downloads", "every report you picked."]),
        ("4", "Files land in one place", ["Stored exactly as the portal", "produced them, with the", "dates on the filename."]),
        ("5", "Your team downloads", ["Filter by brand, platform or", "period. Take one file or", "the whole set as a zip."]),
    ]
    bw, gap, y = 182, 20, 54
    x = 18
    out = [txt(18, 30, "From a new brand to a downloaded report", "h2")]
    for i, (n, title, lines) in enumerate(stages):
        out.append(rect(x, y, bw, 168))
        out.append(fill(x + 16, y + 16, 22, 22, "var(--soft)", r=11))
        out.append(txt(x + 27, y + 31, n, "sm bb", anchor="middle", colour="var(--primary)"))
        out.append(txt(x + 16, y + 62, title, "b"))
        for j, ln in enumerate(lines):
            out.append(txt(x + 16, y + 84 + j * 18, ln, "sm"))
        if i < len(stages) - 1:
            out.append(arrow(x + bw + 4, y + 84, x + bw + gap - 4, y + 84))
        x += bw + gap
    out.append(txt(18, H - 10, "Steps 3 and 4 need nobody at a keyboard. Step 1 happens once per brand and platform.", "sm"))
    return svg(W, H, "".join(out), "The UniQCAI journey in five stages")


# -------------------------------------------------------------- 2. structure
def structure():
    W, H = 1040, 330
    out = [txt(18, 30, "How everything is named", "h2")]

    # --- left panel: platform -> category -> report type -------------------
    out.append(rect(18, 46, 470, 262))
    out.append(txt(38, 74, "What you pick when you ask for reports", "b"))
    out.append(txt(38, 94, "Every screen groups the same way.", "sm"))

    out.append(txt(38, 124, "Platform", "sm b"))
    out.append(txt(152, 124, "Category", "sm b"))
    out.append(txt(254, 124, "Report types", "sm b"))

    c, wc = chip(38, 136, "Blinkit")
    out.append(c)
    out.append(arrow(38 + wc + 4, 147, 148, 147))

    out.append(fill(152, 136, 52, 22, "var(--panel)", r=11))
    out.append(txt(178, 151, "Ads", "sm b", anchor="middle"))
    out.append(fill(152, 168, 52, 22, "var(--panel)", r=11))
    out.append(txt(178, 183, "Sales", "sm b", anchor="middle"))
    out.append(arrow(208, 147, 248, 147))
    out.append(arrow(208, 181, 248, 181))

    for i, r in enumerate(["MTD search report", "Dashboard export"]):
        out.append(txt(254, 149 + i * 19, "\u2022 " + r, "sm"))
    out.append(txt(254, 187, "\u2022 To be confirmed with you", "sm"))

    out.append(txt(38, 226, "You never have to know that Blinkit \u00b7 Sales is really a site called", "sm"))
    out.append(txt(38, 246, "PartnersBiz. Site names appear only in setup details and in error", "sm"))
    out.append(txt(38, 266, "messages, where they help support work out what broke.", "sm"))

    # --- right panel: brand, login, connection ----------------------------
    out.append(rect(506, 46, 516, 262))
    out.append(txt(526, 74, "How a brand is joined to a login", "b"))
    out.append(txt(526, 94, "A login is not owned by a brand. It is connected to one.", "sm"))

    out.append(txt(674, 126, "connection", "sm", anchor="middle"))
    out.append(rect(526, 134, 138, 56, cls="sub"))
    out.append(txt(538, 156, "Brand", "sm"))
    out.append(txt(538, 176, "Northwind Foods", "b"))
    out.append(arrow(668, 162, 694, 162))
    out.append(rect(698, 134, 158, 56, cls="sub"))
    out.append(txt(710, 156, "Platform login", "sm"))
    out.append(txt(710, 176, "one email + password", "sm"))
    out.append(rect(894, 124, 118, 36, cls="sub"))
    out.append(txt(906, 146, "Ads reports", "sm"))
    out.append(rect(894, 170, 118, 36, cls="sub"))
    out.append(txt(906, 192, "Sales reports", "sm"))
    out.append('<path d="M860 162 h16 v-20 h14" class="arw" marker-end="url(#a)"/>')
    out.append('<path d="M860 162 h16 v26 h14" class="arw" marker-end="url(#a)"/>')

    out.append(txt(526, 226, "Two things follow, and both are deliberate:", "sm b"))
    out.append(txt(526, 248, "\u2022  One login can serve several brands \u2014 an agency login is normal.", "sm"))
    out.append(txt(526, 268, "\u2022  One login can serve both Ads and Sales, so you enter it once.", "sm"))
    out.append(txt(526, 292, "Because of the first, every connection records which business it expects.", "sm"))
    return svg(W, H, "".join(out), "Platform, category and report type; brands, logins and connections")


# ----------------------------------------------------------- 3. verification
def verification():
    W, H = 1040, 330
    out = [txt(18, 30, "How UniQCAI gets past a sign-in code", "h2"),
           txt(18, 50, "Most of these portals email a code or a sign-in link instead of "
                       "accepting a password alone.", "sm")]
    y = 74
    boxes = [
        (18, "UniQCAI", ["Opens the portal and", "enters the login."]),
        (278, "The portal", ["Emails a code or a", "one-time sign-in link."]),
        (538, "Your verification inbox", ["An inbox you nominate.", "Nothing else uses it."]),
        (798, "UniQCAI", ["Reads only the matching", "message, and signs in."]),
    ]
    for x, title, lines in boxes:
        out.append(rect(x, y, 224, 104))
        out.append(txt(x + 16, y + 30, title, "b"))
        for j, ln in enumerate(lines):
            out.append(txt(x + 16, y + 56 + j * 18, ln, "sm"))
    for x in (242, 502, 762):
        out.append(arrow(x + 2, y + 52, x + 34, y + 52))
    out.append(mail(732, y + 26))

    out.append(rect(18, 202, 1004, 112, cls="sub"))
    out.append(txt(38, 230, "Four rules stop it ever reading the wrong message", "b"))
    notes = [
        ("Time", ["only messages that arrived", "after we asked for one."]),
        ("Sender and subject", ["must match the rule you can", "see and test on screen."]),
        ("Addressed to us", ["on a shared or forwarded inbox,", "the code must be for this login."]),
        ("One at a time", ["two sign-ins on the same inbox", "never overlap."]),
    ]
    x = 38
    for title, body in notes:
        out.append(txt(x, 258, title, "sm b"))
        for j, ln in enumerate(body):
            out.append(txt(x, 280 + j * 18, ln, "sm"))
        x += 248
    return svg(W, H, "".join(out), "How a one-time sign-in code reaches UniQCAI safely")


# --------------------------------------------------------------- 4. pipeline
def pipeline():
    W, H = 1040, 350
    out = [txt(18, 30, "What happens inside a run", "h2"),
           txt(18, 50, "One run covers one brand. Inside it, each report is a separate job that succeeds or fails on its own.", "sm")]
    y = 76
    steps = [
        ("Queued", ["Waits its turn if that", "login is already busy."], "var(--muted)"),
        ("Signed in", ["Reuses the last session", "if it is still valid —", "no code needed."], "var(--ok)"),
        ("Right business?", ["Reads back which business", "the portal actually opened", "and compares it."], "var(--primary)"),
        ("Downloaded", ["Each report in turn,", "with the dates you asked", "for."], "var(--ok)"),
        ("Stored", ["Byte for byte. Never", "edited, never overwritten."], "var(--ok)"),
    ]
    bw, gap = 180, 21
    x = 18
    for i, (title, lines, colour) in enumerate(steps):
        if i == 2:
            out.append(rect(x, y, bw, 132, cls="soft"))
            out.append(rect(x, y, bw, 132, cls="card",
                            extra='style="fill:none;stroke:var(--primary);stroke-width:1.5"'))
        else:
            out.append(rect(x, y, bw, 132))
        out.append(dot(x + 18, y + 26, colour))
        out.append(txt(x + 32, y + 31, title, "b"))
        for j, ln in enumerate(lines):
            out.append(txt(x + 18, y + 58 + j * 18, ln, "sm"))
        if i < len(steps) - 1:
            out.append(arrow(x + bw + 4, y + 62, x + bw + gap - 3, y + 62))
        x += bw + gap
    # the stop branch off the gate
    gx = 18 + 2 * (bw + gap) + bw / 2
    out.append('<path d="M%s %s v26" class="arw" marker-end="url(#a)"/>' % (gx, y + 134))
    out.append(fill(gx - 118, y + 162, 236, 30, "var(--badbg)", r=8))
    out.append(cross(gx - 100, y + 177))
    out.append(txt(gx - 88, y + 182, "Not your business — stops, downloads nothing", "sm", colour="var(--bad)"))

    out.append(rect(18, 290, 496, 48, cls="sub"))
    out.append(txt(38, 312, "Tries again", "sm b"))
    out.append(txt(38, 330, "A timeout, a slow portal or a changed page: up to two more attempts.", "sm"))
    out.append(rect(526, 290, 496, 48, cls="sub"))
    out.append(txt(546, 312, "Never tries again", "sm b"))
    out.append(txt(546, 330, "A wrong password (locking the account is worse) or the wrong business.", "sm"))
    return svg(W, H, "".join(out), "Inside a run: queue, sign in, verify the business, download, store")


# --------------------------------------------------------------- 5. coverage
def coverage():
    W, H = 760, 348
    out = [txt(18, 30, "Where each platform stands today", "h2")]
    out.append(rect(18, 46, 724, 284))
    out.append(txt(38, 78, "Platform", "sm b"))
    out.append(txt(300, 78, "Ads", "sm b"))
    out.append(txt(510, 78, "Sales", "sm b"))
    out.append(line(18, 92, 742, 92))
    rows = [
        ("Zepto", "Working today", "In build"),
        ("Blinkit", "Scheduled", "Scheduled"),
        ("Swiggy Instamart", "Scheduled", "Scheduled"),
        ("Flipkart Minutes", "Scheduled", "Scheduled"),
        ("BigBasket", "On hold", "On hold"),
    ]
    y = 118
    for name, ads, sales in rows:
        c, _ = chip(38, y - 15, name)
        out.append(c)
        out.append(status_pill(300, y - 14, ads))
        out.append(status_pill(510, y - 14, sales))
        y += 34
    out.append(line(18, y - 22, 742, y - 22))
    out.append(txt(38, y + 2, "BigBasket needs a Google sign-in with two-factor authentication. It is parked until", "sm"))
    out.append(txt(38, y + 20, "you decide whether to pursue it — see the decisions list at the end.", "sm"))
    return svg(W, H, "".join(out), "Platform coverage by category")


# ------------------------------------------------------------------ 6. roles
def roles():
    """Who does what. Two lanes of human work with the automatic part between
    them, so it reads at a glance which half anyone has to turn up for."""
    # No title inside the drawing: the page puts a heading directly above it.
    W, H = 1040, 366
    out = []

    def lane(y, eyebrow, who, steps, bw, gap):
        o = [txt(18, y, eyebrow, "sm b", colour="var(--primary)"),
             txt(18 + 78, y, who, "sm")]
        x = 18
        for i, (title, line) in enumerate(steps):
            o.append(rect(x, y + 12, bw, 78))
            o.append(txt(x + 16, y + 40, title, "b"))
            o.append(txt(x + 16, y + 62, line, "sm"))
            if i < len(steps) - 1:
                o.append(arrow(x + bw + 3, y + 51, x + bw + gap - 3, y + 51))
            x += bw + gap
        return "".join(o)

    out.append(lane(30, "SET UP", "us, once per brand", [
        ("Add the brand", "Its name, and who may see it."),
        ("Connect the platform", "One login, plus its code inbox."),
        ("Pick the reports", "Which exports matter to you."),
        ("Set the timetable", "Daily, weekly, or not at all."),
    ], 237, 18))

    out.append(arrow(520, 126, 520, 150))
    out.append(rect(18, 154, 1004, 62, cls="soft"))
    out.append(txt(520, 182, "UniQCAI signs in, checks it is on your business, and downloads",
                   "b", anchor="middle"))
    out.append(txt(520, 202, "with nobody at a keyboard", "sm", anchor="middle"))
    out.append(arrow(520, 220, 520, 244))

    out.append(lane(264, "USE IT", "your team, any day", [
        ("Open your brand", "Yours, and nothing else."),
        ("See what is new", "How fresh each platform is."),
        ("Download what you need", "One file, or the set as a zip."),
    ], 322, 19))
    return svg(W, H, "".join(out), "Who does what: setup, automatic collection, and use")


write(os.path.join(OUT, "journey.svg"), journey())
write(os.path.join(OUT, "structure.svg"), structure())
write(os.path.join(OUT, "verification.svg"), verification())
write(os.path.join(OUT, "pipeline.svg"), pipeline())
write(os.path.join(OUT, "coverage.svg"), coverage())
write(os.path.join(OUT, "roles.svg"), roles())
