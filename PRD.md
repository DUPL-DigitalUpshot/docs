# UniQCAI — PRD: Unified Report Download Console

Version 0.2 · 21 Sep 2026 · Owner: Vishnu Tripathi · Client: Digital Upshot Pvt Ltd · Delivered by CAIR, SRHU
Companion docs: `SYSTEM_DESIGN.md`, `UI_PLAN.md`, `THEME.md`

---

## 0. Where this PRD sits

The proposal (*UniQCAI*, v3.0, 04 Sep 2026) has two modules: **Module 1 Reporting** (extraction → validation → mapping → warehouse → dashboards) and **Module 2 Campaign Operations** (Zepto first). The working-flow plan breaks Module 1 into:

| Working-flow section | Covered by |
|---|---|
| **A. 1–5** UI & access · Zepto first working flow · platform modules · rollout · unified download reports | **This PRD** |
| B. 6 Unified reporting format | Later PRD (Stage B) |
| B. 7 Report updation (T-15) | Download side here (FR-28a); merge logic in Stage B |
| B. 8 Reporting & dashboarding | Later PRD |
| Module 2 Campaign operations | Later PRD; hooks reserved here (§10) |

In the proposal's terms, this PRD delivers the **unified extraction framework**, **report extraction**, **raw data preservation** and **data freshness indicators** components of §5.2, plus the RBAC, credential and audit requirements of §14.1.

## 1. Summary

UniQCAI is a web app that logs into quick-commerce seller and ads portals on a brand's behalf, downloads their reports automatically (on a schedule or on a click), and gives each brand's SPOC a login where they can see and download only their own reports.

Stage A is **only the download console**. No parsing, no unified database, no dashboards. Those come later (section 10), and Stage A is built so they plug in without a rewrite.

## 2. Problem

Digital Upshot's team manages many brands across Zepto, Blinkit, Instamart, Flipkart Minutes and BigBasket. Today someone logs into each portal and waits for an OTP email. Then they pick dates, download each report and pass the files on, per brand and per platform. This is slow, error-prone and does not scale with the number of brands.

The RPA for four platforms already works as standalone Python + Playwright scripts. What is missing is a product around them: configuration, scheduling, monitoring, storage and access control.

## 3. Goals and non-goals

**Goals (Stage A)**
- G1. An admin can onboard a brand and its platform logins without touching code.
- G2. Reports download on a manual click or on a schedule, for any brand and any platform.
- G3. Every run is visible live and afterwards: which step it is on, what failed and why.
- G4. Downloaded files are stored untouched, organised, versioned and downloadable.
- G5. A brand SPOC sees only their brand's reports.

**Non-goals (Stage A)**
- Parsing reports into a unified schema (Stage B).
- Dashboards and analysis (Stage B).
- Changing anything on the platforms, such as pausing campaigns or editing budgets (Module 2).
- BigBasket automation (on hold: Google sign-in + 2FA). It appears in the catalog as "Coming soon".

## 4. Users and roles

Follows working-flow §1.3 (access privileges).

There are **three roles** and, on top of them, a **per-brand grant level**. The two are different things, and this document uses one vocabulary for each:

| Role (`users.role`) | UI copy | Who | Can do |
|---|---|---|---|
| `super_admin` | Super admin | Tech owner | Everything, including system settings, encryption keys and audit log |
| `admin` (§1.3.1) | Admin | Digital Upshot leads | All brands. Creates brands and users, and **grants other users access to brands** |
| `member` | Member | Everyone else | Nothing by default. Sees exactly the brands granted to them, at the level of each grant |

| Grant level (`brand_grants.level`) | UI chip | Who | Can do on that brand |
|---|---|---|---|
| `manager` (§1.3.2) | `Del Monte · Manager` | Digital Upshot account executive handling specific brands | Add/edit platform credentials and connections, manage schedules, run downloads, download reports |
| `executive` (§1.3.3) | `Del Monte · Executive` | Brand-side person, e.g. Del Monte's SPOC | View and download reports and run history. Trigger manual runs only if the grant allows it (**off by default**) |

