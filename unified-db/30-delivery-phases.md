# 30 · Delivery phases

**Platform order** follows the PRD rollout (PRD:277): **Zepto → Blinkit → FK Minutes → Instamart**, then Flipkart marketplace ads (if P1 says yes) and BigBasket (when it leaves "Coming soon"). Zepto goes first in every phase and passes the client gate before the others follow, the same rule as Stage A (PRD §11).

**Gate.** Stage B starts after the PRD step-7 sign-off (PRD:282); only the unified format for Zepto may run earlier. The approved round (2026-10-02) is therefore **phases 0–2**. On 2026-10-03 the owner waived the gate for **phases 4–5**, built on Zepto data as the analytics builder ([24](24-analytics-builder.md)); phases 3 and 6 still wait for it.

**Each phase** runs: plan → build → tests shown failing first → verify → docs. It ends with a short report to the owner before the next one begins (CLAUDE.md "How to work").

| Phase | Delivers | Exit check |
|---|---|---|
| **0 · Correct the design** | Files 01, 03, 04, 10–13, 16, 20, 21, 22, 30 and 40 updated with the 2026-10-02 review. DECISIONS entries: supersede 2026-09-21 L8 and L20, slice versioning, the ingest queue, the originals endpoint, the pull policy. CLAUDE.md "Scope right now" and rule 6 amended. `tools/column_inventory.py`, which reads the **storage originals** (never the stamped samples) and fails on an unclassified column | owner signs off (PRD Q10); the inventory runs green |
| **1 · Stage A prerequisites** | Fix A1 and A2 in the Zepto collector (`_collect`: failed rows consumed once, drain while an own row is in progress, refuse an ambiguous match, SB/SP `Cpc` guard), plus a guarded **data migration** that relabels the affected `report_files` rows (period, and `report_key` for the run-67 file) by id, sha256 and old period, never touching bytes; then re-pull the days left without a correct file. Fix A3 (Instamart returns its clamped period). `storage.store()` refuses to overwrite an existing file. xlsx headers for every sheet; FR-41 compares with the last file of the same report; the partial unique index on the version key (after the migration; 0 violations today); `?original=true` with `X-Content-SHA256`; the login lock renewed by the run's watcher; a Blinkit month-close option, after a supervised probe confirms the portal honours a past-month end, with a max(`date_ist`) = requested-end guard; `make backup` + `make restore-check` | each bug has a regression test shown failing first; `make test` and `make lint` green; a restore drill done and recorded |
| **2 · Ingest core + Zepto** | Migrations for the `ingest`, `stage` and `wh` schemas; the Zepto format reader; seeded Zepto mappings; loads, checks, slices, restatements; the `parser` service on queue `ingest`; `ingest.report_policies` with the admin **Warehouse feeds** screen (toggle, cadence, cost estimate) and policy-driven scheduling, with backfills chunked into runs that fit the 2 h cap; the admin **Loads** screen (status, checks, approve, quarantine reason); both screens added to `docs/UI_PLAN.md` first | every Zepto original parses; a renamed header holds the load; control totals match; re-pulling a day with the same content writes no facts; a changed day supersedes and both versions are queryable |
| **3 · Blinkit, FK Minutes, Instamart** (after the gate) | Format readers, mappings, declared grain and aggregation rules, reconciliation rules, in the PRD rollout order | every stored original reconciles; the truncated Instamart granular file is quarantined; the Blinkit restatement shows in `wh.restatements` |
| **4 · Marts + metrics API** | `mart.*` with incremental refresh, `mart.freshness`; `/api/metrics/catalogue` and `/api/metrics/query` with coverage per metric, freshness and source files | the RBAC tests below; NULL and coverage tests; a grep test for no `COALESCE(…,0)`; the p95 budget met on a throwaway 30-brand × 12-month synthetic Postgres ([23](23-performance.md) §5) |
| **5 · Screens** | the remaining Stage B screens added to `docs/UI_PLAN.md`; the mapping screen; ECharts; FilterBar `multiselect` and `daterange`; default dashboard with freshness; "Source files" panel (original first); saved views and personal dashboards; provisional / partial / restated statuses | Playwright UI checks; empty, loading, error and no-permission states; client UAT on Zepto, then each platform |
| **6 · Depth** | Keyword / search-query / city drill-downs with coverage share; long-range background queries; CSV/XLSX export (❓Q17) | the drill-down budget met |

## Tests that must exist (each shown failing before its fix)

Fixtures are built from headers and synthetic rows, never from committed client data. Checks against the stored originals report aggregates only.

- **RBAC** (`backend/tests/rbac/`):
  - the metrics API with another brand's id returns 404, with a body identical to the one for a missing brand;
  - a brand revoked after a view was saved disappears from that saved view's results;
  - a Sales-only grant sees no Ads metrics;
  - an empty brand selection returns no data;
  - saved views and dashboards of another user return 404;
  - the Loads and Warehouse feeds endpoints refuse members; `?original=true` is scoped like every other download.
- **Stage A fixes (phase 1):**
  - **Zepto collector:** with a stale failed row in the report centre, two tasks of the same report each receive their own file (today the first raises `EMPTY_REPORT` and the second takes the first's file); a task never raises `EMPTY_REPORT` while its own row is in progress; a leftover Success row that matches more than one task is refused as ambiguous; an SB task never returns an SP file;
  - **wrong-day file:** in ingest, a split-by-day Zepto campaign file holding the previous exporting task's day fails the per-day SP category ≈ campaign check;
  - **data migration:** relabels only rows whose id, sha256 and old period all match, and recomputes `is_latest`;
  - **storage:** `store()` refuses an existing destination;
  - **Blinkit month-close:** a file whose max(`date_ist`) is not the requested end is refused;
  - **original download:** the sha256 of the bytes served with `?original=true` equals `report_files.sha256` and the `X-Content-SHA256` header;
  - the Instamart file is filed under the period it holds;
  - xlsx headers are read; "Columns changed" fires for a split-by-day file.
- **Ingest (phase 2 onwards):**
  - **slice versioning:** a re-pull with identical content moves only `last_observed_at` and writes no facts; a changed slice supersedes all its rows in one transaction and writes `wh.restatements`; a slice missing from a newer file keeps its current version; an older file never replaces a newer one;
  - **truncated file:** a truncated Instamart granular file fails granular = `auto_date` and is quarantined; the good version stays current;
  - **quarantine supersedes nothing**, whatever the reason; the facts of an unpublished or quarantined load are never current;
  - **idempotency:** the same (file, parser version, mapping set) queued twice produces one load; an identical file is `skipped_duplicate`;
  - **duplicates are summed:** Blinkit bid-level rows sum to the declared grain, and the control totals are unchanged;
  - **brand:** a file whose brand column resolves to another brand is quarantined, never split;
  - **headers:** a renamed or new header holds the load.
- **NULL semantics:** a platform without clicks yields CTR "not available", never 0, and the total is marked partial in `coverage.metrics`. No `COALESCE(…,0)` appears in mart SQL (a grep test).
- **Double counting:** a query with no breakdown reads only `wh.headline_sources`. Summing two breakdowns is impossible through the API.
- The existing UniQCAI suite stays green after every commit.
