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

**Admin** — left sidebar (no "Brands" item since 2026-09-28: brands are picked with the switcher on top, and the brand in context adds a **This brand** group — Connections · Schedules · Reports · Runs · Access — above the rest, which is then headed *All brands*; the brand list itself is reached from the switcher's *Manage brands*):
```
[ brand switcher ]
── This brand ── (only while a brand is open)
◉ Overview
◉ Runs
◉ Schedules
◉ Report library
── Setup ──
◉ Platform accounts
◉ Mailboxes
◉ Users & access
◉ Settings (SMTP, system)
◉ Audit log
◉ Unified data   (admins and the toggle admin; /data → Needs attention | Reports | Imports; 2026-10-03)
```
The **This brand** group also has **Data** (2026-10-03): the brand's twin of Unified data. Picking a brand while on `/data/*` lands on `/brands/{id}/data`; *All brands* from there goes back to `/data` (brand users, who have no `/data`, go to the brand list).
Top of the sidebar, under the logo: **brand switcher** (search; avatar only when collapsed). Global header: navigation toggle, the trail of where you are, **Run now** button, live-runs indicator ("2 running"), user menu.

**Where am I (added 2026-09-26).** The header trail names the page: `Del Monte › Runs` on a brand, `Runs › Run #1286` elsewhere. Picking a brand keeps the section and drops the detail — Del Monte's runs become Dinshaw's runs, all runs become one brand's runs — but never carries a run id or a filter across, because the same id on another brand is a different thing. Pages below the trail do not repeat it with "back" links.

One toggle, first in the header on every width: on a desktop it collapses the sidebar to icons (remembered across reloads); below 768px it opens the sidebar as a drawer, closed by any navigation. Ctrl/⌘+B does the same.

**Member with a Manager grant** ("Brand Manager") — the admin sidebar minus Users & access, Settings and Audit log, and every list scoped to their granted brands. With **exactly one** brand, there is nothing to choose: the switcher is replaced by that brand's name (linking to its page), its **This brand** group is always shown, and `/brands` redirects to the brand. A member with no grants has no sidebar items; Home shows an empty state saying they have no brand yet. The switchboard's **Brands** row still exists and covers the brand list, every brand page and the switcher: *hidden* removes the switcher and the *This brand* group, *locked* leaves a greyed, inert placeholder in the switcher's place.

**Member with an Executive grant** ("Brand Executive", the SPOC) — minimal: `Home · Reports · Run history`. If they have one brand, no brand switcher is shown.

The sidebar follows the *highest grant the member holds*, so someone who is a Manager on one brand and an Executive on another gets the Manager sidebar, with per-brand actions gated individually.

**Toggle admin** (`toggle_admin`, PRD §4a) — the full admin sidebar plus a `Visibility` entry under a `Product` group. Nobody else sees that entry, and this sidebar is never filtered by the rules below: a switchboard that can hide its own switch is a lock-out waiting to happen.

### 2a. Per-audience visibility (added 2026-09-23)

On top of the shapes above, a Toggle admin can mark any section **visible**, **locked** or **hidden** for the `admin`, `manager` and `executive` audiences:

- **locked** — the item stays in the sidebar, greyed, with a lock icon and a tooltip (the rule's own note, or "Coming soon"). It is inert: not a link, not focusable as one. A half-built screen shown as coming keeps the shape of the product legible in a way that silently removing it does not.
- **hidden** — the item is absent, and an emptied group leaves no stray divider.
- Both **bounce a typed URL back to the Overview**, so the hiding never looks broken.

Two limits are deliberate. The rules **only subtract**: marking `Users & access` visible for an Executive does not add it, because that audience never had it. And they are **presentation only** — the API answers exactly as before, so this is never how access is enforced (PRD §4a, `DECISIONS.md`). The same three states apply to platforms, categories and report types wherever the catalogue is rendered: the connect wizard's tiles, the Run now report tree and the Report library filters.

### 2b. Visibility switchboard (`/visibility`, Toggle admin only)

Audience tabs (Admin · Manager · Executive). Below them, a flat list of sections and a collapsible Platform → Category → Report tree, each row carrying a three-way state control and a note field enabled only for `locked` — a note that shows nowhere else would promise something that never appears. Saving is explicit, disabled until something changes, and re-pulls `/auth/me` so the editor's own shell updates immediately.

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

Brand detail, header "Del Monte" + **Run now** (pre-filled with this brand). The header sticks from 768px up. Sections are real URLs — `/brands/:id/connections` (the default), `/schedules`, `/reports`, `/runs`, `/access` — listed in the sidebar's **This brand** group rather than as tabs, and old `?tab=` links redirect. A section hidden from the audience by the visibility switchboard is hidden there too:
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

Range presets include **Week to date** (added 2026-10-02): the Monday of yesterday's week, or the 1st if later, through yesterday. Fired on Mondays and on the 1st, it pulls calendar weeks cut at month ends — the tiles the warehouse's weekly range check needs.

### 3.8 Report library

Top-level tabs: **Ads | Sales**. Filter bar under the tab: brand · platform · report type · period · "Latest only" toggle (on by default). The table shows file name, brand, platform chip, report, period, extracted at, size, badges (Latest, Columns changed), the *Data status* badge (§3.16) and a download button. Multi-select gives **Download as zip**. A row menu shows *Versions* (older pulls of the same period), *Open run* and the portal's original filename.

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

### 3.14 Unified data (`/data`, admins; rewritten 2026-10-03)

**Words.** Every user-visible word comes from one glossary, `frontend/src/lib/words.ts` (DECISIONS 2026-10-03). An *import* is one downloaded file going into unified data. Statuses: *Checking…* · *Waiting for your OK* · *Publishing…* · *Published* · *Held back* · *Pulled back* · *Same as an earlier file*. Actions: **Publish** · **Hold back** · **Import again** · **Re-pull** · **Mark as handled**. Enum names, keys, ids, file names, hashes and versions appear only under *Technical detail*; a test (`findJargon`) fails any page that shows them elsewhere. `/warehouse/*` links redirect here with their query.

Page shell: h1 is the page name; tabs **Needs attention | Reports | Imports**; the trail reads `Unified data › …`.

**Needs attention** (`/data/attention`, the landing page; refreshes every 30 s and on focus)
```
 Waiting for your OK
 ┌ Zepto · Ads   Sponsored Products — Campaign   21–27 Sep 2026 ───────────────┐
 │ 7 imports, all checks passed                    [ Review ]  [ Publish all ] │
 └─────────────────────────────────────────────────────────────────────────────┘
 Held back
 ┌ Zepto · Ads   Sponsored Products — Campaign   21–27 Sep 2026 ───────────────┐
 │ The day files don't add up to the weekly pull.                              │
 │ [ Re-pull ]  [ Import again ]  [ Mark as handled ]                          │
 └─────────────────────────────────────────────────────────────────────────────┘
 Publishing automatically      Campaign performance ▓▓▓▓▓▓░░░░ 9 of 14 clean days
```
- **Waiting** cards: brand → report → calendar week (cut at month ends). **Publish all** confirms with *Applies to* (brand, report, week) and summarises in words ("6 published, 1 held back after a last check").
- **Held back** cards: one sentence, the facts in words, and **Re-pull** (confirm states what will be pulled, e.g. "21–27 Sep 2026, one file per day"; the toast links *Watch the run*), **Import again**, **Mark as handled** (a note is required).
- Empty: *All caught up*, with links to Imports and Reports.

**Reports** (`/data/reports`, was Feeds)
- One section per platform, one card per category. Per report: switch **Feeds unified data** (optimistic; disabled until its columns are *Ready*), the columns word (*Ready* / *Columns being reviewed* / *Not supported yet*), **Weekly cross-check** with its explanation in view, **Pulled by:** (schedule links, *One file per day*) or *No schedule yet*, *Time per brand: about 35 s a day*, *Last import*.
- *Figures may still change for N days* sits under **Advanced** (it decides when brand users see *Provisional*).
- **Set up a brand**: preview (*Will pull 12 reports*, schedules *New* / *Adds N reports* / *No change* with their timing in words, *Can't pull:* with the reason, time per day) → **Create schedules for <Brand>** → the result with links; *Already set up* when nothing would change. At most three schedules: daily 06:00 for yesterday, one file per day; Mondays and the 1st at 07:00, *Week to date* (the weekly cross-check). The one-report *Create recommended schedule* dialog stays.

**Imports** (`/data/imports`, was Loads)
- Chips **Waiting for your OK · Held back** (held and pulled back) **· Published · All**, filters as data in the URL, header sort in the URL. Rows are named by report and period; no ids.
- Select waiting rows → sticky bar *N selected · Publish selected · Clear*. Refreshes every 10 s while a row is *Checking…*.
- The drawer (`?load=`; Back and Esc close it): title = report + period, status; *What happened*; checks in words (hard first, then *Worth a look*); *What it changed* (counts only); *The file* (the shared download buttons, as in the Library); footer actions the status allows (**Publish**, **Hold back** with a reason, **Import again**, **Re-pull**); links *Open the run* and *See in Library*. A publish that ends held gives a warning toast, never a success. Refusals are worded from the API's `code`.

### 3.15 Brand Data tab (`/brands/{id}/data`, everyone who can see the brand; added 2026-10-03)

- **Status** (everyone): Platform → Category → Report, each with *Data through 1 Oct* or *No data yet*, *2 days held back, being re-pulled*, *Provisional from 18 Sep: figures may still change*; a report that doesn't feed is muted (*Doesn't feed unified data yet*). Words and dates only — never a figure from the warehouse (dashboards come in phase 4–5). Category grants apply: an Ads-only manager sees Ads only. Works at 390 px.
- **Needs attention** and **Imports** (admins, when *Unified data* and *Data status* are visible): the same panels as §3.14, fixed to this brand — no other brand's card or import can appear. Header action **Set up unified data for <Brand>**.
- Empty: *This brand's reports don't feed unified data yet* (admins also get *Set up*).

### 3.16 Data status elsewhere (added 2026-10-03)

- **Report library**: a *Data status* badge per file (*Checked* · *Being checked* · *Held back, being re-pulled* · *Provisional*, each with a tooltip) and a *Data status* filter; nothing when the file doesn't feed or isn't the current version. *Columns changed* (was "Header changed").
- **Schedules**: a *Feeds unified data* badge on schedules that pull a feeding report; pausing or deleting the brand's only running schedule behind one warns first ("…will stop reaching unified data for <Brand>"); a partial last run is amber; *One file per day* everywhere (Run now, schedule dialog, list).

### 3.17 Analytics (`/analytics`, everyone with an Ads grant; added 2026-10-03)

The no-code dashboard builder; full design in `docs/unified-db/24-analytics-builder.md`.
```
 Analytics › Dinshaw's overview                     [ Saved views ▾ ] [ Share ] [ Edit ]
 [Brands ▾] [Platforms ▾] [Ad type ▾] [Last 30 days ▾] [vs previous period ▾]
 Data through 1 Oct · 2 days provisional
 ┌ Ad spend ────┐┌ Ad revenue ──┐┌ ROAS ────────┐┌ Orders ──────┐
 │ ₹4.2 L ▲12% ││ ₹13.1 L ▲8%  ││ 3.1× ▼4%     ││ 2,140 ▲6%    │
 └──────────────┘└──────────────┘└──────────────┘└──────────────┘
 ┌ Spend and ROAS by week ──────────────────┐┌ Top campaigns ─────────────┐
 │  (combo chart, provisional days hatched) ││  ranked table              │
 └──────────────────────────────────────────┘└────────────────────────────┘
 Editing a chart opens the side panel:
 ┌ Fields ─────────┐  Rows / X     [Week ×]          Chart  ★Line ★Combo Bar Area Pie …
 │ Money           │  Split by     [Platform ×]
 │  Ad spend       │  Values       [Ad spend · Sum ▾] [ROAS · from totals ▾]
 │ Rates  ROAS …   │  Filters      [Campaign contains "diwali" · keeps 64% of spend ×]
 │ Time · Where …  │  ▸ Advanced
 └─────────────────┘  Ad spend and ROAS by week · Dinshaw's · Zepto · 1–30 Sep 2026 · 1 filter
```
- A 12-column grid; move by dragging, resize from the corner. On phones the dashboard is view-only and stacks into one column.
- Dashboard filters live in the URL. A chart's own overrides show as a badge on that chart.
- Every chart: View as table; Source files (originals behind a point); Provisional / Partial / Restated / Data through.
- Save · Save as · Reset · Undo · My charts · Templates · Saved views · Share (viewer's own grants).
- Sidebar item **Analytics**; the brand twin is the brand's **Analytics** tab; switchboard section `analytics`.

## 4. Shared components

| Component | Used in |
|---|---|
| `StatusBadge` (icon + word; import statuses from `lib/words.ts`) | unified data |
| `DataStatusBadge` + `Hint` (icon + word, tooltip on hover, focus or tap) | library, brand Data tab |
| `DownloadActions` (*Download with dates* / *Download original*, `download` attribute) | library, import drawer |
| `Switch` (optimistic toggle) | unified data reports |
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
| `DataTable` opt-in column menu (`columnToggle`, `initiallyHidden`), row selection (`selected` / `onSelectedChange` / `canSelectRow`) and URL-driven sort (`sort` / `onSortChange`) | imports, library |
| `useUrlFilters(defaults, {push})`: keys in `push` add a history entry, so Back closes a drawer | imports |

## 4a. "Applies to" (added 2026-09-26)

Every dialog or drawer that changes something opens with an **Applies to** block naming the brand (with its avatar), and the login where the change belongs to one: Run now, the schedule dialog, *Brands on this login*, disconnect/delete login, archive brand. The confirm button names the target too: *Start run for Del Monte*, *Create schedule for Del Monte*, *Delete DM Blinkit*. Removing something permanent (a login, or a brand's last use of one) or archiving a brand asks for its name to be typed first.

This is the human side of CLAUDE.md rule 9: the adapter refuses to download for the wrong business, and this makes sure the person pressing the button can see which business they are acting on.

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