Access is granted **per user × brand**, and the grant carries the level. One person can be a Manager for one brand and an Executive for another.

**"Brand Manager" and "Brand Executive" are shorthand**, used throughout this PRD, for *a member holding that grant level on that brand*. They are not roles in the schema and not words the UI shows on their own.

"View credentials" (§1.3.2) means seeing that a login exists, its login id, mailbox and health. **Passwords and app passwords are never displayed to anyone**, including Admins; they can only be replaced. Access is always enforced server-side, never only hidden in the UI.

## 5. Platform scope and organisation

Everything users see is organised as **Platform → Category (Ads | Sales) → Report type**. This matches the proposal's split between advertising/campaign reports and business reports (§5.2).

| Platform | Ads | Sales | Verification | Stage A status |
|---|---|---|---|---|
| Zepto | ✓ `zepto.ads` — brands.zepto.co.in | ✓ `zepto.vendor` — fcc.zepto.co.in API, **same login** | Email OTP | Ads working, client-validated; Sales working in prototype |
| Blinkit | ✓ `blinkit.brandcentral` — magic link | ✓ `blinkit.partnersbiz` — OTP, separate login | Email link / OTP | Working in prototypes |
| Swiggy Instamart | ✓ `instamart.brandportal` | ✓ `instamart.brandportal` — **one portal serves both** | Email OTP, no password | Working in prototypes |
| Flipkart Minutes | ✓ `fkminutes.ads` — advertising.flipkart.com | ✓ `flipkart.sellerhub` — seller.flipkart.com (reports to confirm) | Email OTP | Ads working in prototype (proposal §3 lists it as pending — update the client on status) |
| BigBasket | Coming soon | Coming soon | Google sign-in + 2FA | On hold |

A category is switched on per platform in configuration, so adding Zepto or Instamart Sales later is a new adapter plus a config change, with no redesign.

**Two layers:**
- **What users see: Platform → Category.** "Blinkit · Sales", "Zepto · Ads". Setup, health, runs, schedules, the report library and access all use this.
- **What the system uses: Portal.** The actual website behind a category, e.g. PartnersBiz behind "Blinkit · Sales". Each portal has its own adapter, OTP rule and health, so a broken PartnersBiz login never stops Ads downloads. **Portal keys name the website, not the category** — the verified list is in `SYSTEM_DESIGN.md` §3. A portal does not always mean a separate login: Zepto's vendor reports ride the ads session, and Instamart serves both categories from one portal.

**Category belongs to the report type, not the portal.** Usually Ads reports come from the ads portal and Sales reports from the seller portal. If a platform ever puts a sales-style report in its ads console, that report is still filed under Sales.

**Categories are an extendable list.** Stage A ships Ads and Sales. The proposal's Module 3 (inventory and stock) would add an Inventory category without design changes.

All OTPs and verification links arrive by email, either in the account's own Gmail or via a forwarded inbox. Both are read over IMAP with an app password.

## 6. Core concepts

- **Brand**: a client brand, e.g. *Del Monte*.
- **Platform**: Zepto, Blinkit, Instamart, Flipkart Minutes, BigBasket.
- **Category**: the business grouping of reports: **Ads** or **Sales** (extendable).
- **Portal**: the website behind a platform's category (e.g. PartnersBiz). Mostly invisible to users. Named after the site, never the category.
- **Mailbox**: an IMAP inbox used to read OTPs/links (direct or forwarded).
- **Platform account**: one login on one or more portals of the same platform (if Ads and Seller share credentials, one account covers both) (username + password + which mailbox receives its OTP). One account may serve more than one brand if an agency login sees several brands.
- **Connection**: Brand × Platform account, plus which reports to pull and any in-portal brand selector.
- **Report type**: a downloadable report, with its platform, category and source portal (e.g. Zepto · Ads · SP `keyword_performance`).
- **Run**: one execution that logs in and downloads one or more report types for a date range.
- **Schedule**: a saved rule that creates runs automatically.
- **Report file**: a downloaded file, stored raw with its metadata.

