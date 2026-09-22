# UniQCAI — System Design (Stage A)

Version 0.1 · 21 Sep 2026 · Companion to `PRD.md`

---

## 1. Architecture at a glance

```
                ┌──────────────────────────────────────────┐
  Browser  ───▶ │  nginx  (HTTPS, serves React build,      │
 (Admin/SPOC)   │          proxies /api and /api/events)   │
                └──────────────┬───────────────────────────┘
                               │
                     ┌─────────▼─────────┐        ┌──────────────┐
                     │   API (FastAPI)   │◀──────▶│  PostgreSQL  │
                     │  auth, RBAC, CRUD │        │  all state   │
                     │  SSE run events   │        └──────▲───────┘
                     └───┬─────────▲─────┘               │
              enqueue    │         │ pub/sub events      │
                     ┌───▼─────────┴─────┐               │
                     │      Redis        │               │
                     │ queue · locks ·   │               │
                     │ event channel     │               │
                     └───▲─────────┬─────┘               │
                         │         │ jobs                │
   ┌─────────────────┐   │   ┌─────▼──────────────────┐  │
   │   Scheduler     │───┘   │  Worker(s)             │──┘
   │  every 60s:     │       │  Playwright + Chromium │
   │  due schedules  │       │  platform adapters     │──▶ File storage
   │  → create runs  │       │  mailbox svc (IMAP)    │    (volume or S3/MinIO)
   └─────────────────┘       └────────────────────────┘
```

Six containers: `nginx`, `api`, `worker` (scalable), `scheduler`, `postgres`, `redis`. MinIO is optional; a local volume is fine for Stage A.

## 2. Tech stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React + Vite + TypeScript, Tailwind, shadcn/ui, TanStack Query, React Router | Fast to build, good component kit, easy live updates |
| API | FastAPI, Pydantic v2, SQLAlchemy 2, Alembic | Python everywhere; reuse your code |
| Queue | Redis + **Dramatiq** (or Celery if you prefer familiarity) | Simple, reliable, per-queue concurrency limits |
| Scheduler | Small Python process using `croniter`, driven by the `schedules` table | Schedules live in the DB and are edited from the UI, so no beat-config sync problems |
| RPA | Playwright (async) + Chromium | Your existing scripts |
| Mailbox | `imaplib`/`aioimaplib` polling | One service for OTPs, magic links and report mail; works with Gmail app passwords |
| App DB | PostgreSQL 16 | Operational state only (users, grants, schedules, runs, file metadata). The analytical warehouse is chosen separately in month 2, per proposal §14 |
| Files | Local Docker volume → S3-compatible later | Swappable storage interface |
| Live updates | Server-Sent Events (SSE) | One-directional run progress; simpler than WebSockets |
| Crypto | `cryptography` Fernet (or AES-GCM), master key in env | Encrypt passwords, app passwords, session state |

## 3. Data model

