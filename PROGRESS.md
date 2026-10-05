# Progress

| Stage | Working-flow ref | Status | Notes |
|---|---|---|---|
| 0 Scaffold | — | ☑ | Six services up, `/api/v1/health` green, baseline migration applied, headed Chromium verified under Xvfb, gitleaks wired |
| 1 Auth, roles, brands, access | 1.1–1.3 | ☑ | 404-for-invisible proven byte-identical; invites work without SMTP; login rate-limited; lockout guards |
| 2 Catalog, mailboxes, OTP rules, credentials | 2.1 | ☑ | M1 done: catalogue, mailboxes, OTP rules, accounts, wizard, SSE test login |
| 3 Adapter framework + **Zepto Ads** + live runs | 2.2, 3.1–3.2 | ☑ | `zepto.ads` downloads end to end — run 64, session reused, brand verified, file stored with checksum |
| 4 **Zepto Sales** + schedules, T-15, notifications | 2.2 | ◐ | **Schedules are done** (table, API, preview, firing, stale-run sweep). Left: `zepto.vendor` — a JSON API on the `zepto.ads` session, no second login — plus T-15 and notifications |
| 5 Zepto review gate | 2.3 | ☐ | Gate covers Ads **and** Sales |
| 6 Rollout: Blinkit Ads/Sales, FK-Minutes Ads, Instamart Ads/Sales, FK-Minutes Sales | 4.2 | ◐ | Started ahead of the plan. **Instamart Ads downloads** (run 115, 23 Sep; the adapter was built from a live capture of the portal, since the prototype engine code (Q13) was never found). **Blinkit Ads** (Brand Central) stores its MTD search report (26 Sep). **FK-Minutes Ads**: adapter built, but Del Monte's connection currently fails `WRONG_ACCOUNT` (no ad account matches the mapped selector). Blinkit Sales, Instamart Sales and FK-Minutes Sales not yet run end to end |
| 7 Hardening, UAT, deploy | 5.1–5.3 | ☐ | |
| B0 Unified Ads DB — correct the design | `unified-db/30` phase 0 | ☑ | 2 Oct: design reviewed against every stored original and the Stage A code; docs/unified-db rewritten (v2); 15 DECISIONS entries; CLAUDE.md scope amended (owner approved). 37 mapping seeds (`backend/ingest/mappings/`) and `tools/column_inventory.py`, which classifies every stored ads header and fails on the mislabelled file (A2) |
| B1 Unified Ads DB — Stage A prerequisites | phase 1 | ☑ | 2 Oct: verified, merged and applied on dev; emptied days re-pulled and checked against range pulls (Zepto SP 17–28 Sep complete, 72 files). Left for later: Blinkit past-month probe (supervised) before the month-close pull is built |
| B2 Unified Ads DB — ingest core + Zepto | phase 2 | ◐ | 2 Oct: built, verified over 5 adversarial rounds, merged and deployed on dev (0012–0013, mappings seeded, parser running). All 111 stored Zepto originals load with 0 failed checks; they wait for admin approval (auto-approve after 14 clean days) |
| A2 Analytics query engine | `24-analytics-builder`, `an-query` | Verified | 3 Oct: 2,196 backend tests pass, 16 skipped; 47 targeted regressions and 520 oracle specs; all 32 budgeted performance cases pass, product table p95 786 ms. Fixes uncommitted, unmerged and undeployed |

## Stage 0 — what was verified (21 Sep 2026)

| Check | Result |
|---|---|
| `make dev` from a clean slate | **all six containers report healthy** |
| `GET /api/v1/health` | `200 {"status":"ok","checks":{"db":"ok","redis":"ok"}}` |
| `make migrate` | `0001 baseline` applied; `alembic_version` present in Postgres |
| Worker | Xvfb ready → **headed Chromium 131.0.6778.33** launched → Dramatiq booted, 2 threads |
| Queue | `ping.send()` from api → actor ran in the worker |
| Scheduler | 60 s ticks, logged with `tz: Asia/Kolkata` |
| App shell | renders at 1440×900; all 10 sidebar items; no console errors |
| Theme | light `--bg-app` `#fafbfc`, sidebar `#0d1014`; dark `#0d1014` / `#080a0d`; `--brand-600` `#2a45cc`; Inter loaded — all matching THEME.md |
| Contrast | every status badge ≥ 4.5:1 in both themes, verified in the browser and pinned by `contrast.test.ts` |
| Healthchecks | each negative-tested: stale heartbeat, dead display and dead broker all fail as they should |
| Routes | every UI_PLAN area resolves, including `/spoc` and a 404 |
| `make test` | 4 backend + 34 frontend, green |
| `make lint` | ruff, tsc and eslint clean |
| `make types` | `api-types.ts` regenerated from the live OpenAPI schema |
| `make secrets-check` | no leaks in history; the three custom rules each fire on a planted secret |
| `pre-commit run` | all 10 hooks pass |

### Open before Stage 1

- **Docker is a snap on the dev host** and its `removable-media` interface is disconnected, so it cannot read this repo under `/media`. Stage 0 was verified from a copy under `$HOME`. Fix with `sudo snap connect docker:removable-media`, or move the repo under `$HOME`, or install Docker from apt instead of snap.
- **Port 5173 is already in use** on the dev host. `FRONTEND_PORT` in `infra/.env` moves it.
- **`--text-muted` was darkened** from `--gray-500` to `--gray-600` in light mode to clear AA on `--bg-app` and `--bg-subtle`. Every timestamp and helper label is slightly darker as a result — worth a look before Stage 1 builds screens around it. Reverting is one line in THEME.md §4.

## Stage 1 — what was verified (21 Sep 2026)

**Tests:** 81 backend (32 of them RBAC) + 39 frontend. The backend suite runs against a real Postgres, schema built by `alembic upgrade head` — so every run also proves the migration.

| Check | Result |
|---|---|
| Invisible brand vs missing id | `404` with a **byte-identical body**; asserted across four guessed ids |
| Sub-resources (`/brands/{id}/access`) | same 404, same body |
| Admin-only mutations | refused identically for every id, so the reply never varies with existence |
| Manager editing a brand record | `403` — PRD §4 gives Managers credentials and schedules, not the brand |
| Executive changing grants | `403`, including on themselves |
| Members on `/users`, `/audit` | `403`; anonymous anywhere `401` |
| Archived brands | invisible to members even with a grant, and `archived=all` cannot be used to opt in; admins see them behind the filter |
| Invites | show-once, hash-only storage, single-use under a row lock, 7-day expiry, revoke and reissue |
| Password reset | 24h, single-use, revokes existing sessions on issue; cannot be crossed with an invite token |
| Login | unknown email and wrong password are byte-identical; 5/15min per email, 10/15min per IP, `Retry-After` |
| CSRF | missing or mismatched header refused; token rotates on sign-in |
| Cookies | `HttpOnly`, `SameSite=Lax`, `Secure` outside dev |
| Lockout guards | no self-demote, self-deactivate, self-ungrant or self-reset; last active super admin protected; an inactive one does not count as cover |
| Deactivation | existing sessions dropped immediately, not at cookie expiry |
| Audit | login success/failure/rate-limit/logout/reset/revoke recorded; no password ever appears in the log |

