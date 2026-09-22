# UniQCAI — UI Plan (Stage A)

Version 0.1 · 21 Sep 2026 · Companion to `PRD.md`, `THEME.md`

---

## 1. Design principles

1. **Never make the user wait blind.** Every login, test and download shows live steps. This is what makes the app feel interactive rather than like a form that submits and hopes.
2. **Health at a glance.** The first thing an admin sees is what is broken and what runs next.
3. **Brand-first navigation.** People think "Del Monte on Blinkit", not "account #14". Brands are the spine of the app.
4. **Guided setup, not forms.** Adding a platform login is a 4-step wizard that ends with a real test login.
5. **One primary action per screen**, placed top-right: *Run now*, *Add brand*, *New schedule*.

## 1a. Organising principle: Platform → Ads | Sales

Every screen groups the same way: **Platform first, then category (Ads or Sales), then report type.** Users never have to know that "Blinkit · Sales" is technically PartnersBiz. Portal names appear only in setup details and error messages ("PartnersBiz login failed") — and they are the real site names, listed in `SYSTEM_DESIGN.md` §3.

## 2. Navigation

**Admin** — left sidebar:
```
◉ Overview
◉ Brands
◉ Runs
◉ Schedules
◉ Report library
── Setup ──
◉ Platform accounts
◉ Mailboxes
◉ Users & access
◉ Settings (SMTP, system)
◉ Audit log
```
Global header: brand switcher (search), **Run now** button, live-runs indicator ("2 running"), user menu.

**Member with a Manager grant** ("Brand Manager") — the admin sidebar minus Users & access, Settings and Audit log, and every list scoped to their granted brands.

**Member with an Executive grant** ("Brand Executive", the SPOC) — minimal: `Home · Reports · Run history`. If they have one brand, no brand switcher is shown.

The sidebar follows the *highest grant the member holds*, so someone who is a Manager on one brand and an Executive on another gets the Manager sidebar, with per-brand actions gated individually.

## 3. Screens

### 3.1 Overview (admin home)

```
┌───────────────────────────────────────────────────────────────────────┐
│ Overview                                          [ ▶ Run now ]       │
├──────────────┬──────────────┬──────────────┬──────────────────────────┤
│ Runs today   │ Success 7d   │ Needs        │ Next scheduled           │
│ 42           │ 96.4%        │ attention  3 │ Del Monte · 06:00        │
├──────────────┴──────────────┴──────────────┴──────────────────────────┤
│ Connection health            A = Ads   S = Sales                      │
│              Zepto     Blinkit    Instamart   FK Minutes   BigBasket  │
│ Del Monte    A● S—     A● S●      A● S—       A○ S○        soon       │
│ Dinshaw's    A● S—     A▲ S●      —           —            soon       │
│ Field Fresh  —         A● S●      A● S—       A● S●        soon       │
│   ● healthy  ▲ needs attention  ○ untested  — not connected           │
├───────────────────────────────────────────────────────────────────────┤
│ Live now                                                              │
│ #1284 Del Monte · Instamart   ⟳ Downloading AUTO_CITY    01:12        │
│ #1285 Dinshaw's · Zepto       ✉ Waiting for OTP          00:21        │
├───────────────────────────────────────────────────────────────────────┤
│ Recent failures                                                       │
│ #1279 Dinshaw's · Blinkit Ads  LOGIN_FAILED  2h ago    [View] [Retry] │
└───────────────────────────────────────────────────────────────────────┘
```
Clicking a dot opens that brand × platform × category connection. Hovering shows the portal, login and last result. Clicking a live run opens the live run view.

### 3.2 Brands list → Brand detail

List: cards or table with name, logo, connected platform chips, last successful download, SPOC count.

Brand detail, header "Del Monte" + **Run now** (pre-filled with this brand). Tabs:
- **Connections**: one card per platform, with an Ads row and a Sales row inside it. Each row shows health, login, default reports, last run, `[Test login] [Edit]`. `+ Connect platform` at the top; `+ Add Sales` inside a card that only has Ads.

```
 ┌ Blinkit ─────────────────────────────────────────────────────┐
 │ Ads    ● Healthy   dm-blinkit@…   5 reports   last run 06:02  │
 │ Sales  ● Healthy   same login     3 reports   last run 06:04  │
 └───────────────────────────────────────────────────────────────┘
 ┌ Zepto ───────────────────────────────────────────────────────┐
 │ Ads    ● Healthy   dm-ads@…       12 reports  last run 06:00  │
 │ Sales  —  Not set up                           [ + Add Sales ] │
 └───────────────────────────────────────────────────────────────┘
```
- **Schedules**: this brand's schedules with next run time and a toggle.
- **Reports**: the library pre-filtered to this brand.
- **Runs**: history pre-filtered.
- **Access**: SPOCs with access, `+ Invite SPOC`.

### 3.3 Connect platform wizard (the key setup flow)

