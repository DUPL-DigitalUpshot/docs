# Blinkit — port reference

Two portals, **two separate logins, two separate sessions**, deliberately kept
apart in the prototype and kept apart here. `legacy/README.md` maps the files;
this says what the code has to do.

Sources: `legacy/blinkit/blinkit_session.py`, `report_engine.py`,
`link_provider.py`, `partnersbiz_session.py`, `partnersbiz_engine.py`,
`partnersbiz_otp.py`, `partnersbiz_scorecard.py`, `config.example.py`.

| | `blinkit.brandcentral` | `blinkit.partnersbiz` |
|---|---|---|
| Host | `brands.blinkit.com` | `partnersbiz.com` |
| Category | Ads | Sales |
| Sign-in | **magic link**, no password | **6-digit OTP**, no password |
| Sender | `brands@blinkit.com` | `noreply@partnersbiz.com` |
| Which business | — | `PB_ENTITY` → `connections.portal_brand_selector` |

Everything prefixed `PB_` in the old config belongs to PartnersBiz. Separate
browser profiles and cookie jars **on purpose** — do not merge them.

## Brand Central (Ads) — magic-link sign-in

No password exists. The portal mails a sign-in link; `link_provider.py` polls
IMAP for a message from `LINK_SENDER`, extracts the button URL, and navigates to
it. Guards worth keeping: a **baseline UID** taken before requesting, a
freshness check against the request time, a strict `LINK_REGEX` with a looser
`LINK_FALLBACK_REGEX`, and `LINK_MAX_ATTEMPTS = 3`.

**The sign-in link is a credential** (SYSTEM_DESIGN §6). It is never logged in
full and never stored — truncated in any UI, exactly as an OTP would be.

Timeouts: poll 3 s, timeout 180 s, verify 30 s.

### Two reports, two entirely different mechanisms

| Key | What it is |
|---|---|
| `dashboard` | Overview report — **emailed** as `.xlsx` for the chosen filters |
| `mtd` | Month-to-date — **instant download** |

So one portal needs both a browser download path *and* an email-delivery path.
The emailed one polls for `REPORT_EMAIL_SUBJECT`, extracts
`REPORT_LINK_REGEX`, and fetches it — with its own baseline UID, a 5 s poll and
a **600 s** timeout. That link is a credential too.

**Filters before requesting:** eight campaign types — Product Booster,
Recommendation Ads, Product Shelf, Stories, Prime Banner, Listing Spotlight,
Brand Spotlight, Brand Booster. Native date presets are only *This Week*, *This
Month*, *This Quarter*; anything else goes through **Custom Dates**.

## PartnersBiz (Sales) — OTP sign-in

Six-digit OTP, regex `One Time Password \(OTP\)\s+(\d{4,8})`, poll 3 s, timeout
180 s, 3 attempts. Same resend-and-retry shape as Zepto.

**`PB_ENTITY` is the legal entity name** — one login can carry several, so this
becomes `connections.portal_brand_selector` and is subject to CLAUDE.md rule 9:
verify the selected entity, raise `WRONG_ACCOUNT` on a mismatch, never guess.

### Reports

| Key | Notes |
|---|---|
| `sales` | Sales details — **queued** by the portal, also emailed. Never wait for a file dialog |
| `po` | Bulk PO — Excel, **max 30 days**; POSTs to `/v1/reports/bulk-po-excel/` |
| `soh` | Stock on hand — snapshot; the control queues it directly, **no dialog** |
| `scorecard` | In-portal scorecard |
| `invoice` | |
| `fees` | |
| `scorecard_email` | **`delivery: email`** — see below |

Three distinct download shapes in one portal: queued-then-emailed, queued via
XHR, and no-dialog-at-all. The `instant: False` flag exists because waiting for
a file dialog that will never appear is how this breaks.

`po` declaring `max_days: 30` is the second place a per-report range cap is
real (Zepto's `OOS_VISIBILITY` is the other), which is why `max_range_days`
needs enforcing rather than merely storing.

### The weekly scorecard is email-delivered (PRD FR-19a)

`partnersbiz_scorecard.py` does **not** drive a browser. It parses HTML tables
out of mail from `reports-noreply@partnersbiz.com` and writes a workbook.
Port it as a **`ReportEmailRule`**, not a browser step.

- Period comes from `(\d{4}-\d{2}-\d{2})\s*(?:to|and)\s*(\d{4}-\d{2}-\d{2})` —
  present in both the body ("for the date X to Y") and the subject ("for X and
  Y").
- Summary fields: CURRENT GRADE, FILL RATE, WEIGHTED FILL RATE PERCENT,
  POTENTIAL LOSS, HIGHEST RANK IN CATEGORY.

> `delivery: "email"` is **not** in `IMPLEMENTED_DELIVERIES` yet (Stage 6). The
> registry refuses a live adapter declaring it, so `scorecard_email` stays
> inactive until the executor grows that branch.

### The date picker is the hard part

`partnersbiz_engine.py` carries a whole DockKit calendar driver — month caption
parsing, JS-evaluated navigation, day clicking with a back-off — plus overlay
dismissal and a fallback ladder of confirm-button labels ("Download Data",
"Request Data", "Download", "Confirm"). That accumulated against a real,
awkward widget. **Port it as-is**; do not rewrite it against an idealised DOM.

## Do not port

- `webapp.py` / `templates/` — replaced by the React UI.
- Any debug dump taken on a login page (rule 1).
- Config-file credentials — logins live in `platform_accounts`, encrypted.

## Gotchas

| Trap | Consequence |
|---|---|
| Merging the two portals' sessions | one login invalidates the other |
| Waiting for a file dialog on a queued report | hangs until timeout |
| Treating the sign-in or report link as ordinary data | a credential in logs or UI |
| Assuming a date preset exists | only three are native; the rest need Custom Dates |
| Ignoring `po`'s 30-day cap | portal rejection mid-run |
| Rewriting the DockKit calendar driver | re-learning every quirk it already encodes |
| Driving the scorecard through the browser | it only ever arrives by email |