**Browser walkthrough** (headed Chromium, admin and SPOC in separate contexts, zero console errors):
sign in as the seeded super admin → forced to `/change-password` and bounced back when trying to skip it → set a real password → create two brands → invite a SPOC and copy the link → accept it in a separate context → the same link a second time is refused → SPOC with no grants sees an explanatory empty state → admin grants `Del Monte · Executive` → SPOC sees exactly one brand and the Executive sidebar → SPOC opens the other brand's URL and gets "Brand not found", identical to a nonexistent id → SPOC opens `/users` and gets "You don't have access" → admin archives the brand and the SPOC's list empties while the admin sees it under "Archived".

### Open before Stage 2

- **Docker is a snap on the dev host** and its `removable-media` interface is disconnected, so it cannot read this repo under `/media`. Verified from a copy under `$HOME`. Fix with `sudo snap connect docker:removable-media`, or move the repo under `$HOME`, or install Docker from apt instead of snap.
- **Port 5173 is already in use** on the dev host. `FRONTEND_PORT` in `infra/.env` moves it.
- **`--text-muted` was darkened** from `--gray-500` to `--gray-600` in light mode to clear AA on `--bg-app` and `--bg-subtle`. Reverting is one line in THEME.md §4.
- **Rate limiting reads the peer IP directly.** Stage 7 must put nginx in front and trust `X-Forwarded-For` only from that proxy, or the per-IP limit is bypassable.

---

# Build mode — milestones

Functional parity with `legacy/` is the bar. Resume a session with
"Continue from docs/PROGRESS.md".

| Milestone | Status | Notes |
|---|---|---|
| M1 Finish Stage 2 | ☑ | accounts/connections, wizard, real SSE, screens |
| M2 Run engine | ☑ | browser, OTP poller, executor, storage, Run now, live run view, library |
| M3 Zepto Ads | ☑ | ported from legacy/zepto; first real download 22 Sep (run 64) |
| M4 Zepto Sales | ☐ | **next** — vendor API on the Ads session |
| M5 Blinkit Ads + Sales | ☐ | |
| M6 FK Minutes + Seller Hub | ☐ | |
| M7 Instamart | ☐ | engine code missing — see Blocked |
| M8 Schedules, Overview, SPOC home | ◐ | schedules ☑; Overview, SPOC home and Settings are still `PlaceholderPage` |
| M9 SMTP delivery | ☐ | |

## Exact next step

**M4 — Zepto Sales** (`zepto.vendor`). Zepto Ads landed on 22 Sep and the
schedules half of Stage 4 is built, so what is left of Stage 4 is the vendor
API, T-15 and notifications.

1. `backend/rpa/adapters/zepto/sales.py` — replace `NotImplementedAdapter`.
   It declares `delivery="api"` and `shares_session_with = "zepto.ads"`, so:
   * the executor needs its `api` branch — queue, poll, fetch — where `page`
     may be `None`;
   * add `"api"` to `IMPLEMENTED_DELIVERIES` only once that branch exists, or
     the registry refuses the adapter at import, which is the point of it;
   * **no second sign-in.** It rides the `zepto.ads` session under the same
     account lock. Opening a second browser for it is the bug to avoid.
2. T-15 re-pull and the notification hooks.
3. Then Stage 5, the Zepto review gate, which covers Ads **and** Sales — and
   which needs a named approver on the client side (asked for in
   `docs/client/FLOW.md` §11).

## Tooling — watching the RPA browser (22 Sep 2026)

Built ahead of M3, because it is what makes debugging a selector port practical
rather than guesswork.

The worker has always run Chromium **headed** on Xvfb (CLAUDE.md rule 10);
there was simply no way to look at it. `UNIQCAI_BROWSER_VIEW=on` now attaches
x11vnc to that display, exactly as the legacy bootstrap scripts did, with
websockify/noVNC in front so it opens in a browser tab.

```
# infra/.env
UNIQCAI_BROWSER_VIEW=on
UNIQCAI_BROWSER_SLOW_MO_MS=400     # pace Playwright so a login is followable

make up            # NOT 'docker compose restart' — that reuses the old env
make watch         # prints the URL
```

Dev only: the viewer has no password, so the entrypoint logs `viewer_refused`
and starts nothing when `UNIQCAI_ENV` is not `dev`, and compose publishes the
ports to `127.0.0.1` only. Nothing about how the browser runs changed.

Works before M3: restarting the worker shows the Chromium preflight open and
close, which proves the whole path.

## M2 — what was built (21 Sep 2026)

`rpa/browser.py`, `rpa/otp.py` (poller), `rpa/executor.py`, `rpa/storage.py`,
`rpa/errors.py`, migration `0004` (`run_tasks`, `report_files`), the Run now
drawer, the live run page, Runs history and the Report library with Ads | Sales
tabs, versions and zip download.

Backend 231 tests, frontend 42. The engine is ported from the prototypes, not
redesigned — the behaviours that look odd are the ones the prototypes needed:

- a persistent profile **and** a saved cookie jar, because Zepto's token is a
  session cookie Chromium drops on exit;
- a UID baseline taken before the login click, plus a 60 s clock-skew grace;
- a consumed Message-ID set, so two runs never share a code;
- `WRONG_ACCOUNT` never retried — the retry yields the same believable file for
  the wrong business.

## M1 — what was verified (21 Sep 2026)

Browser walkthrough, zero console errors: sign in → add brand → add mailbox →
**Test connection** returns "The server rejected those credentials. For Gmail
this must be an app password, not the account password…" → OTP rules tab shows
the adapter default with an **Unverified** badge → the tester matches pasted
text, says pasted text cannot verify, and leaves **Save and mark verified**
disabled → Connect wizard (Zepto → Ads → login → mailbox + in-portal selector →
27 report types listed, inactive ones explained) → **Save and test login**
streams live steps over SSE (Browser started → Credentials entered → Waiting
for the code → Code received → Signed in → Brand selected) → Accounts page
shows the login, its brand and per-portal health → Runs history records it.

Backend: 204 tests. Frontend: 39.

### Two bugs found by running it, not by tests

- **Dramatiq had no broker in the API process.** `workers/tasks.py` declared
  actors without setting one, so Dramatiq fell back to its default at
  `localhost:6379` and every enqueue from the API failed. The run sat at
  "queued" with nothing in the UI to explain why. Fixed with
  `workers/broker.py`, imported by both the API and the worker.