```
 ① Platform & categories  ──  ② Login(s)  ──  ③ Verification  ──  ④ Reports & test
```
1. **Platform & categories:** five platform tiles (Zepto, Blinkit, Instamart, FK Minutes; BigBasket disabled as "Coming soon"). After picking one, tick **Ads**, **Sales** or both. A category not yet available on that platform is shown greyed with "Not available yet".
2. **Login(s):** one login block per ticked category. If both are ticked, a toggle **"Ads and Sales use the same login"** collapses them into one. Each block can **reuse an existing account** (agency login) or create a new one: login id, password (masked), label.
3. **Verification:** choose the mailbox that receives this account's OTP (or `+ Add mailbox` inline). For forwarded mailboxes, confirm the original address. The portal's default OTP/link rule is shown collapsed, with *Customise* to open the rule editor (3.10).
4. **Reports & test:** report checkboxes under **Ads** and **Sales** headings (sub-grouped where useful, e.g. Sponsored Products / Sponsored Brands under Zepto · Ads), plus the in-portal brand selector if needed. Then **Test login**, run once per portal (both in parallel if Ads and Sales use different logins), which streams live:

```
 ✓ Browser started                        0:02
 ✓ Opened brands.blinkit.com              0:05
 ✓ Credentials entered                    0:07
 ⟳ Waiting for OTP in ops@du.com …        0:19   (timeout 3:00)
 ○ Signed in
 ○ Brand selected
```
Save is enabled after a successful test. "Save without testing" is allowed and marks the account *Untested*.

### 3.4 Run now (drawer from the right)

```
 Brand         [ Del Monte            ▾ ]
 Categories    [✓] Ads   [✓] Sales                (quick filter across platforms)
 Reports
   ▼ [✓] Zepto
        Ads    [✓] Campaign [✓] Keyword [ ] City …      (defaults ticked)
   ▼ [✓] Blinkit
        Ads    [✓] MTD search report  [✓] Dashboard export
        Sales  [✓] (seller reports…)
   ▸ [ ] Instamart
 Date range    (Yesterday) (Last 7d) (Last 30d) (MTD) (Prev month) (Custom…)
               01 Sep 2026 → 20 Sep 2026   IST
 Options       [ ] Split Zepto reports by day  (20 files per report)
                                          [ Cancel ]  [ ▶ Start run ]
```
It warns inline when a range exceeds a portal's limit and offers to auto-split. On start, it navigates to the live run view.

### 3.5 Live run view (the heart of the app)

```
 Run #1286 · Del Monte · Manual by Vishnu · 01–20 Sep 2026     [Cancel]
 Status: Running  ▓▓▓▓▓▓▓░░░░  5 / 8 reports

 ▼ Zepto · Ads  (dm-ads@…)                                 ✓ done 2:41
     ✓ Signed in (session reused, no OTP)
     ✓ SP · Campaign performance     24 KB    [⬇]
     ✓ SP · Keyword performance     310 KB    [⬇]  ⚠ Columns changed
 ▼ Blinkit · Ads  (dm-blinkit@…)                            ⟳ 1:05
     ✓ Signed in via OTP (ops@du.com, 0:26)
     ⟳ Downloading MTD search report …
     ○ Dashboard export
 ▸ Blinkit · Sales  (same login, waits for Ads to finish)     ○ queued
 ▸ Activity log (38 events)
```

A report type with `delivery: email` shows the wait explicitly, because it can outlast a browser step by a long way: `⟳ Requested — waiting for the report mail in ops@du.com … 4:12`. The task stays *Running*, not *Waiting for OTP*.
Rows group by **portal** (`run_tasks.portal_key`), which is why the task row carries it: one login can span several portals, so the connection alone cannot say which one a task ran against.

Failed task rows expand to show the error code in plain words, the screenshot thumbnail and a `[Retry this report]` button. Updates arrive via SSE and the page never needs refreshing.

Two failures have no `[Retry]` button, because retrying cannot help:
- `LOGIN_FAILED` — "Wrong password. Update the login, then retry." Retrying risks a lockout.
- `WRONG_ACCOUNT` — "Signed in fine, but this login opened **VaultKicks** and this connection expects **ReebokCricket**. Nothing was downloaded." Offers `[Fix the brand selector]`, linking to the connection, not a retry.

### 3.6 Runs (history)

A table with ID, brand, platforms (chips), trigger (manual/schedule icon), range, status badge, duration and files. Filters: brand, platform, status, trigger, date. Row click opens the live run view (read-only once finished).

### 3.7 Schedules

List: name, brand, platforms, "Daily 06:00 IST", range ("Rolling · last 3 days"), next run, last result badge, enable toggle.

Create/edit form:
```
 Name          Del Monte daily pull
 Brand         Del Monte ▾      Platforms & reports  (same picker as Run now)
               ☑ Blinkit · Sales — all reports  (new Sales reports included automatically)
 Frequency     (Daily) (Weekly) (Monthly) (Advanced cron)
               at [06:00] IST
 Date range    (● Rolling) [ Last N days ▾ ] N = [3]      ( ○ Fixed ) start → end
 Preview       Next runs: Tue 22 Sep 06:00 · Wed 23 Sep 06:00 · …
               Each run pulls e.g. 19–21 Sep for the 22 Sep run
```
The preview line that shows the resolved date range removes most scheduling mistakes.