## 7. Functional requirements

Priority: **P0** = must ship in Stage A, **P1** = should ship, **P2** = nice to have.

### 7.1 Authentication and access
- FR-1 (P0) Email + password login. Session via secure HTTP-only cookie.
- FR-2 (P0) Roles `super_admin | admin | member`, plus a per-brand grant level `manager | executive`, as defined in section 4.
- FR-3 (P0) Members see only granted brands in every list, file download and API response, whatever their grant level. Platform accounts are visible only if they serve at least one granted brand.
- FR-4 (P0) Admin can invite a user by email (invite link via SMTP), assign brand grants at Manager or Executive level, and deactivate users.
- FR-5 (P1) Per-grant permission `can_trigger_runs` for executive-level grants.
- FR-5a (P2) Optionally limit a grant to certain categories (e.g. Del Monte · Sales only). By default a grant covers all categories.
- FR-6 (P2) TOTP 2FA for Admins.

### 7.2 Mailboxes and SMTP
- FR-7 (P0) Add a mailbox with IMAP host, port, email and app password. Type is **Direct** or **Forwarded**. A forwarded mailbox lists which original addresses forward into it.
- FR-8 (P0) "Test connection" button: logs in, lists the latest 5 subjects and shows the result inline.
- FR-9 (P0) App passwords are stored encrypted, are write-only in the UI (shown masked) and are never returned by the API.
- FR-9a (P0) **OTP and link extraction rules** (working-flow §2.1.3–2.1.4). Each portal ships default rules (sender, subject pattern, OTP regex, login-link regex). Admins can override them per portal or per account, without code changes.
- FR-9b (P0) **Rule tester**: paste an email body, or pick one of the latest emails in a mailbox, and see what the regex extracts before saving.
- FR-9c (P0) **Forwarding** (§2.1.2): a forwarded mailbox records the original addresses; OTPs are matched to the right account by recipient.
- FR-10 (P1) Configure one outbound SMTP profile for invites and notifications, with a "Send test email" button.

### 7.3 Brands
- FR-11 (P0) Create, edit and archive a brand (name, optional logo, notes).
- FR-12 (P0) Brand page shows its connections, schedules, recent runs, reports and who has access.

### 7.4 Platform accounts and connections
- FR-13 (P0) Connect a platform to a brand: pick platform (e.g. Blinkit) → tick categories (Ads, Sales or both) → for each category enter its login, or reuse the same login if the portals share credentials → pick the mailbox that receives its OTP.
- FR-14 (P0) "Test login" runs a real login in the background and streams the steps live (browser started → credentials entered → waiting for OTP → OTP received → logged in).
- FR-15 (P0) Connect a brand to a platform account and choose which report types to pull by default.
- FR-16 (P0) If the account sees multiple brands inside the portal, store the in-portal brand selector for this connection. Confirmed necessary, not hypothetical (see §12 Q1), and it is what `WRONG_ACCOUNT` checks against before every download.
- FR-17 (P0) Health is tracked per portal and shown per **brand × platform × category**: **Healthy** (last login OK), **Needs attention** (last login failed), **Untested**. A Sales failure never marks Ads as broken.
- FR-18 (P1) Reuse browser session cookies between runs where the portal allows it, to avoid an OTP on every run.