- **The worker could not map `runs.account_id`.** It imported `Run` but not
  `PlatformAccount`, so SQLAlchemy raised `NoReferencedTableError` at mapper
  configuration. The API only worked because its routers happened to import
  everything. Fixed with `app/models.py`, imported by the worker, Alembic and
  the test harness; a test asserts it covers every table.

## Blocked — needs Vishnu

- **Instamart engine code (M7).** `legacy/instamart/*.py` are shims importing
  `upshot.platforms.instamart.*` from a `src/` tree that was never imported.
  Either find it, or M7 becomes a rewrite from `download_reports.py`,
  `download_sales.py` and the saved HTML in `legacy/instamart/docs/`.
- **Real portal credentials and mailbox app passwords.** Not recoverable from
  `legacy/`: every `config.py` was deleted and the history rewritten when the
  credentials were rotated (DECISIONS, 21 Sep). What survives is placeholders —
  `<REDACTED>` and `you@example.com`. They have to be entered once, by hand, in
  the UI.

  **Everything that is not a secret is already configured.** The senders,
  regexes, subject filters and the Minutes relay flag were ported from the
  legacy `config.example.py` files into the adapter defaults, so the OTP rules
  need no typing:

  | Portal | Sender | Pattern | Login |
  |---|---|---|---|
  | `zepto.ads` | `mailer@zeptonow.com` | `otp code is\s*(\d{4,8})` | password + OTP |
  | `blinkit.brandcentral` | `brands@blinkit.com` | SendGrid click-wrapped link | link only |
  | `blinkit.partnersbiz` | `noreply@partnersbiz.com` | `One Time Password \(OTP\)\s+(\d{4,8})` | OTP only |
  | `instamart.brandportal` | `no-reply@swiggy.in` | subject `Login OTP` | OTP only |
  | `fkminutes.ads` | `flipkart.com` | `\b(\d{6})\b`, relay scan **on** | password + OTP via relay |
  | `flipkart.sellerhub` | `noreply@rmo.flipkart.com` | `Your OTP:\s*(\d{4,8})` | password → picker → OTP |
  | `zepto.vendor` | — | rides the `zepto.ads` session | none of its own |

  Every rule ships `verified = false`: none has been matched against a real
  email yet. The rule tester marks one verified once it has.

  **What still has to be entered, in the UI, per platform:**

  1. **Mailboxes** → the inbox address and its Gmail **app password** (not the
     account password; two-step verification must be on). Tick *"Several logins
     forward into this inbox"* for a forwarded or relay inbox and list the
     addresses that forward in — that list is what matches a code back to the
     account that asked for it.
     Legacy used `imap.gmail.com`; the Zoho hosts it also supported are
     `imap.zoho.in`, `imap.zoho.com`, `imap.zoho.eu`.
  2. **Connect platform** wizard → the portal login id, and the password for
     the two portals that have one. Leave the password blank for Blinkit
     Brand Central, PartnersBiz and Instamart: the code or link *is* the
     credential there.
  3. **In-portal brand or entity** (wizard step 3) wherever one login carries
     several businesses — Instamart, Flipkart Seller Hub, PartnersBiz. This is
     what `WRONG_ACCOUNT` checks before every download.
  4. For **Flipkart Minutes**, point the account at the *relay* inbox, not the
     login address: the portal mails the personal account and the relay
     receives the forward. Matching uses the login id, so it still lines up.

  Type them into the UI rather than putting them in a file: the UI encrypts on
  save, whereas a seed file would put plaintext credentials back on disk —
  which is the thing the rotation exercise was undoing.
- **Mail fixtures.** Ten files listed in
  `backend/tests/adapters/fixtures/mail/README.md`. The matcher is built and
  its tests skip by name until they land. OTP rule defaults come from the
  legacy `config.example.py` senders and regexes meanwhile.

## 2026-09-23 — Brand discovery and mapping, and Instamart Ads downloads

**Instamart Ads is downloading.** Run 115 stored
`UQ_AUTO_SUMMARY_20260915_20260921_063448.csv` for Del Monte, 19 KB, with
`Brand selected and verified` — so rule 9's read-back passes against a mapped
selector on the path that actually uses it. The file states its own window:
`From Date,15/09/2026` / `To Date,21/09/2026`, exactly as requested.

Four real faults were behind the long date-picker hunt, and only the last one
was the widget:

1. **The session had silently expired.** Instamart does not navigate on expiry
   — a modal covers the page while the URL stays `/reports` and the brand stays
   in the sidebar — so a URL-only `is_logged_in` read it as signed in and the
   modal's overlay ate every click. This alone presented as a dropdown that
   timed out, a date that "did not take", and a calendar that offered days and
   ignored them.
2. **The trigger's format is `15/09/2026`,** not `15 Sep 2026`, so the
   read-back rejected a date that had in fact been set.
3. **The read-back compared only the day number,** which would have accepted
   `22/09` for a requested `22/08` — a complete, believable report about the
   wrong month.
4. **An ordinary click closes the popup without committing.** Calling `click()`
   on the element commits; clicking at its position does not.

**Brand discovery** replaces typing `portal_brand_selector` from memory:

- `PlatformAdapter.list_brands` → `BrandList`, concrete so non-enumerating
  portals are unaffected, opted into via `capabilities`.
- `account_portal_brands` (migration `0007`), written on test logins only.
- `GET /accounts/{id}/brands`, `POST /accounts/{id}/connections`, both with
  RBAC tests.
- `BrandMappingDialog` with `suggestBrand`: an identical name arrives ticked,
  a fuzzy match unticked and badged, a tie not at all.
- `0007` also adds the `(brand_id, account_id)` unique constraint `connections`
  never had.

Instamart's switcher (`side-panel-v2-account-switcher-trigger`) reports one
brand for the Del Monte login, which is the true answer for it. A portal that
cannot show its list says so rather than reporting none.

### Known gap

`report_files.header_row` for Instamart records `['Selected Filters', '', …]` —
the CSV's filters preamble, not the column header on row 6. `header_changed`
therefore watches a constant and can never fire for this platform. The stored
bytes are correct and untouched (rule 6); only the recorded header is wrong.

## 2026-09-23 — UI visibility switchboard (`toggle_admin`)

A runtime switchboard for what each audience is shown, owned by a fourth role that no admin can see. Built outside the stage plan, at the client's request.

**What it does.** Any nav section, platform, category or report type can be marked `visible`, `locked` ("coming soon": greyed, lock icon, tooltip, inert) or `hidden`, per sidebar audience (`admin`, `manager`, `executive`). Locked and hidden routes bounce a typed URL back to the Overview. Rules live in `ui_visibility`, keyed `(audience, kind, key)`; an absent row means visible, so an empty table behaves exactly as before the feature existed.

**What it is not.** Presentation only. A hidden section is still a 200 for anyone whose role allowed it, and a rule can never grant an audience something it never had. RBAC is untouched — see `DECISIONS.md` 2026-09-23 and PRD §4a.