```sql
users            (id, email, name, password_hash, role[super_admin|admin|member],
                  is_active, last_login_at, created_at)
brand_grants     (user_id, brand_id, level[manager|executive],
                  can_trigger_runs bool, categories text[] NULL,      -- NULL = all categories
                  granted_by, granted_at)                              -- per-brand access

brands           (id, name, slug, logo_path, notes, archived_at, created_at)

mailboxes        (id, label, email, imap_host, imap_port, secret_enc,
                  kind[direct|forwarded], forwarded_for text[],
                  last_test_ok bool, last_test_at)
smtp_profiles    (id, host, port, username, secret_enc, from_address, use_tls)

platforms        (key 'zepto'|'blinkit'|'instamart'|'fkminutes'|'bigbasket',
                  display_name, sort_order, enabled bool)
categories       (key 'ads'|'sales', display_name, sort_order)         -- extendable: 'inventory' later
platform_categories (platform_key, category_key, enabled bool)         -- which combos are live

portals          -- seeded from adapter registry, not user-created
                 (key, platform_key, display_name, host, enabled bool)   -- see the table below
report_types     -- seeded from adapter registry
                 (key, portal_key, platform_key, category_key, report_group, name, description,
                  max_range_days, supports_split_by_day, active bool)

otp_rules        (id, portal_key, account_id NULL,          -- NULL = portal default override
                  sender_pattern, subject_pattern, code_regex, link_regex,
                  updated_by, updated_at)

platform_accounts(id, platform_key, label, login_id, secret_enc, mailbox_id,
                  created_by, created_at)
account_portals  (account_id, portal_key, session_state_enc, session_saved_at,
                  health[healthy|needs_attention|untested], last_login_at, last_error)

connections      (id, brand_id, account_id, portal_brand_selector,
                  default_report_keys text[], enabled)                  -- brand × account

schedules        (id, brand_id, name, cron, timezone default 'Asia/Kolkata',
                  range_mode[rolling|fixed], range_preset, range_days,
                  fixed_start, fixed_end, split_by_day bool,
                  connection_ids int[], report_keys text[],
                  category_keys text[],          -- "all reports in category"; new types auto-included
                  enabled, next_run_at, last_run_id, created_by)

runs             (id, brand_id, trigger[manual|schedule|test_login], schedule_id,
                  requested_by, date_start, date_end, options jsonb,
                  status[queued|running|awaiting_otp|succeeded|partial|failed|cancelled],
                  created_at, started_at, finished_at, manifest jsonb)
run_tasks        (id, run_id, connection_id, portal_key, report_key, period_start, period_end,
                  status, attempt, error_code, error_message, screenshot_path,
                  started_at, finished_at)                              -- one per report pulled
run_events       (id, run_id, task_id, ts, step, level, message)        -- timeline + logs

report_files     (id, task_id, brand_id, platform_key, category_key, portal_key, report_key,
                  period_start, period_end, extracted_at,
                  storage_path, original_filename, size_bytes, sha256,
                  header_row jsonb, header_hash, header_changed bool,
                  is_latest bool)

audit_log        (id, user_id, action, entity_type, entity_id, diff jsonb, ts, ip)
```

### Portal keys (verified against the prototypes)

A **portal key names the real website**, never the category. The category lives on the report type, so one portal may serve report types in several categories.

| key | platform_key | host | login | serves |
|---|---|---|---|---|
| `zepto.ads` | zepto | `brands.zepto.co.in` | password + email OTP | Ads |
| `zepto.vendor` | zepto | `fcc.zepto.co.in` (JSON API) | **none of its own** — rides the `zepto.ads` session | Sales |
| `blinkit.brandcentral` | blinkit | `brands.blinkit.com` | **magic link** from `brands@blinkit.com` | Ads |
| `blinkit.partnersbiz` | blinkit | `partnersbiz.com` | 6-digit OTP from `noreply@partnersbiz.com` | Sales |
| `instamart.brandportal` | instamart | `partner.instamart.in` | email + OTP, **no password** | Ads **and** Sales |
| `fkminutes.ads` | fkminutes | `advertising.flipkart.com` | password + OTP read from a relay mailbox | Ads |
| `flipkart.sellerhub` | fkminutes | `seller.flipkart.com` | password → **seller-account picker** → OTP | Sales |

Two deliberate irregularities:
- **`flipkart.sellerhub` breaks the `platform_key` prefix convention.** `seller.flipkart.com` is Flipkart-wide, not Minutes-specific, and may later serve another platform; its `platform_key` stays `fkminutes`. Nothing may assume `key.split('.')[0] == platform_key`.
- **`zepto.vendor` is not a separate login.** It is a portal row so that the vendor adapter and its health are separate from Ads, but it shares one browser session with `zepto.ads`: the vendor API reads the ads session cookie and takes the brand from the JWT, not from a selector. The executor must never open a second browser or perform a second login for it.

BigBasket gets its key when it comes off hold.

