# Build prompts — one per stage

Use one Claude Code session per stage. Paste the prompt, review the plan it proposes, approve, let it build, test it yourself, commit, then clear the conversation and start the next stage.
Stages follow the working-flow plan: UI & access → Zepto first working flow → review gate → other platforms → testing & UAT.

---

## Stage 0 — Scaffold

```
Read CLAUDE.md and docs/SYSTEM_DESIGN.md §1, §2, §10, §12.
Scaffold the monorepo exactly as the folder map in CLAUDE.md:
- backend: pyproject (uv or pip-tools), FastAPI app with /api/v1/health, async SQLAlchemy + Alembic wired to Postgres, Redis connection, Dramatiq worker and scheduler entrypoints that start and log.
- frontend: Vite + React + TS strict + Tailwind + shadcn/ui + TanStack Query + React Router. Generate src/theme/tokens.css and the Tailwind config from docs/THEME.md (light + dark). An empty AppShell with the sidebar from docs/UI_PLAN.md §2.
- infra: docker-compose.dev.yml (postgres, redis, api with reload, worker, scheduler, frontend dev server) and .env.example. The worker image ships **Xvfb** and Playwright Chromium: adapters run headed by default (CLAUDE.md rule 10), and worker concurrency is 2.
- Makefile with dev, test, types, migrate.
Plan first. Done when `make dev` brings everything up and the app shell renders with theme tokens.
```

## Stage 1 — Auth, roles, brands, access (working-flow 1.1–1.3)

```
Read CLAUDE.md, docs/PRD.md §4 and FR-1…FR-6, FR-11, FR-12, docs/SYSTEM_DESIGN.md §3 (users, brand_grants, brands) and §9, docs/UI_PLAN.md §3.2 and §3.11.
Build:
- Login/logout with argon2 + HTTP-only cookie + CSRF; roles super_admin | admin | member; brand_grants with level manager | executive, can_trigger_runs, categories.
- core/rbac.py with scope_to_user_brands(query, user, min_level) and tests proving a member cannot see or fetch another brand.
- Brands CRUD + Users & access screens (invite, grant rows, chips like "Del Monte · Manager").
- A seeded super admin from env.
- Audit log table + middleware/helper that records create/update/delete (FR-45).
Plan first.
```

## Stage 2 — Catalog, mailboxes, OTP rules, credentials (working-flow 2.1)

```
Read CLAUDE.md, docs/PRD.md §5, §6, FR-7…FR-10, FR-13…FR-18, docs/SYSTEM_DESIGN.md §3, §6, docs/UI_PLAN.md §1a, §3.3, §3.9, §3.10.
Build:
- platforms, categories, platform_categories, portals, report_types tables, seeded from the adapter registry (registry can hold stub adapters for now).
- core/crypto.py (Fernet, key from UNIQCAI_MASTER_KEY). Secret fields are write-only everywhere.
- Mailboxes (direct/forwarded) with "Test connection" listing the latest 5 subjects.
- OTP & link rules: adapter defaults, portal/account overrides, and the rule tester (paste text or pick a recent email).
- Platform accounts + account_portals + connections, and the Connect platform wizard (Platform → Ads/Sales → login(s) with "same login" toggle → verification → reports). Test login can be a stub that streams fake steps via SSE for now, so StepTimeline is built and styled.
Plan first.
```

## Stage 3 — Adapter framework + Zepto **Ads**, live runs (working-flow 2.2, 3.1–3.2)

```
Read CLAUDE.md, docs/SYSTEM_DESIGN.md §4 (incl. session strategy), §5, §6, §8, docs/PRD.md FR-19…FR-25, FR-30…FR-37, docs/research/zepto-ads-schema.md, legacy/README.md, and legacy/zepto/ (zepto_session.py, otp_provider.py, report_engine.py, download_reports.py). Use samples/zepto/ to confirm report names and file formats.
Build:
- rpa/base.py (PlatformAdapter, ReportSpec with category and `delivery`, RunContext), registry.py, browser.py (context per account, storage_state restore/save encrypted), otp.py (time window, consumed Message-IDs, recipient match, OTP lock), storage.py (raw file store, sha256, header row, is_latest), executor.py (account lock, tasks, retries, error codes, failure screenshots, heartbeat).
- rpa/adapters/zepto/ads.py (portal key `zepto.ads`) ported from legacy with the report catalog from the Zepto schema doc (SP + SB × 6 reports, split-by-day support). Declare Sponsored Display's report types too, with `active = false`. `session_mode = persistent_profile` **and** save storage_state; on an invalid session, wipe the profile and log in fresh.
- Do **not** port `stamp_dates` / `stamp_dates_csv`: files are stored byte-for-byte and the period lives in `report_files` and the generated download filename (CLAUDE.md rule 6).
- `select_brand()` verifies the captured brand UUID against `connections.portal_brand_selector` and raises `WRONG_ACCOUNT` on a mismatch (CLAUDE.md rule 9).
- Runs API + SSE events; Run now drawer (Platform → Ads/Sales tree), live run view, Runs history, Report library with Ads | Sales tabs, versions, zip download.
- Real "Test login" wired to the executor.
Declare the full `delivery: browser | api | email` enum on ReportSpec, but **implement only `browser`** in this stage — `api` is Stage 4 and `email` is Stage 6. An adapter declaring an unimplemented delivery must fail loudly at registry load, not at run time.
Zepto Sales is Stage 4, not this stage. Test end to end against a real Zepto account in dev with a headed browser. Plan first.
```