**The role.** `toggle_admin` ranks above `super_admin` in `ROLE_ORDER`, so every existing gate passes unchanged, and it is never subject to the rules it writes. Unlike the sections, the *role* is hidden server-side: filtered from `GET /users`, refused as the source or target of any promotion or invite, and its endpoints answer 404 rather than 403. Seeded from `UNIQCAI_TOGGLE_ADMIN_EMAIL` / `_PASSWORD`; no screen can create one.

| Piece | Where |
|---|---|
| Migration | `0008_ui_visibility.py` — new table, `ck_users_role` widened |
| Backend | `app/modules/visibility/`, `RequireToggleAdmin` in `core/rbac.py`, guards in `modules/users/service.py`, `seed_toggle_admin()` |
| Rules delivery | `GET /auth/me` → `CurrentUserResponse.visibility` (no extra request; already cached under `['me']`) |
| Frontend | `app/sections.ts` (one registry), `lib/visibility.ts`, `navFor(audience, rules)`, `RequireSection`, `features/visibility/` |

**Verified so far:** frontend `tsc`, `eslint` and `vitest` green — 101 tests, 12 new (8 in `app/nav.test.ts`, 4 sidebar rendering cases in `AppShell.test.tsx`). Backend `ruff check` and `ruff format` clean.

**Not yet run — the environment had no Docker access:** `make migrate` (0008 has never been applied), `make test` (backend pytest, including the new `tests/rbac/test_visibility_rbac.py` and `tests/unit/test_visibility_rules.py`), `make types`, and the browser walkthrough. Until `make types` runs, `lib/api.ts` carries a `PENDING REGENERATION` block declaring the two fields the generator will supply; delete it once `api-types.ts` is regenerated.

## 2026-09-26 — Navigation and "Applies to" (from the VNM layout pattern)

Built outside the stage plan, after reviewing the VNM multi-entity layout document. Frontend only: no migrations, no endpoints, so no new RBAC tests.

| Piece | Where |
|---|---|
| "Applies to" + typed confirm | `components/common/WorkTarget.tsx`; used in `RunNowDrawer`, `ScheduleDialog`, `BrandMappingDialog`, `AccountsPage` delete/disconnect, archive brand |
| Brand avatar | `components/common/BrandAvatar.tsx`, `avatar.ts`; tokens `--avatar-1…8` (THEME.md §6a) |
| Brand sections as URLs | `features/brands/BrandLayout.tsx` (replaces `BrandDetailPage.tsx`), `useBrand.ts`, `BRAND_SECTIONS` + `switchTarget` in `app/sections.ts` |
| Switcher + trail | `app/BrandSwitcher.tsx`, `app/ContextTrail.tsx`, `app/crumbs.ts`, `components/ui/dropdown-menu.tsx` |
| Shell | `AppShell.tsx`: persisted collapse, Ctrl/⌘+B, phone drawer, skip link; `LiveRunPage` sticky header; Run now drawer closes on Esc from anywhere |

**Verified:** `tsc`, `eslint` and `vitest` green, with 174 tests (35 new). Checked in a browser at 1440×900 and 390×844 against a mocked API: every route renders with the right trail and no horizontal scroll; switching goes `/brands/1/runs → /brands/2/runs` and `/runs/1286 → /brands/3/runs`; brand search works; `?tab=runs` redirects; Run now shows "Applies to" and "Start run for …"; the archive button stays disabled until the name is typed; Ctrl+B survives a reload; the phone drawer closes on navigation.

**Amended the same day:** the brand switcher moved to the top of the sidebar and the toggle to the start of the header, as in the VNM document (`DECISIONS.md`). 175 tests; the browser pass was repeated at both widths.

**Not run:** `make test` (backend untouched) and a pass against the live API, because this environment has no Docker access.

## 2026-09-26 — Dates on Zepto downloads, and a file's real period

Commits `cbc0ebb` and `a600996`. The reasoning is in `DECISIONS.md` (2026-09-26).

| Piece | Where |
|---|---|
| A stored file records the period it holds, not the period requested (Blinkit MTD) | `DownloadedFile(path, period_start, period_end)` from `download()`; migration **0009** relabels the existing Blinkit rows and recomputes `is_latest` |
| Zepto's period is added to the download, never to the stored file | `app/modules/files/stamp.py`, opted in by `ReportSpec.stamp_period_on_download`; the library marks such files "Date added" |
| Month to date is a range | Run now preset, resolved in IST (`features/runs/ranges.ts`); the schedule preset's "1 Oct – 30 Sep" on the 1st is fixed |

The live API reports migrations at **0009** (health check, 28 Sep).

## 2026-09-28 — The brand in context brings its own sections (branch `visibility-switchboard`, uncommitted)

"Brands" leaves the sidebar for everyone. While a brand is open, a *This brand* group lists Connections · Schedules · Reports · Runs · Access, and the group beneath is headed *All brands*. The switchboard keeps its Brands row (it guards `/brands`, every brand page and the switcher). Decisions: `DECISIONS.md` 2026-09-28; screen: UI_PLAN §2.

Files: `app/Sidebar.tsx`, `app/nav.ts`, `app/BrandSwitcher.tsx`, `app/ContextTrail.tsx`, `app/router.tsx`, new `app/useBrandSections.ts` and `features/overview/HomeRoute.tsx`, `features/brands/BrandLayout.tsx`, `modules/visibility/service.py`, and tests in `app/nav.test.ts` and `AppShell.test.tsx`.

**Not recorded here:** the test run for this change. Run `make test` and `make lint` before committing.

## 2026-09-29 — Client videos: the admin walkthrough, and a home for the next ones

Built outside the stage plan, for a client demonstration. There's no app code, migration or endpoint, so there are no RBAC tests.

| Piece | Where |
|---|---|
| The video: 1 min 55 s, 720p, narrated, 10 labelled steps | `docs/client/videos/demo/admin-walkthrough/video.mp4` (+ `poster.jpg`, `captions.en.vtt`) |
| Watch page: player, chapters, written steps, download | `…/admin-walkthrough/index.html` + `video.json`; shared `videos/shared/watch.{css,js}` |
| Index of all videos, grouped by type | `docs/client/videos/index.html` + `catalog.json` |
| Recording kit: captions, highlight, cursor, pacing to the voice | `videos/_tools/demo_kit.py`, `overlay.js`; the storyboard is in `…/source/record.py` |
| Voice (local Kokoro), build (ffmpeg), new-video setup | `_tools/tts.py`, `build.py`, `new_video.py`; how-to in `videos/README.md` |

Recorded as `owner@digitalupshot.com` (Super admin) against the live dev stack, viewing screens only: no save, no run. Runs, Schedules, Report library, Users & access, Settings and Audit log are **locked for the Admin audience** in the switchboard, so the video shows them as "Coming next" (see `TOGGLE_ADMIN.md`).