Key points:
- **Platform → Category → Report type** is what the UI groups by. **Portal** is the technical source: it owns the login, adapter, OTP rule and health. Each report type records all four, so the library can filter by category without knowing which portal produced a file.
- **One account, several portals:** a `platform_accounts` row can be linked to more than one portal of the same platform (e.g. Blinkit Ads and Seller sharing credentials) via `account_portals (account_id, portal_key, health, last_login_at)`. Health is stored per portal, so a Seller failure shows as "Blinkit · Sales needs attention" while Ads stays green.
- **Access:** Admins see all brands. `member` users see only brands in `brand_grants`; the grant level decides whether they can manage credentials (manager) or only view/download (executive).
- **OTP rules:** adapters ship defaults in code; `otp_rules` rows override them per portal or per account (working-flow §2.1.3–2.1.4). Resolution order: account → portal override → adapter default.
- **Run → Tasks → Files.** A run is what the user clicked. A task is one report pull for one connection and one period. `partial` = some tasks failed.
- **Versioning:** on insert, set `is_latest=false` on older files with the same (brand_id, portal_key, report_key, period_start, period_end).
- **A portal row does not imply a separate login.** `account_portals` may map one account to several portals that share a single browser session (`zepto.ads` + `zepto.vendor`). The account lock covers all portals of that login.
- **`run_tasks.portal_key`** is what says which portal a task ran against. A connection is brand × *account*, and one account spans several portals, so the connection alone cannot answer it. The live run view groups on it and health attributes to it.
- **Account vs connection** separation handles agency logins that see multiple brands, and makes the "one run per account" lock correct. Agency logins are confirmed, not hypothetical: one Instamart login carries BACARDI, Dilmah Tea and Del Monte, and the Flipkart Seller Hub login carries two unrelated businesses — hence `WRONG_ACCOUNT` (§4).

## 4. The adapter contract

Every portal is one Python module implementing the same interface. Your existing scripts get refactored into this shape; the rest of the system never knows platform details.

```python
class ReportSpec(BaseModel):
    key: str                    # "sp.keyword_performance"
    name: str                   # "Sponsored Products — Keyword"
    category: Literal["ads", "sales"]   # extendable
    group: str                  # sub-heading inside the category, e.g. "Inventory"
    max_range_days: int | None
    supports_split_by_day: bool = False
    delivery: Literal["browser", "api", "email"] = "browser"
    email_rule: ReportEmailRule | None = None    # required when delivery == "email"

class ReportEmailRule(BaseModel):
    """How to recognise the mail that carries this report. Same shape and same
    mailbox service as OtpRule, resolved the same way (account → portal → default)."""
    sender_pattern: str
    subject_pattern: str
    attachment_pattern: str | None = None   # filename glob, when it arrives attached
    link_regex: str | None = None           # when the mail carries a download link

class PlatformAdapter(ABC):
    portal_key: str             # "zepto.ads"
    display_name: str
    reports: list[ReportSpec]
    otp: OtpRule                # sender pattern, subject pattern, code/link regex
    capabilities: set[str] = {"download"}   # Module 2 adds "actions"
    session_mode: Literal["storage_state", "persistent_profile"] = "storage_state"
    login_mode: Literal["automatic", "bootstrap"] = "automatic"   # bootstrap = one-time human login (e.g. Google SSO)

    async def is_logged_in(self, page: Page) -> bool: ...
    async def login(self, page: Page, creds: Credentials, ctx: RunContext) -> None: ...
    async def select_brand(self, page: Page, selector: str | None, ctx: RunContext) -> None: ...
        # MUST verify, not just select: read back which business the session is
        # actually on and raise WrongAccount if it is not `selector`. See below.
    async def download(self, page: Page, report: ReportSpec,
                       start: date, end: date, ctx: RunContext) -> list[Path]: ...
        # `page` is None when report.delivery == "api" and the portal needs no DOM.
        # When report.delivery == "email", this only REQUESTS the report; the
        # executor then awaits it via ctx.wait_for_report_email().

class RunContext:
    async def step(self, name: str, message: str = "") -> None   # emits live event
    async def wait_for_otp(self, since: datetime) -> str          # code or link
    async def wait_for_report_email(self, rule: ReportEmailRule,
                                    since: datetime) -> list[Path]   # delivery == "email"
    download_dir: Path
    def cancelled(self) -> bool
```

