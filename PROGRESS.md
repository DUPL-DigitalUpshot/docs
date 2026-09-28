# Progress

| Stage | Working-flow ref | Status | Notes |
|---|---|---|---|
| 0 Scaffold | — | ☑ | Six services up, `/api/v1/health` green, baseline migration applied, headed Chromium verified under Xvfb, gitleaks wired |
| 1 Auth, roles, brands, access | 1.1–1.3 | ☑ | 404-for-invisible proven byte-identical; invites work without SMTP; login rate-limited; lockout guards |
| 2 Catalog, mailboxes, OTP rules, credentials | 2.1 | ☑ | M1 done: catalogue, mailboxes, OTP rules, accounts, wizard, SSE test login |
| 3 Adapter framework + **Zepto Ads** + live runs | 2.2, 3.1–3.2 | ☑ | `zepto.ads` downloads end to end — run 64, session reused, brand verified, file stored with checksum |
| 4 **Zepto Sales** + schedules, T-15, notifications | 2.2 | ◐ | **Schedules are done** (table, API, preview, firing, stale-run sweep). Left: `zepto.vendor` — a JSON API on the `zepto.ads` session, no second login — plus T-15 and notifications |
| 5 Zepto review gate | 2.3 | ☐ | Gate covers Ads **and** Sales |
| 6 Rollout: Blinkit Ads/Sales, FK-Minutes Ads, Instamart Ads/Sales, FK-Minutes Sales | 4.2 | ☐ | Instamart blocked: engine code was never imported (PRD §12 Q13) |
| 7 Hardening, UAT, deploy | 5.1–5.3 | ☐ | |

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