**Verified:**
- **Recording:** a dry pass of the storyboard ran through every screen against the live app.
- **Build:** `build.py` rebuilt the published video from the recorded take with the same length, loudness and chapter times.
- **Pages:** the watch page and index render with no errors, chapters seek correctly, and nothing scrolls sideways at 390 px. Checked in Chromium with the files served in-process; a local web server wasn't allowed.
- **Live:** the first push served the page without styles, caused by Jekyll dropping `_shared/`. The rename to `shared/` has **not yet been checked live**.

**Open:** the video shows real brands and addresses. It needs sign-off before it stays public (`DECISIONS.md` 2026-09-29).

## 2026-10-01 — Cancel a run (FR-35)

There's a **Cancel run** button on the live-run dialog and the run page. It asks once ("Stop run #N?"), and appears only for unfinished runs the viewer may stop. Decisions are in `DECISIONS.md`, 2026-10-01.

| Piece | Where |
|---|---|
| `POST /api/v1/runs/{id}/cancel`, `RunDetail.can_cancel` | `modules/runs/router.py` |
| The cancel as one transaction; `set_status` changes only unfinished runs; `run_is_open` | `modules/runs/service.py` |
| `watch_run` (cancel watcher and heartbeat), `_hold_open` before every task commit, `RunClosed`, a login lock owned by its run | `rpa/executor.py` |
| Re-delivered jobs for finished runs are skipped | `workers/tasks.py` |
| The sweep claims a run before reporting `WORKER_LOST` | `workers/scheduler.py` |
| Button and confirm | `features/runs/CancelRunButton.tsx`, used by `LiveRunDialog.tsx` and `LiveRunPage.tsx` |

No migration: `cancelled` was already a run and task status.

**Tests:** `tests/rbac/test_runs_rbac.py::TestCancelRun` (who may cancel, 404 vs 403, 409 once finished); `tests/unit/test_run_cancel.py` (a failure part-way rolls the cancel back completely; a cancelled run can't be revived; a task commit and a cancel serialise on the row lock in either order; the watcher stops the run; a worker shutdown isn't mistaken for a cancel; lock ownership); `CancelRunButton.test.tsx`. Backend: 672 passed, 10 skipped. Frontend: typecheck, lint and the new tests pass.

**Not verified:** cancelling a real run in the browser end to end. The worker must be restarted to load the new executor code (`docker compose … restart worker`).

**Still open (not in this change):** `run_download`'s 2-hour `time_limit` ends a long run partway. 30 Zepto reports at about 15 minutes each need around 7 hours, so large batches should be split into smaller runs.


## B0 — Unified Ads DB, phase 0 (2 Oct 2026)

| Check | Result |
|---|---|
| Design vs Stage A code | 4 claims wrong (no lease mechanism, no backups, no untouched-original download for Zepto, warehouse decision L8 unsuperseded) — corrected |
| Design vs stored originals | grain wrong for Blinkit KT/CT (bid-level rows), Instamart search_query and granular; "granular 37 %" was a truncated download; Blinkit Σdaily = served on ≥95 % of campaigns; Claimables = min(served, budget) on 693/693; restatement windows measured (Blinkit/Instamart ~3 d, FK-Minutes revenue >7 d) |
| Stage A bugs found | Zepto collector files reports under the previous task's day (39 files) and once filed SP as SB; Instamart period clamp (0 rows affected); lock TTL; `store()` overwrite; 2 h cap not enforced |
| Zepto cost | 22–45 s per report-day; all 18 daily = 10.9–12.1 min per brand (the "14–16 min" figure was one report over a 30-day run) |
| `pytest tests/unit/test_mapping_seeds.py tests/tools/test_column_inventory.py` | 303 passed, 6 skipped (inactive SD) |
| `make test-backend` | 986 passed, 16 skipped |
| `tools/column_inventory.py` on the storage volume | exit 1 on file 8 (SP data filed as SB city); exit 0 with it excluded; 731 rows, 0 data values |

## B1 — Unified Ads DB, phase 1 (2 Oct 2026)

Five workstreams, each built in its own worktree and attacked by a separate verifier before merging.

| Workstream | What is now true | Verified by |
|---|---|---|
| Zepto collector (A1, A2) | a task claims only a row it can prove is its own, or refuses; SB/SP files checked by their `Cpc` column; browser runs on India's clock | 4 verifier rounds, 98 collector tests, run 161 and 67 replays; clean daily pull 0 refusals, timing unchanged |
| Data repair | 40 mis-filed rows moved to the day/ad type they hold (0010); one latest file per key enforced (0011) | rehearsed twice on copies of the live DB; every true day re-derived from range pulls; live: "relabelled 40 of 40" |
| Storage + headers | xlsx headers on every sheet; FR-41 across periods; `store()` never overwrites; Instamart files the clamped period; header backfill tool | all 157 stored originals + 468 samples read; live backfill fixed 114 rows, 0 false flags |
| Runtime | lock renewed (300 s TTL), compare-and-delete everywhere; run deadline inside the actor limit; chunked runs; Cancel stops a series; busy login re-queues; never-started runs swept after 24 h; no SQL in user messages; Blinkit MTD date guard | 2 verifier rounds + attack suites; live: run 88 (queued since 22 Sep) ended `NOT_STARTED` |
| Originals + backup | `?original=true` streams the stored bytes with their sha256; dated copy labelled; `make backup` / `make restore-check` | RBAC tests; live backup 3 s, restore-check 157/157 files match |

| Check | Result |
|---|---|
| Full backend suite (merged) | 1255 passed, 16 skipped |
| Frontend | 223 tests, typecheck and lint clean |
| `ruff check --config ruff.toml backend tools` | clean (the old executor I001 fixed) |
| `tools/column_inventory.py`, no exclusions | exit 0 — every stored ads header classified (file 8 now under SP city) |
| Re-pulls (runs 174–177) | all 11 days filed; every file equals independent evidence (category files, range differences): e.g. 23 Sep campaign 19,098 impressions = range arithmetic. Run 175 exposed a failed export recorded as "no data" — fixed as `EXPORT_FAILED` and re-pulled (run 177) |

## B2 — Unified Ads DB, phase 2 (2 Oct 2026)

Four workstreams: A schema, B pure reader, C loader and runtime, D admin screens. Each was built in its own worktree; C and D were attacked by a fresh verifier in five rounds before merging.