### How a report arrives: `delivery`

Not every report is a file the browser downloads. Three mechanisms are in use across the prototypes, so the report type declares which one applies and the executor branches on it. Nothing else in the system needs to know.

| `delivery` | What happens | Where it is used | Built in |
|---|---|---|---|
| `browser` | The adapter drives the DOM and catches a download. | Zepto Ads, Blinkit Ads, Instamart, Flipkart | **Stage 3** |
| `api` | The portal has a real JSON API: queue the report, poll until it is ready, fetch the file. No DOM, and `page` may be `None`. | Zepto vendor (`zepto.vendor`) | **Stage 4** |
| `email` | The adapter *requests* the report in the portal, then the file arrives in a mailbox — as an attachment or a download link. | Blinkit PartnersBiz weekly scorecard | **Stage 6**, with Blinkit Sales |

`email` reuses the OTP mailbox service (§6) rather than inventing a second IMAP path: same poller, same freshness guards, same consumed-Message-ID set, same per-mailbox lock. What differs is the rule — `ReportEmailRule` matches a report mail (sender, subject, attachment filename or download link) instead of a code. Rules resolve account → portal → adapter default, exactly like `otp_rules`, and the rule tester in the UI works on them unchanged.

Two consequences worth stating, because they are easy to get wrong:
- **A report mail is not an OTP mail.** It can arrive minutes or hours after the request, so its timeout is per-report, not the 3-minute OTP timeout, and a task waiting on one sits in `running`, not `awaiting_otp`.
- **The freshness window is the request, not the login.** `since` is when the adapter clicked *Request*, so a scorecard mailed last week is never mistaken for this run's.

Build `browser` in Stage 3 and `api` in Stage 4. `email` is not built until Stage 6: nothing before Blinkit Sales needs it, and building it earlier would be guessing at a rule we have no sample for.

Registry: `adapters/__init__.py` maps `portal_key → adapter class`. The `portals` table and report catalog in the UI are seeded from this registry at startup.

### Session strategy (from the prototypes)

The prototypes use two approaches, and both are supported per adapter:
- **`storage_state`** (Playwright cookies + local storage in one JSON): the default. Stored encrypted in `account_portals.session_state_enc`.
- **`persistent_profile`** (a full Chrome user-data directory): used where a portal only trusts a real browser profile. Stored on an encrypted volume at `/data/profiles/<account_id>/<portal_key>/`, never in git or the DB. Only one browser may use a profile at a time, which the account lock already guarantees.

**Zepto is the worked example.** `zepto.ads` declares `session_mode = persistent_profile` **and** also saves `storage_state`, exactly as the prototype does: one profile directory per `account_portal` on the shared volume, plus the cookie jar in `account_portals.session_state_enc`. The Zepto account is shared with human users who invalidate the session server-side, so `is_logged_in()` failing is normal, not exceptional: **wipe the profile directory and log in fresh**, rather than trying to repair it. `zepto.vendor` opens no browser of its own — it reuses the `zepto.ads` context.

### Verifying the account: `WRONG_ACCOUNT`

One login may carry several businesses. The Flipkart Seller Hub login carries two unrelated companies; one Instamart login carries three brands. A session can therefore be perfectly valid and still be the *wrong* one, and the resulting file is complete and believable — nothing downstream can tell.

So `select_brand()` verifies rather than assumes: after selecting, read back which business the portal says it is on and compare it with `connections.portal_brand_selector`. On a mismatch, raise `WrongAccount` → error code `WRONG_ACCOUNT`, and **never fall back to a default or a cached choice**. The prototypes already refuse to guess (`seller_account.resolve()` raises `AccountChoiceRequired` rather than picking); this makes that behaviour mandatory for every adapter.

Where the portal offers no selector at all — `zepto.vendor` takes the brand from the JWT, `instamart.brandportal` filters by brand inside the report form — the adapter still verifies that the identity the session reports is the expected one.

**Bootstrap login** (BigBasket pattern): for portals that need a human step such as Google sign-in, an Admin runs a one-time headed login from the setup wizard; afterwards runs reuse the saved session headlessly until it expires, and the account turns *Needs attention* when it does.