## Stage 4 — Zepto **Sales** + schedules, T-15, notifications → complete Zepto flow

```
Read CLAUDE.md, docs/PRD.md FR-26…FR-29, FR-28a, FR-38…FR-45, docs/SYSTEM_DESIGN.md §4, §7, docs/UI_PLAN.md §3.1, §3.7, §3.12, §3.13, plus legacy/zepto/vendor_report_engine.py and legacy/zepto/docs/vendor-reports.md.
Build first: rpa/adapters/zepto/sales.py (portal key `zepto.vendor`) — the 13 vendor reports, `delivery: api` (implement that branch of the executor here): queue the report, poll until COMPLETED, fetch the presigned file. It shares the `zepto.ads` login and browser session (the API reads that session's cookie and takes the brand from the JWT), so it must never open a second browser or trigger a second login; the account lock already covers both. Port the max-days clamp into `max_range_days`.
Then build: schedules with CronBuilder + next-5-runs preview showing resolved date ranges; rolling/fixed ranges; "Refresh last 15 days" preset; category-level schedules; scheduler loop with SKIP LOCKED and stale-run sweep; SMTP profile + failure alerts; header-changed flag; run manifest.json; Overview page with the A/S health matrix; SPOC home; command palette.
Then write docs/ZEPTO_DEMO.md: a click-by-click script for the client review, covering **both** Zepto Ads and Zepto Sales — the gate is on the whole flow.
Plan first.
```

## Stage 5 — Zepto review gate (working-flow 2.3)

No build prompt. Demo to the client using `docs/ZEPTO_DEMO.md`. Log feedback in `docs/DECISIONS.md`, then:
```
Read docs/DECISIONS.md (latest entries). Plan and apply the Zepto review changes. Plan first.
```

## Stage 6 — Platform rollout (working-flow 4.2)

Run once per portal, in this order: Blinkit Ads (`blinkit.brandcentral`), Blinkit Sales (`blinkit.partnersbiz`), FK-Minutes Ads (`fkminutes.ads`), Instamart Ads and Instamart Sales (both `instamart.brandportal` — one login, one session), FK-Minutes Sales (`flipkart.sellerhub`, once its reports are confirmed). Zepto Sales is Stage 4, not here. legacy/README.md says which old files feed each adapter.

Blinkit Sales is where `delivery: email` gets built (PRD FR-19a, SYSTEM_DESIGN §4/§6): the adapter requests the PartnersBiz weekly scorecard in the portal, then the executor awaits it through the mailbox service using a `ReportEmailRule`. Reuse the OTP poller — same freshness guards, consumed set and per-mailbox lock — with a per-report timeout, not the OTP timeout.

Still blocked: the Instamart engine code was never imported and must be found before its adapters can be ported (PRD §12 Q13). Use the `/new-adapter` command, or:
```
Read CLAUDE.md, docs/SYSTEM_DESIGN.md §4 and §6, legacy/README.md (the row for this portal), the listed files in legacy/<platform>/, samples/<platform>/ for real output files, docs/research/<platform>-ads-schema.md if it exists, and backend/rpa/adapters/zepto/ads.py as the reference adapter.
Create backend/rpa/adapters/<platform>/<category>.py. Port login, OTP rule, brand selection and downloads from legacy; declare the report catalog with categories; verify the selected account/brand and raise WRONG_ACCOUNT on a mismatch (CLAUDE.md rule 9); add adapter tests with saved, redacted fixtures. No changes outside the adapter folder unless you explain why first.
Plan first.
```

## Stage 7 — Hardening, UAT, deploy (working-flow 5.1–5.3)

```
Read CLAUDE.md and docs/SYSTEM_DESIGN.md §9–§11.
Hardening pass: RBAC test coverage for every endpoint; secret-leak check (grep logs, traces, API responses); retry/backoff and lockout rules; rate-limited login; nightly pg_dump + file backup; production docker-compose with nginx + HTTPS; staging environment; a UAT checklist in docs/UAT.md covering every FR marked P0.
Plan first.
```

---

## UI polish prompt (use after any stage, or via `/ui-polish`)

```
Review the screens in frontend/src/features/<area> against docs/UI_PLAN.md and the "UI quality bar" in CLAUDE.md.
List every gap (missing states, feedback, keyboard, responsive, tokens not used, inconsistent spacing), then fix them.
```