| Workstream | What is now true | Verified by |
|---|---|---|
| A schema (0012) | schemas `ingest`, `stage`, `wh`; monthly partitions attached without blocking reads; `make seed-mappings` never edits an active mapping | 37 mappings rebuilt from the DB equal their YAML; partition lock and DEFAULT-race tests |
| B reader | Zepto reader + mapper + per-file checks (header, row count, control totals, formula half-to-even, brand, dates); content hash over identity and numbers only | all 111 stored originals: 9,707 rows, every hard check passes, raw totals = canonical totals |
| C loader (0013) | loads → slices → facts at map time; publish by newest `extracted_at`; restatements; must-equal hard **within one pull**, soft `drift:` across pulls; range tiling that never pulls back a newer file and holds an older disagreeing range; one lock order; `parser` service on queue `ingest`; outbox sweep, partitions, retention; `make ingest-backfill`, `make ingest-dry-run`; Zepto window 14 days | independent truth on 106 slices, 0 mismatches; with 0010 undone, 0 mis-filed slices current in every arrival order (9 tried); true labels 0 holds; Zepto cross-pull drift never blanks a day; 0 deadlocks in every race mode |
| D admin screens | Warehouse feeds (switch, window, weekly reconciliation, schedules and cost, "create the recommended schedule") and Loads (DataTable, URL filters, drawer with checks in words, Approve / Quarantine / Retry) | RBAC tests; action states = loader's; race tests through the router; 0 name leaks against stored names |

| Check | Result |
|---|---|
| Full backend suite (unified-db) | 1802 passed, 16 skipped |
| Frontend | 290 tests, typecheck and lint clean; api-types in sync |
| `ruff check --config ruff.toml backend tools` | clean |
| Deploy on dev | backup + restore-check 168/168; migrate 0013; 31 active + 6 draft mappings (Sponsored Display stays draft); parser, worker, scheduler healthy; the scheduler's sweep loaded all 111 Zepto files: 111 validated, every hard check passed (444 control totals, 102 cross-report), 9,707 rows |

Open:
- **Approve the 111 validated loads** (Warehouse → Loads). Publishing is an admin decision until 14 clean days. There is no bulk approve for loads that already exist.
- Not built in phase 2: `freshness_lag` (phase 3). Known limits are recorded in DECISIONS 2026-10-02:
  - tiling alone misses some shifts; the within-pull check covers them;
  - a wrong day approved before its week's range stays visible until the week is re-pulled, and the held range says so.
- Blinkit past-month probe (supervised), carried over from B1.

## U — Unified data in the UI (3 Oct 2026)

Plain business words, a review inbox, brand set-up, and data status for brand users (plan approved 3 Oct; DECISIONS 2026-10-03). Four workstreams, each attacked by a separate verifier; three final-check rounds before merging.

| Stream | What is now true |
|---|---|
| Words | one glossary (`lib/words.ts`); import / Checking… / Waiting for your OK / Published / Held back / Pulled back; no enum, key, id or file name outside *Technical detail* — `findJargon` fails any page test that shows one; 0 hits across 24 rendered page views |
| Needs attention (`/data`) | waiting imports as weekly cards with **Publish all**; held items in one sentence with **Re-pull** (starts a run through Run now), **Import again**, **Mark as handled** (migration 0014); progress to automatic publishing |
| Reports, Imports | feed switch, *Pulled by*, weekly cross-check, *Set up a brand* (≤ 3 schedules, idempotent, joins an existing daily); Imports with chips, **Publish selected**, a drawer that Back and Esc close, *Open the run*, *See in Library* |
| Brand **Data** tab | the brand twin of Unified data: admins get that brand's inbox, imports and set-up; brand users get *Data through*, held days and *Provisional*, within their category grant, never a figure |
| Elsewhere | Library data-status badge and filter, *Columns changed*; Schedules badge, stop warning, amber partial, *One file per day*; switchboard row *Data status* |

| Check | Result |
|---|---|
| Backend suite (unified-db) | 1940 passed, 16 skipped; ruff clean |
| Frontend | 538 tests, typecheck and lint clean |
| On a copy of live | 108 waiting imports → 30 weekly cards; publishing all of them: data matches the stored files (105/105 slices); re-pull created a run on the copy only; brand switch shows one brand only; managers and executives: restricted on `/data`, status words and dates only |
| 390 px | Library, brand Data tab and Unified data pages: no sideways scroll |
| Deploy on dev | backup + restore-check; migrate 0014 (renamed the 3 old "Warehouse …" schedules, audited); api, parser, worker, scheduler healthy |