## 5. Run execution flow

```
API  POST /runs ─▶ create run + tasks (status=queued) ─▶ enqueue run_id
Worker picks run_id
  for each connection in run (grouped by account):
     acquire lock  lock:account:{account_id}  (covers all portals of that login)      (else stay queued, message "queued behind #N")
     launch browser context (restore session_state if present)
     ctx.step("Opening portal")
     if not adapter.is_logged_in(page):
         ctx.step("Signing in")
         adapter.login(...)  ──▶ ctx.wait_for_otp()  (status=awaiting_otp)
         save session_state (encrypted)
     adapter.select_brand(...)
     for each task (report × period):
         ctx.step("Downloading <report> <period>")
         files = adapter.download(...)
         store files → report_files (checksum, header, is_latest)
     release lock
  finalize run status, write manifest, send notification if failed
```

**Retries:** per task, max 2, with exponential backoff (30s, 120s) for `DOWNLOAD_TIMEOUT`, `PLATFORM_ERROR` and `PAGE_CHANGED`. `LOGIN_FAILED` is never retried automatically: it marks the account `needs_attention` to prevent lockouts. `WRONG_ACCOUNT` is never retried either — retrying cannot change the answer, and on portals that re-OTP on account switch it would burn a code for nothing. It marks the *connection*, not the account, as needing attention, because the credential is fine and the selector is wrong.

**Crash safety:** the worker writes a heartbeat to `runs.started_at`/Redis. The scheduler marks runs with no heartbeat for 10 min as `failed (WORKER_LOST)` and releases the lock (locks also have a TTL).

**Concurrency:** Dramatiq queue `rpa` with worker concurrency **2** (≈ 2 Chromium instances). Start at 2 and **measure RAM per headed Chromium under Xvfb before raising it** — headed with a persistent profile costs more than the headless figure the sizing in §10 was based on. Add a per-platform limit (e.g. max 2 concurrent Zepto) if any portal rate-limits.

## 6. Mailbox service (OTPs, links and report mail)

The most fragile part of the system. One IMAP service serves three jobs — OTP codes, magic links, and reports that arrive by mail (`delivery: email`, §4) — because they need exactly the same machinery: polling, freshness guards, a consumed-Message-ID set and a per-mailbox lock. Only the matching rule differs.

```python
async def wait_for_otp(mailbox, rule: OtpRule, since: datetime,
                       recipient: str, timeout=180) -> str:
    # poll every 4s:
    #   SEARCH SINCE <date> FROM <rule.sender>
    #   keep messages with Date >= since - 30s
    #   subject matches rule.subject_pattern
    #   if mailbox.kind == forwarded: recipient_matches(msg, recipient)   # see below
    #   Message-ID not in consumed set
    #   extract rule.code_regex or rule.link_regex from body
    # mark Message-ID consumed (Redis set, 1-day TTL); return value
```

Rules that prevent mix-ups:
1. **Time window:** only emails received after the login attempt started.
2. **Consumed set:** an OTP email is used once, never by two runs.
3. **Recipient match** for forwarded mailboxes, since several accounts forward into one inbox. Resolution order below.
4. **OTP lock:** `lock:otp:{mailbox_id}:{platform}` is held from "request OTP" to "OTP received". If two accounts on the same platform share a mailbox and the forwarded email cannot be told apart by recipient, they serialize instead of racing.
5. **Session reuse** (stored Playwright `storage_state`) skips the OTP entirely when the portal still trusts the session. This cuts OTP traffic and failure risk the most.

### Recipient matching, in order

```
1.  X-Forwarded-For / X-Forwarded-To header      (auto-forwarders that set it)
2.  the original To header                        (Gmail auto-forwarding keeps it)
3.  a "To:" line inside the body of a manual      ("---------- Forwarded message ---------"
    "Fwd:" email                                   then From:/Date:/Subject:/To:)
otherwise → no match is possible; the per-mailbox OTP lock (rule 4) serialises
logins so the time window alone is sufficient.
```