### 7.5 Report catalog
- FR-19 (P0) Each portal publishes its list of report types from code (the adapter), with name, description, **category (Ads | Sales)** and date-range rules (e.g. max days per pull).
- FR-19a (P0) Each report type declares **how it is delivered**: `browser` (the adapter drives the page and catches a download), `api` (the portal has a JSON API — queue, poll, fetch) or `email` (the adapter requests it in the portal and the file arrives in a mailbox, as an attachment or a download link). Report mail is read by the same mailbox service as OTPs, with its own rule (sender, subject, attachment or link pattern) that admins can edit and test like an OTP rule. `browser` ships in Stage 3, `api` in Stage 4, `email` in Stage 6.
- FR-20 (P0) Initial catalog, from the verified schema docs:
  - **Zepto · Ads:** Sponsored Products and Sponsored Brands × {campaign, category, city, keyword, page, product}. Sponsored Display is declared in the catalogue with `active = false` — the prototype downloads it, but it has never been captured or schema-verified, so it stays hidden until it is.
  - **Blinkit · Ads:** MTD search report workbook; dashboard export (Banner Listing, Product Recommendation).
  - **Instamart · Ads:** AUTO_SUMMARY, AUTO_DATE, AUTO_CITY, AUTO_PRODUCT, AUTO_PLACEMENT, AUTO_SEARCH_QUERY, AUTO_GRANULAR.
  - **Flipkart Minutes · Ads:** attribution, daily, FSN, keyword, placement, search term, zone.
  - **Zepto · Sales** (`zepto.vendor`): sales, inventory, DEQ inventory, catalogue, GRN, fill rate, ODR, ODR inbound, OTIF, RTV, MSL, OOS visibility, non-FBZ sales ledger.
  - **Blinkit · Sales** (`blinkit.partnersbiz`): sales, stock on hand (SOH), purchase orders, invoices, fees & charges, scorecards, fill-rate scorecard. The weekly scorecard is `delivery: email` (FR-19a) — there is no page to drive.
  - **Instamart · Sales:** sales report (options as in the prototype's `sales_options.json`).
  - **Flipkart Minutes · Sales:** to be confirmed in the platform study.
- FR-20a (P0) Report types carry a **group** shown as sub-headings inside a category. Sales has many supply-chain reports, so it is grouped as *Sales · Inventory · Purchase & supply · Finance · Scorecards* rather than one long list. Ads uses groups such as *Sponsored Products / Sponsored Brands*.
- FR-21 (P1) Zepto files have no date column, so Zepto report types offer a **"Split by day"** option that pulls one file per day.

### 7.6 Manual runs ("Run now")
- FR-22 (P0) "Run now" from a brand, a connection, or the global header: choose brand → platforms → categories → report types → date range. Reports are grouped under **Ads** and **Sales** headings, and ticking a heading selects all its reports.
- FR-23 (P0) Date range presets: Yesterday, Last 7 days, Last 30 days, Month to date, Previous month, plus a custom range. All dates in IST.
- FR-24 (P0) After submitting, the user lands on the **live run view** (FR-30). No blind waiting.
- FR-25 (P0) Only one run per platform account executes at a time. Additional runs queue and show "Queued behind run #123".

### 7.7 Schedules
- FR-26 (P0) Create a schedule: brand → platforms → categories → report types → frequency → date range. A schedule can target a whole category, e.g. "All Sales reports for Del Monte, daily"; newly added report types in that category are then included automatically.
- FR-27 (P0) Frequency builder: Daily at HH:MM, Weekly on days at HH:MM, Monthly on day N at HH:MM, or Advanced (cron). The next 5 run times are shown before saving.
- FR-28 (P0) Date range mode is either **Rolling** (preset relative to run date, e.g. "last 3 days") or **Fixed** (a custom start/end).
- FR-28a (P0) **T-15 report updation** (working-flow §7.1): a built-in preset "Refresh last 15 days" re-downloads the trailing 15 days on each run, because platforms restate figures after the fact (verified on Blinkit). Every pull is kept as a version; merging versions into the unified data is Stage B.
- FR-29 (P0) Pause, resume, edit and delete a schedule. Each schedule shows its last run result and next run time.

### 7.8 Run execution and monitoring
- FR-30 (P0) Live run view: a step timeline updated in real time, per connection and per report, with elapsed time and current action (e.g. "Waiting for OTP in ops@… 0:34").
- FR-31 (P0) Run states: Queued, Running, Waiting for OTP, Succeeded, Partially succeeded, Failed, Cancelled.
- FR-32 (P0) Failures carry a readable error code and message: `LOGIN_FAILED`, `OTP_TIMEOUT`, `PAGE_CHANGED` (selector not found), `DOWNLOAD_TIMEOUT`, `EMPTY_REPORT`, `PLATFORM_ERROR`, `WRONG_ACCOUNT`.
  `WRONG_ACCOUNT` means *the session is valid but belongs to a different business* — the login carries several and the one selected is not the one this connection expects. It is never retried and never worked around: the alternative is a complete, believable file for the wrong brand.
- FR-33 (P0) On failure, store a screenshot of the page (credentials never visible) and attach it to the run.
- FR-34 (P0) Automatic retry: up to 2 retries with backoff for transient errors. No retry for `LOGIN_FAILED` (wrong password), to avoid account lockout.
- FR-35 (P0) Cancel a queued or running run. Retry a failed run with one click.
- FR-36 (P0) Runs history: filter by brand, platform, status, trigger (manual/schedule) and date.

### 7.9 Report library
- FR-37 (P0) Every downloaded file is stored byte-for-byte **exactly as received and is never rewritten or stamped**, with: brand, portal, report type, requested period, extracted-at time, run id, file size and checksum.
- FR-37a (P0) The name a user downloads is generated, not the portal's: `<brand>_<platform>_<category>_<report>_<start>_<end>.<ext>`. Several portals return uninformative or colliding filenames, and Zepto's files carry no date column at all, so the period has to survive somewhere — this is where, instead of editing the bytes. The portal's own name is kept in `report_files.original_filename`.
- FR-38 (P0) Library view has top-level tabs **Ads | Sales**, then filters by brand, platform, report type and period. Download one file or a zip of a selection.
- FR-39 (P0) Keep every version. If the same brand × report × period is pulled again, the newest is marked **Latest** and older ones stay available. (Blinkit is verified to restate past figures.)
- FR-40 (P1) Each run also writes a `manifest.json` (requested range, report types, per-report status and files).
- FR-41 (P1) Store each file's header row. If it differs from the last file of the same report type, flag the file **"Columns changed"**. This is cheap now and protects Stage B parsing.

### 7.10 Notifications
- FR-42 (P1) Email admins when a scheduled run fails or an account moves to "Needs attention".
- FR-43 (P2) Daily digest email: runs, successes, failures.
- FR-44 (P2) Optional: email a SPOC when new reports for their brand are ready.

### 7.11 Audit
- FR-45 (P0) Audit log of who created, changed or deleted brands, accounts, mailboxes, schedules and users, and who downloaded which file. Required before Module 2, when actions will affect ad spend.

## 8. Non-functional requirements

- **Security:** all credentials encrypted at rest (AES-GCM / Fernet, key from environment). Secrets are never logged and never sent to the browser. Login steps are excluded from browser traces. HTTPS only.
- **Reliability:** ≥ 95% of scheduled runs succeed over a rolling 14 days, excluding portal outages. A worker crash must not lose a run; it is picked up again or marked failed.
- **Scale (Stage A target):** 30 brands × 5 portals, around 150 runs/day, 3–4 concurrent browsers.
- **Timezone:** all scheduling and date ranges in Asia/Kolkata.
- **Portability:** the whole stack runs with Docker Compose on one Linux machine (lab server or cloud VM).
- **Maintainability:** each portal is a separate adapter module. A portal UI change is fixed in one file.
- **Interactivity:** every long action shows live progress. No action leaves the user on a static spinner for more than 2 seconds.

## 9. Assumptions and decisions

- D1. Python end to end: FastAPI backend and Playwright workers, reusing the existing scripts. React frontend and Docker, as in proposal §14.
- D1a. PostgreSQL here is the **application database** (users, schedules, runs, file metadata). The proposal deliberately leaves the **analytical warehouse** choice to month 2 (M2); nothing in this PRD pre-empts that decision.
- D2. Files stay raw in Stage A. Parsing is Stage B.
- D3. Executive-level grants are view/download only by default; credentials are managed by admins and manager-level grants.
- D4. All verification is email-based (IMAP). SMS/phone OTP is not supported in Stage A.
- D5. One run per platform account at a time, to avoid session invalidation and OTP mix-ups.
- D6. Hosting is undecided. The design is host-agnostic (see SYSTEM_DESIGN §10 for the decision checklist).

## 10. Roadmap: how this maps onto the proposal

| Stage | Proposal reference | What it adds | What this console already provides |
|---|---|---|---|
| **A. Unified download console** (this PRD) | §5.2 extraction framework, raw preservation, freshness; working-flow A | Configure, run, schedule, store, share | — |
| **B1. Unified format + mapping layer** | §5.4, working-flow 6 | Admin mapping UI (columns → standard fields), versioned mappings, unmapped-column flags. Expect **two unified formats, one for Ads and one for Sales**: they have different grains (campaign/keyword vs SKU/day) and different metrics | Raw files kept byte-for-byte with header row and header-change flag, so any mapping can be re-applied to history |
| **B2. Validation engine** | §5.3 | Control totals, row counts, date completeness, duplicates, null rates. Load status **extracted → validated → approved → published**; failed loads quarantined | Every file is already recorded as *extracted*, with run manifest, requested range and checksum. Validation adds the next states |
| **B3. Report updation** | working-flow 7 (T-15) | Idempotent merge of restated days into the warehouse | T-15 refresh schedules and file versioning (FR-28a, FR-39) |
| **B4. Warehouse + dashboards** | §5.2, M4–M5, working-flow 8 | Staging + master layers, executive summary and drill-down | Brand model, RBAC scoping and freshness indicators reused |
| **Module 2. Campaign operations** (Zepto first) | §6, M6–M7 | Budget, bid, pause, activate with preview, approval thresholds, idempotency, audit | Adapter interface reserves an `actions` capability; audit log and per-grant permissions exist |

## 11. Success metrics and acceptance

- Onboard a new brand with 2 portals and get the first successful download in **under 10 minutes**, without code changes.
- A scheduled daily run for every configured connection runs unattended for **14 days** at ≥ 95% success.
- A member cannot list, download or guess the URL of a file belonging to a brand they have no grant on (verified by test).
- Every failed run shows a reason and a screenshot. There are no silent failures.
- **Zepto gate** (working-flow §2.3): the complete Zepto flow — mailbox, forwarding, regex, links, download, storage, access — is reviewed and approved by the client before other platforms are rolled onto the console.

## 12. Open questions

1. ~~Does any single platform login give access to **multiple brands** (agency login)?~~ **Answered: yes.** One Instamart login carries BACARDI, Dilmah Tea and Del Monte; the Flipkart Seller Hub login carries two unrelated businesses. FR-16 is P0 and `WRONG_ACCOUNT` (FR-32) exists because of it. Still to confirm with the client: *which* brands run through agency logins in production.
2. Maximum date range each portal allows per export, and whether Zepto offers a day-wise export (which avoids the split-by-day loop).
3. PartnersBiz (`blinkit.partnersbiz`) and the Flipkart Seller Hub (`flipkart.sellerhub`): which report types exist and are needed? Overlaps Q7 for the Flipkart half.
4. Do any portals show captchas when logging in from a new or datacenter IP? This affects hosting choice.
5. How long must raw files be retained?
6. BigBasket: outcome of the discussion with BigBasket on the Google sign-in + 2FA issue (proposal §12 lists this as a blocking client input).
7. Which Flipkart Seller Hub reports are needed for Flipkart Minutes · Sales? (Zepto, Blinkit and Instamart Sales are already working in the prototypes.) The surface is mapped — `legacy/fkminutes/docs/ads-report-flow.md` records the Report Centre at `#dashboard/metrics/report-centre` carrying Fulfilment, Invoices, Listings, Payment and Tax — but nothing there is automated yet, and the existing pipeline pulls only the eight *ads* reports. The client picks which Report Centre reports count as Sales.
8. Can a Brand Executive ever add credentials for their own brand, or is that strictly Digital Upshot staff (Manager level)?
9. Working-flow §3.2.3 "click-and-opt related handling": confirm the wording. Is this click-to-verify login links, opt-in consent screens, or something else?
10. Who approves the Zepto gate (§2.3.2), and who is the nominated business owner (proposal §16)?
11. **Forwarded-OTP samples — needed before Stage 2 is signed off.** FR-9c matches an OTP to an account by recipient, but no prototype does any recipient matching today (they read only `Date`, `From` and `Subject`), so all of it is new code with no evidence behind it. We need one real, redacted sample per forwarding setup — auto-forward, relay mailbox, and a manual `Fwd:` — saved as a fixture. A saved manual forward already shows the hard case: the outer `From:` was the *person forwarding*, not the platform, so a sender-based search would not have found it at all, and the only recipient evidence was a `To:` line inside the forwarded body. Redaction is not optional: these emails carry live magic links and presigned report URLs.
12. ~~**One Blinkit Sales report is delivered by email, not by download.**~~ **Answered.** `ReportSpec` gains `delivery: browser | api | email` (FR-19a), so the mechanism is a property of the report type rather than an assumption baked into the adapter contract. `browser` ships in Stage 3, `api` in Stage 4, and `email` with Blinkit Sales in Stage 6.
13. **The Instamart engine code was never imported.** `legacy/instamart/*.py` are shims importing `upshot.platforms.instamart.{ads,sales,login}.cli` from a `src/` tree that is not in this repo — the session module and both report engines are missing. What survives is the CLI surface, `webapp.py`, `sales_options.json`, the saved HTML and the README. **Open, with an owner:** Vishnu will locate the missing tree in the original working folder and import it before Stage 6. If it cannot be found, Instamart becomes a rewrite from the saved HTML rather than a port, and Stage 6 has to be re-estimated.

## 13. Build plan (follows working-flow section A)

| Step | Working-flow ref | Deliverable |
|---|---|---|
| 1 | 1.1–1.3 | App shell with the approved UI, auth, the four roles, brand grants, credential flow (accounts, connections, encrypted secrets) |
| 2 | 2.1 | Mailboxes, forwarding, OTP/link rules with the rule tester — built and proven on Zepto |
| 3 | 2.2, 3.1–3.2 | Adapter interface and executor; **Zepto Ads** (`zepto.ads`) as the first module; runs, live run view, report library |
| 4 | 2.2 | **Zepto Sales** (`zepto.vendor`, the JSON-API adapter); then schedules, T-15 refresh, notifications, audit log → **complete Zepto working flow, Ads and Sales** |
| 5 | 2.3 | **Client review and approval of the Zepto flow** (gate) — covers both categories |
| 6 | 4.2 | Roll out the remaining adapters in the working-flow order: Blinkit Ads → Blinkit Sales → FK-Minutes Ads → Instamart Ads → Instamart Sales → FK-Minutes Sales. BigBasket stays "Coming soon" |
| 7 | 5.1–5.3 | Testing and bug fixing, UAT with Digital Upshot users, finalisation and deployment |

The gate is on the *whole* Zepto flow, so Zepto Sales has to be working before it, not in the rollout after it — and the vendor side is a genuinely different mechanism (a JSON API, no DOM), which is exactly the kind of thing a gate should have exercised.

Stage B (§10) starts once step 7 is signed off. Working-flow item 2.4 (unified format for Zepto) can run in parallel from step 3 onwards, using the files the console is already storing.