Open: run screens in plain words, a per-brand data calendar, ⌘K (owner's choice, next round); a period filter on `GET /files` so *See in Library* never misses a file beyond the latest 100; Postgres row-level security by brand with the metrics API (phase 4).

## A2 - Analytics query engine verification (3 Oct 2026)

**Status: A2 verified on `an-query`.** The earlier
669-pass partial run was not verification. These fixes were subsequently
committed as `3f0909e` on `an-query` and integrated into the isolated
`an-builder` branch. Nothing is merged into `unified-db` or deployed. Dev
remains on the Unified data screens and migration 0014. A5/A6 add visible
charts in a separate preview, recorded below.

Changes:
- Active report/ad-type metadata is loaded into the internal catalogue using
  the owner session before entering `uniqcai_reader`. The compiler no longer
  reads `ingest.mapping_versions`; reader grants and policies are unchanged.
- Filtered coverage includes published empty reports and ignores unselected
  historical SB reports when answering SP ranges. Exact non-overlapping range
  tiling, authoritative headline totals, paired ratios and NULLs are preserved.
- Breakdown queries filter platforms/partitions before aggregation, validate
  publication once per slice, and reuse their grouping sort. Coverage shares
  reuse existing sums only for an explicitly selected single platform;
  unfiltered orphan-platform breakdowns retain separate shares.
- Breakdown planning uses transaction-local `force_custom_plan` and `work_mem`
  of 64 MiB per plan node, with a regression proving rollback restores both.
  This is not a global database setting or a process-wide memory limit.
- Earlier review hardening is retained: disabled filters do not add source
  dependencies, extended-metric filters bypass headline caching, duplicate
  reports do not double-count, product names respect platform/brand scope,
  percentages guard NULL/zero totals, and Top N preserves retained headlines.
  The public API is unchanged.

| Check | Final result |
|---|---|
| Targeted A2 compiler and semantics regressions | 47 passed; includes real reader-role coverage, settings rollback, orphan-platform shares, extended metrics and source-file provenance |
| Both numerical-oracle seeds through the real service | Pass in the final full suite: seeds `20261003` and `7`, 260 generated specs each, 520 total |
| Complete backend suite | 2,196 passed, 16 skipped in 883.60 s; isolated Postgres/Redis, database `uniqcai_test_a2_verify`; one SQLAlchemy non-active-transaction warning in unchanged `test_run_hardening.py` |
| Final independent adversarial review | Orphan-platform share attribution finding fixed and covered by a reader-role regression; reviewer confirmed the fix, with no other concrete query regression identified |
| Backend/tool lint | `ruff check backend tools` clean using root `ruff.toml`; changed Python files pass format check |
| Frontend | `npm run typecheck` and `npm run lint` pass |
| Final uncached performance matrix | 40/40 cases complete, 800 samples, all 32 budgeted cases pass; eight longer-table observations without a defined budget; no HTTP or EXPLAIN errors |

Performance methodology: authenticated ASGI requests through the real
catalogue/compiler/reader/RLS/Redis service path; 40 cases, 20 measured samples
per case after one warm-up, every response `cached=false`. Synthetic data:
30 brands, five platforms, 365 days, 6,570,000 fact rows and 2,190,000 campaign
mart rows. Selections are Zepto-only, for one brand or all 30, over 1/3/6/12
months. The budgets are the explicit rows in `23-performance.md`; 6/12-month
tables are recorded without an invented one-second acceptance threshold.

Final 30-brand Zepto server p95, milliseconds:

| Shape | 1 month | 3 months | 6 months | 12 months |
|---|---|---|---|---|
| Tiles | 66 | 116 | 265 | 463 |
| Weekly trend | 61 | 157 | 322 | 600 |
| Platform split | 70 | 117 | 262 | 467 |
| Campaign table | 133 | 203 | 329 | 569 |
| Product table | 446 | **786** | 1,535 | 3,144 |

The three-month product-table blocker was reported at 2,284 ms; the final
snapshot measures 786 ms, below its 1,000 ms target. The 12-month product-table
observation exceeds three seconds and is retained as a longer-period UX/load
consideration, not described as passing a nonexistent table budget.

Evidence is retained on this host under
`/home/ai-centre-01/.cache/uniqcai-a2-verification/`: full-suite and regression
JUnit XML, `backend-final.tar.gz`, benchmark scripts and README, plus
`performance-final-rerun/` with every timing sample, request/response, captured
SQL, EXPLAIN (ANALYZE, BUFFERS, SETTINGS), source diff and image/commit identity.
EXPLAIN replays the service's transaction-local planner settings. Earlier
failed/partial measurements remain separate and are not final acceptance.

Limits: warm database/OS buffers, regular synthetic cardinalities, sequential
requests, and only daily/current data in the performance fixture. This is
not evidence for cold-cache or concurrent production load, all-platform
queries, 50-150 million rows, or browser/network latency. Range/restatement
and access-control correctness are covered by tests, not this benchmark.
Concurrent memory sizing remains a deployment check because work memory is
per plan node, potentially multiplied by parallel workers.

Verification containers/networks and the synthetic benchmark data volume were
removed after completion. Artifacts remain; existing dev services were not
restarted or modified. Subsequent A1/A2/A3/A4 integration and A5/A6 work are
recorded below. Merging into `unified-db` and deployment remain separate.

## A5/A6 - Analytics builder and dashboards (3 Oct 2026)

**Status: implemented and verified on isolated branch `an-builder`.**
The existing `unified-db` worktree and dev services remain unchanged. The
preview uses synthetic published Zepto data only, not live brand data.

| Stream | What is now true |
|---|---|
| Integration | Verified A1 marts, A2 query engine, A3 dashboard API and A4 frontend groundwork are integrated into `an-builder`; generated API types match the combined OpenAPI schema |
| Migration | No-op merge revision 0018 joins 0016/0017 without rewriting their ancestry; upgrades from either analytics head are tested |
| A5 builder | Catalogue fields, keyboard/pointer drag-and-drop and plus controls; rows/series/values/filter wells; aggregation, per-level calculations, show-as, nested any/all filters and impact; period overrides, Top N, sort, formatting, axes and reference lines |
| Charts | All 16 catalogue chart types, ranked/pivot tables with authoritative totals, NULL preservation, freshness/coverage/status markers, accessible table views, point/cell Source files and untouched-original downloads |
| A6 dashboards | Global and brand routes; six-KPI Ads overview, spend/ROAS trend, platform split and campaigns; URL filters; desktop grid editing, mobile view-only; versioned save/save-as, 409 draft retention, undo/redo/reset, dirty-navigation guards |
| Reuse and access | My charts, saved views, templates, sharing and version restore; Ads grants and visibility control navigation; shared queries and provenance use the viewer's own grants; incompatible saved charts do not blank other widgets |

| Check | Result |
|---|---|
| Entire integrated backend suite | 2,301 passed, 16 skipped, 977.08 s; isolated Postgres/Redis; `uniqcai_test_analytics_integration`; one existing non-active-transaction warning in `test_run_hardening.py` |
| Additional preview-tool safety regressions | 12 passed after the full suite; reject ordinary databases and URL connection overrides before connecting |
| Entire final frontend suite | 888 passed across 76 files; includes 74 new analytics/dashboard tests; existing Router future-flag and Radix `act` warnings remain |
| Final real-service Playwright checks | 15 workflows pass; zero page errors; a blank chart built in 2.62 s; all 16 encodings render; every checked canvas is painted and framed |
| Browser correctness/access | Six KPI oracle with paired ratios; empty brand selection; brand/ad-type/date URL totals; save/reopen; real 409 and save-as recovery; filters with impact; keyboard DnD; reset/reuse/views/template/restore; manager-only results/provenance; Sales-only denial |
| Browser layout/themes | 1440 px dashboard/editor, 1024 px editor, 390 px mobile light/dark; no page overflow or clipped dashboard KPI/canvas; mobile has no chart/dashboard editing controls |
| Tooling | Backend/tools Ruff and changed-Python format checks pass; frontend types/lint/production build pass; regenerated combined API types compare byte-for-byte |

Evidence: `/home/ai-centre-01/.cache/uniqcai-a5-a6-verification/` holds
backend/frontend JUnit, preview-guard JUnit, the synthetic seed manifest,
`browser-check.json`, screenshots, the combined generated schema and preview
logs. Reproducible tools: `tools/analytics_preview.py` (requires an empty,
already migrated `uniqcai_test` database) and `tools/analytics_browser_check.py`
(loopback synthetic preview only; creates its own check dashboards).

Preview: `http://127.0.0.1:5175/analytics`, API on loopback port 8001,
isolated containers `uniqcai-analytics-{postgres,redis,api}`. Public disposable
login: `preview.admin@example.com` / `Synthetic-Preview-Only-2026!`.
No ingestion worker, scheduler, portal login or live data is used by this
preview. The existing dev containers were not restarted.

Limits and remaining work:
- Merge into `unified-db`, backup/migration/deployment rehearsal, and showing
  actual published brand data in dev remain separate release steps.
- A2 compiler, catalogue, service and spec are unchanged from the verified
  snapshot; integrated mart refresh hardening is covered by the backend suite. Its 30-brand
  uncached performance evidence remains in the A2 entry; this small browser
  seed is correctness/UX evidence, not a new production-load benchmark.
- Vite reports >500 kB chunks (main ~1,033 kB, lazy ECharts ~665 kB before
  gzip). Build passes; further bundle splitting is a release optimization.
- Other-platform ingestion, Sales analytics and phase-6 CSV/XLSX exports are
  still outside this approved round.

## Navigation usability review (3 Oct 2026)

**Status: implemented and verified on isolated branch `ui-navigation`.** The
existing dev app and `unified-db` worktree remain unchanged.

- Audited 14 desktop routes and three mobile routes against the isolated
  Dinshaw's Zepto reporting snapshot. The main issue was repeated brand and
  all-brand destinations at the same visual weight, followed by internal labels
  and duplicate Run now actions.
- The default sidebar now exposes only high-frequency destinations. Secondary
  work is grouped under accessible `Manage brand`, `Operations`, and
  `Workspace setup` disclosures; the group containing the current route opens
  automatically.
- Scope is explicit (`This brand`, `All brands`), and ambiguous/internal labels
  use plain language: `All-brand analytics`, `All reports`, `Data status`,
  `Data quality`, `Run history`, `Platform logins`, `Email inboxes`,
  `People & access`, and `Activity log`.
- Run now appears once in the global header. On a brand route the same drawer
  starts with that brand selected.
- All 890 frontend tests pass across 76 files. Typecheck, lint and production
  build pass; the existing Router/Radix test warnings and >500 kB bundle warning
  remain. Real-service Playwright checks pass for disclosures, active routes,
  keyboard operation, current-brand Run now, desktop/mobile framing and zero
  page errors.

Preview: `http://127.0.0.1:5177/analytics/2`, using the isolated real-data demo
API on loopback port 8002. Evidence and before/after screenshots are under
`/home/ai-centre-01/.cache/uniqcai-real-data-demo/`.

## Dashboard table modal (4 Oct 2026)

**Status: implemented and verified on isolated branch `ui-navigation`.**

- The table icon on every dashboard widget now opens an almost full-screen,
  responsive data dialog instead of replacing the chart inside its card.
- The dialog reuses the complete table experience: filters, sorting, column
  visibility, authoritative totals, freshness/coverage, status markers and
  source-file drill-down. Closing it returns to the unchanged chart.
- The complete frontend suite passes: 893 tests across 77 files. Typecheck,
  lint and the production build pass; existing Router/Radix test warnings and
  the existing >500 kB bundle warning remain.
- Real Dinshaw's Zepto data was checked at 1440 x 1000 and 390 x 844. The modal
  settles at 1280 x 976 and 366 x 820 respectively, stays inside the viewport,
  creates no page overflow and reports zero browser errors.

Preview: `http://127.0.0.1:5177/analytics/2`. Screenshots and the reproducible
browser check are under
`/home/ai-centre-01/.cache/uniqcai-real-data-demo/dashboard-table-modal/`.

## Analytics visual refresh (4 Oct 2026)

**Status: implemented and verified on isolated branch `ui-navigation`.** A
provided commerce-dashboard screenshot was used as visual direction, without
copying its navigation, branding or product-specific recommendations.

- The default dashboard now uses three wider KPI cards per row over two rows,
  rather than six narrow tiles. Each KPI keeps its authoritative server total
  and adds a daily sparkline from the same query response.
- KPI cards now lead with label, headline and trend. The redundant per-card
  period was removed because the dashboard filter already states it; chart
  overrides remain explicit. Partial, provisional, restated, coverage and
  source-file semantics are preserved as supporting information.
- Lines use restrained smoothing and low-opacity area fills, larger graphs use
  readable `17 Sep` date labels instead of ISO strings, and provenance member
  keys remain unchanged. Card titles, actions, padding and table-modal spacing
  now share one compact visual rhythm.
- Chart-quality metadata now sits in a bottom `Data status` footer rather than
  above the visual. It says `Some data missing`, `May still change` and
  `Updated` instead of exposing unexplained Partial/Provisional/Restated tags.
  `Data details` opens a popover with the exact definitions and platform/date
  coverage without resizing the chart.
- The complete frontend suite passes: 893 tests across 77 files. Typecheck,
  lint and production build pass. Real Dinshaw's Zepto checks show eight
  painted canvases, no viewport overflow and zero page errors at 1440 px and
  390 px in light and dark themes.

Preview: `http://127.0.0.1:5177/brands/2/analytics`. Screenshots and the
reproducible browser check are under
`/home/ai-centre-01/.cache/uniqcai-real-data-demo/dashboard-visual-refresh/`.

## Chart editor usability (4 Oct 2026)

**Status: implemented and verified on isolated branch `ui-navigation`.**

- The permanent field catalogue is replaced by contextual `Add field` and
  `Add value` menus beside the destination they affect. Each menu is searchable,
  groups business fields by meaning, hides incompatible choices by default and
  can reveal their reason on demand.
- The setup flow now reads `Chart type`, `Break down by`, `Compare series`,
  `Measure`, `Filters` and `More options`. Only selected fields remain on screen;
  filters and advanced settings use progressive disclosure.
- Those six setup sections now have restrained, theme-aware background tints,
  giving non-technical users consistent visual landmarks without colouring the
  controls or changing their meaning.
- Filter members use a searchable checkbox picker with a compact selection
  summary instead of a tall native multi-select. Existing saved members remain
  selected even when their display label is unavailable.
- Query specs, calculations, filters, field ordering, chart switching and the
  server-authoritative preview are unchanged. No API or persistence format
  changed.
- The complete frontend suite passes: 896 tests across 77 files. Typecheck,
  lint and production build pass; the existing Router/Radix test warnings and
  >500 kB bundle warning remain.
- The real Dinshaw's Zepto `Campaign spend` editor passes at 1440 px and
  1024 px with zero browser errors and no viewport overflow. The field picker,
  unavailable-field disclosure and two saved filters were exercised through
  the running service.
- The real Dinshaw's Zepto `CPC` editor was also checked in light and dark
  themes; all six computed section backgrounds are distinct and the editor has
  no viewport overflow or browser errors.

Preview: `http://127.0.0.1:5177/analytics/2`. Screenshots and the reproducible
browser check are under
`/home/ai-centre-01/.cache/uniqcai-real-data-demo/chart-editor-simple/`.

## Data consistency hardening phases 1-3 (4 Oct 2026)

**Status: implemented and verified on isolated branch `ui-navigation`; not
merged or deployed.**

- Migration 0019 adds a row-level-secured mart refresh outbox. Publish and
  retract transactions durably record the affected brand/platform/date range;
  the scheduler retries pending, failed and stale work every minute, and the
  parser completes work atomically with the mart update.
- Analytics responses expose `refreshed_at`, `refresh_pending` and
  `pending_since`. Pending work changes cache identity immediately. Dashboard
  widgets poll every 30 seconds, offer manual refresh and show `Updating data`
  with platform detail while refresh work is incomplete.
- Duplicate declared grains are named hard failures. After five comparable
  published files, unexpected emptiness and row or metric-total movements
  outside 20%-500% of the recent median are soft review warnings.
- Backend: 2,321 passed, 16 skipped on isolated PostgreSQL/Redis. Frontend:
  897 passed across 77 files; typecheck, lint and production build pass. Ruff
  passes. Existing SQLAlchemy and Router/Radix test warnings remain.
- Backup rehearsal passed: `backups/20261004T023148Z` restored into the
  throwaway database with matching key-table counts, and all 170 stored files
  matched their SHA-256 hashes.