**This is all new code.** Not one legacy reader does any recipient matching: an exhaustive check of the prototypes shows only three headers are ever read — `Date`, `From`, `Subject`. They separate one login's mail from another's purely by sender substring + same-day + newer-than-baseline-UID + newer-than-click. That is safe only while a mailbox serves exactly one login, which is already untrue in three places (a shared Seller Hub mailbox, the Minutes relay, and the hand-forwarding described below).

**Manual forwards break the sender rule too, not just the recipient rule.** In a real saved sample, a Blinkit sign-in link was hand-forwarded by a person: the outer `From:` is the forwarder, not `brands@blinkit.com`, so a `FROM`-based IMAP search would not find the message at all — and the only recipient evidence anywhere in it is the plain-text `To:` line inside the forwarded body. So for a mailbox marked `forwarded`, `otp_rules.sender_pattern` must also be allowed to match the forwarder, and step 3 above is not a rare fallback but the common case.

Prior art worth porting: the Minutes reader already handles a forwarder that rewrites `From:` by falling back to scanning the day's mail from any sender and accepting only a message that matches the code regex **and** mentions the platform (`MINUTES_OTP_RELAY_SCAN`). Keep that as a per-rule opt-in.

### Report mail (`delivery: email`)

`wait_for_report_email(rule: ReportEmailRule, since)` is the same poller with three differences:

```python
#   SEARCH SINCE <date> FROM <rule.sender_pattern>
#   subject matches rule.subject_pattern
#   Date >= since          # since = when the adapter clicked Request, not login time
#   Message-ID not in consumed set
#   then either: save attachments matching rule.attachment_pattern
#           or: follow rule.link_regex and download what it serves
```

1. **`since` is the request, not the login.** A scorecard mailed last week must never satisfy this run.
2. **Timeout is per report, not the OTP's 3 minutes.** A queued export can take an hour. The task stays `running` with a live "waiting for the report mail" step; it does not go `awaiting_otp`.
3. **The link is a credential.** PartnersBiz and Blinkit both mail SendGrid-wrapped or presigned S3 URLs. They are logged redacted, never stored, and the fetched bytes go straight to `report_files` (`CLAUDE.md` rule 1).

Everything else — consumed set, per-mailbox lock, recipient matching for forwarded inboxes — is shared with the OTP path, so a forwarded mailbox behaves the same for a report as for a code.

**Before Stage 2 is signed off, capture one real sample per forwarding setup** (auto-forward, relay, manual `Fwd:`) as a redacted fixture in `backend/tests/adapters/fixtures/`. Redaction matters: the saved samples contain live magic links and presigned report URLs, which are credentials.

## 7. Scheduler

A loop that runs every 60 seconds:
```
SELECT * FROM schedules WHERE enabled AND next_run_at <= now() FOR UPDATE SKIP LOCKED
for each: resolve date range (rolling preset relative to today IST, or fixed)
          create run(trigger=schedule) + tasks; enqueue
          next_run_at = croniter(cron, now IST).get_next()
```
It also sweeps stale runs (section 5). Only one scheduler container runs; `SKIP LOCKED` keeps it safe if you ever run two.

Rolling presets: `yesterday`, `last_n_days(n)`, `month_to_date`, `previous_month`. For Blinkit, a schedule of "last 3 days, daily" gives automatic re-pulls of restated days. Versioning keeps both copies.

## 8. API surface (REST, `/api/v1`)

```
POST   /auth/login · POST /auth/logout · GET /auth/me
GET/POST/PATCH/DELETE  /users, /users/{id}/grants
GET/POST/PATCH/DELETE  /brands
GET/POST/PATCH/DELETE  /mailboxes          POST /mailboxes/{id}/test
GET/PUT                /smtp               POST /smtp/test
GET                    /catalog            (platform → category → report types, with portal and enabled flags)
GET/POST/PATCH/DELETE  /accounts           POST /accounts/{id}/test-login  → returns run_id
GET/POST/PATCH/DELETE  /connections
GET/POST/PATCH/DELETE  /schedules          POST /schedules/preview  (next 5 times)
GET/POST               /runs               POST /runs/{id}/cancel · POST /runs/{id}/retry
GET                    /runs/{id}          (tasks, events, files)
GET  (SSE)             /events/runs/{id}   · /events/runs (global feed for overview)
GET                    /files              (filters) · GET /files/{id}/download
POST                   /files/zip          (selection → zip stream)
GET                    /audit
```