### 3.8 Report library

Top-level tabs: **Ads | Sales**. Filter bar under the tab: brand · platform · report type · period · "Latest only" toggle (on by default). The table shows file name, brand, platform chip, report, period, extracted at, size, badges (Latest, Columns changed) and a download button. Multi-select gives **Download as zip**. A row menu shows *Versions* (older pulls of the same period), *Open run* and the portal's original filename.

**The filename is generated, not the portal's:** `<brand>_<platform>_<category>_<report>_<start>_<end>.<ext>`. The stored bytes are never touched, so the period has to live in the name and in the metadata — several portals return uninformative or colliding names, and Zepto's files carry no date column at all. `report_files.original_filename` keeps what the portal called it.

### 3.9 Platform accounts

A table of logins grouped by platform, showing label, login id, mailbox, which categories it serves (Ads, Sales), brands using it, health per category, last login, `[Test login]`. Password fields are always write-only ("•••• Change").

### 3.10 Mailboxes

Cards showing email, type (Direct/Forwarded + forwards-from list), last test result and last OTP read time. `[Test]` shows the latest 5 subjects inline.

**OTP & link rules** (tab on this page):
```
 Portal   [ Zepto Ads ▾ ]   Applies to  (● Portal default) ( ○ One account ▾ )
 Sender   noreply@zepto…        Subject contains  "OTP"
 OTP      \b(\d{6})\b           Link   https://…/verify\?token=[\w-]+
 ─ Test ─────────────────────────────────────────────
 Source  ( ● Latest emails in ops@du.com ▾ ) ( ○ Paste text )
 Result  ✓ OTP found: 482913   from email received 10:42 · "Your Zepto OTP"
                                               [ Reset to default ] [ Save ]
```

### 3.11 Users & access

A table of users with role and brand grants. Invite modal: email and role — **Super admin**, **Admin** or **Member** (`users.role`). For Members, add brand grants as rows: `brand ▾ · level (Manager | Executive) · Can trigger runs ☐`. The user row shows chips like `Del Monte · Manager`, `Field Fresh · Executive`.

Role and grant level are different things and the copy keeps them apart: the role picker never offers "Manager" or "Executive", and a grant chip never says "Admin". A member with no grants sees nothing, and the empty state says so.

### 3.12 Settings and audit

SMTP form with *Send test email*. Notification toggles (failure alerts, daily digest). Audit log is a filterable table (who, action, entity, when).

### 3.13 SPOC home

```
 Del Monte — Reports                               Last updated 06:14 today
 [ Ads ]  [ Sales ]                                 freshness: ● today ● ≤2d ● older
 ┌────────────┬────────────┬────────────┐
 │ Zepto      │ Blinkit    │ Instamart  │
 │ ● today    │ ● today    │ ● 3 days   │
 │ 12 reports │ 2 reports  │ 7 reports  │
 └────────────┴────────────┴────────────┘
 Latest Ads files          [ Download all latest (zip) ]
 …table as in Report library, scoped to their brand…
```
It also shows a read-only run history, and a Run now button only if `can_trigger_runs` is granted.

## 4. Shared components

| Component | Used in |
|---|---|
| `StatusBadge` (queued/running/awaiting_otp/succeeded/partial/failed/cancelled) | runs, overview, library |
| `HealthDot` (healthy/needs_attention/untested/not_connected) | matrix, accounts, connections |
| `PlatformChip` (platform colour + name, optional `· Ads` / `· Sales` suffix) | everywhere a platform appears |
| `CategoryTabs` (Ads \| Sales, extendable) | library, SPOC home |
| `HealthPair` (two dots, A and S, for one platform cell) | overview matrix, brand connections |
| `StepTimeline` (live SSE-driven list) | test login, live run |
| `DateRangePicker` with presets + IST label | run now, schedules, filters |
| `ReportPicker` (Platform → Ads/Sales → report checkboxes, with select-all per group) | run now, schedules, connection wizard |
| `SecretInput` (masked, write-only, "Change" affordance) | accounts, mailboxes, SMTP |
| `CronBuilder` with next-runs preview | schedules |
| `EmptyState` with one clear next action | every list |

## 5. States to design for every screen

- **Empty:** e.g. "No brands yet. Add your first brand to start pulling reports." with a button.
- **Loading:** skeleton rows, not full-page spinners.
- **Error:** inline, human wording plus the technical code in small text.
- **Permission:** a SPOC hitting an admin URL gets a friendly "You don't have access" page, not a crash.

## 6. Responsive

Desktop-first (1280px+) for admins. The SPOC home and report library must work on a phone (cards instead of tables below 768px), since SPOCs may just want to grab a file.

## 7. Build order for the frontend

1. App shell, auth, sidebar, theme tokens
2. Brands + Connect platform wizard + `StepTimeline` (test login)
3. Run now drawer + live run view
4. Runs history + report library
5. Schedules with `CronBuilder`
6. Overview, users & access, SPOC home, settings, audit