Also: `GET/PUT /otp-rules` · `POST /otp-rules/test` (regex against pasted text or a recent mailbox email).

Every query that returns brand-scoped data goes through one dependency, `scope_to_user_brands(query, user, min_level)`. This is the single choke point for RBAC; write tests against it.

File downloads stream through the API after a permission check. There are no public or static file URLs.

## 9. Security

- **Encryption:** `secret_enc` fields are encrypted with a master key from env (`UNIQCAI_MASTER_KEY`). Keep that key outside the repo and outside backups of the DB.
- **Never leak secrets:** Pydantic response models exclude secret fields. Log filters mask passwords and OTPs. Playwright tracing/video is **off during `login()`** (traces record typed values). Failure screenshots are taken after navigation away from login forms where possible.
- **Auth:** argon2 password hashes, HTTP-only SameSite cookies, CSRF token on mutating requests, rate-limited login.
- **Audit:** every config change and file download is logged (PRD FR-45).
- **Transport:** HTTPS via nginx (Let's Encrypt if public; internal CA if on the lab network).

## 10. Deployment and the hosting decision

Everything ships as `docker-compose.yml`, so the host can be decided later.

**Browsers run headed, under Xvfb, by default.** This is not a fallback for a portal that misbehaves — it is the normal mode. The Zepto prototype runs headed deliberately because the portal sits behind AWS WAF bot protection, and the Flipkart login page states it is reCAPTCHA-protected. So the worker image ships Xvfb from day one and every adapter is written for it; a portal that turns out to tolerate headless is the exception, opted into per adapter.

**Sizing (Stage A):** 4 vCPU, 16 GB RAM, 100 GB disk. The ~300–600 MB per Chromium figure is the headless one; headed under Xvfb with a persistent profile costs more. **Worker concurrency starts at 2, and is raised only after measuring actual RSS per headed Chromium on the chosen host.** Budget disk for the persistent profiles too: one per `account_portal` at `/data/profiles/<account_id>/<portal_key>/`, and they grow.

**Checklist before choosing a host:**
1. **IP reputation.** Quick-commerce portals may challenge logins from datacenter IPs or new locations. Before committing, run your existing scripts from the candidate host for a few days. If captchas or extra verification appear, prefer the lab server or an Indian static IP.
2. **Static IP in India.** Consistent location means fewer "new device" OTP challenges. If cloud, use Mumbai/Hyderabad (AWS ap-south-1/2, GCP asia-south1).
3. **Always on.** Schedules need a machine that does not sleep.
4. **Access for SPOCs.** Brand users outside your network need the app reachable over HTTPS. A lab server needs a reverse proxy/tunnel (e.g. Cloudflare Tunnel) for that.
5. **Backups:** nightly `pg_dump` plus file storage sync to a second location.

Environments: `dev` (your laptop, headed browser for debugging adapters), `staging` and `prod`, as required by proposal §14.1. Staging uses test brands/accounts only; in Module 2 it is where campaign actions are validated against the test account and spend allowance (proposal §12). Adapters run headed under Xvfb in every environment, including prod.

## 11. Observability

- `run_events` is the user-facing timeline and also your debug log.
- Structured JSON logs from api/worker/scheduler.
- Overview page metrics come straight from the DB: success rate 7d, failures by error code, accounts needing attention, schedules due next.
- Optional later: Sentry for exceptions.

## 12. Repository layout

**`CLAUDE.md` is canon.** If this section and the folder map in `CLAUDE.md` ever disagree again, `CLAUDE.md` wins and this section is the one to fix. The scaffold on disk already follows it.

```
uniqcai/
├─ CLAUDE.md · README.md · Makefile          dev · test · types · migrate
├─ docs/                                     PRD · SYSTEM_DESIGN · UI_PLAN · THEME · PROGRESS · DECISIONS · research/
├─ legacy/                                   the working prototypes, reference only (see legacy/README.md)
├─ samples/                                  real downloaded reports, gitignored
├─ storage/                                  raw report files (dev); /data volume in prod
├─ infra/
│  ├─ docker-compose.dev.yml · docker-compose.yml · .env.example
│  └─ nginx/
├─ frontend/
│  └─ src/
│     ├─ app/                                router, providers, AppShell (sidebar + header)
│     ├─ theme/                              tokens.css generated from docs/THEME.md
│     ├─ components/
│     │  ├─ ui/                              shadcn primitives
│     │  ├─ common/                          StatusBadge · HealthPair · PlatformChip · StepTimeline · SecretInput · EmptyState
│     │  ├─ filters/                         FilterBar · filter definitions · useUrlFilters
│     │  └─ data/                            DataTable
│     ├─ features/<area>/                    one folder per screen area: page, sub-components, hooks, api calls
│     │                                      overview · brands · connect-wizard · runs · schedules · library · users · settings · audit · spoc
│     ├─ hooks/
│     └─ lib/                                api client · api-types.ts (generated) · sse.ts · format.ts
└─ backend/
   ├─ app/
   │  ├─ main.py                             FastAPI app
   │  ├─ core/                               config · db session · security · crypto · rbac (scope_to_user_brands) · events (SSE)
   │  └─ modules/<x>/                        router.py · service.py · models.py · schemas.py — one folder per domain
   │                                         auth · users · brands · mailboxes · catalog · accounts · runs · schedules · files · audit
   ├─ rpa/
   │  ├─ base.py                             PlatformAdapter · ReportSpec · RunContext
   │  ├─ registry.py                         portal_key → adapter class; seeds `portals` and `report_types`
   │  ├─ executor.py                         run/task loop, account locks, retries, error codes, heartbeat
   │  ├─ otp.py                              IMAP mailbox service: OTPs, links and report mail (§6)
   │  ├─ browser.py                          context per account_portal; storage_state and persistent profiles, encrypted
   │  ├─ storage.py                          raw file store: sha256, header row, is_latest, generated download filename
   │  └─ adapters/<platform>/<category>.py   zepto/ads.py · zepto/sales.py · blinkit/ads.py · blinkit/sales.py ·
   │                                         instamart/ads.py · instamart/sales.py · fkminutes/ads.py · fkminutes/sales.py
   ├─ workers/
   │  ├─ worker.py                           Dramatiq entrypoint
   │  └─ scheduler.py                        60s loop over `schedules`
   ├─ tests/
   │  ├─ unit/ · rbac/                       one RBAC test per endpoint
   │  └─ adapters/fixtures/                  saved emails, HTML snippets — redacted
   └─ alembic/
```

Two things to note against the older sketch this replaces: adapters are `<platform>/<category>.py`, not flat `zepto_ads.py`, because one platform folder holds both categories and shares helpers; and `rpa/browser.py` and `rpa/storage.py` exist because session handling and the raw-file store are duplicated in every prototype and get ported once (`CLAUDE.md` rule 4).

## 13. How Stage B and Module 2 attach

- **Stage B (validation):** each `report_files` row gets a `load_status` (extracted → validated → approved → published, or quarantined), matching proposal §5.3. Stage A writes `extracted`.
- **Stage B (unified data):** a new `parser` worker listens for new `report_files`, reads the raw file and writes to the warehouse using admin-maintained, versioned mappings (proposal §5.4), seeded from the schema docs (`raw_row_json`, `extracted_at`, idempotent upsert keys). Because every file is stored raw with its header, history can be re-parsed whenever a mapping changes.
- **Stage B (dashboards):** reads from the Stage B tables. RBAC scoping is the same `scope_to_user_brands` dependency.
- **Module 2 (campaign management):** adapters add an `actions` capability (`pause_campaign`, `set_budget`, …). These go through the same run/task/audit pipeline with an approval step, since they spend money.
