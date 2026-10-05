# 01 · Architecture — four layers on top of Stage A

## 1. The layers

```
RAW        report_files + the untouched file on disk             exists today (Stage A)
  │  read           format reader per platform (parser_version)
STAGE      stage.parsed_rows — every source row, every column, as raw_row_json
  │  map            active mapping versions; an unmapped header → the load holds
  │  validate       hard checks hold the load; soft checks flag it
  │  approve → publish, slice by slice
WH         wh.fact_ad (versioned per slice) + wh dimensions + alias maps + wh.restatements
  │  refresh        only the (brand, platform, dates) a publish changed
MART       mart.ad_* rollups      ← dashboards and the metrics API read here

INGEST     control schema beside the layers, domain-agnostic (Sales reuses it):
           mapping_versions · column_mappings · loads · slices · checks · report_policies
```

**The rebuild rule.** Everything below RAW is a pure function of three inputs: the raw file, the `parser_version` and the active mapping versions. Changing a mapping creates a new version, and the affected files are loaded again as new loads. Nothing below RAW is ever hand-edited.

**One store, not one per platform or per brand.** Brand and platform are columns on every row. A cross-brand or cross-platform view is then a filter, not a join across databases. Brand isolation comes from the existing RBAC layer ([22-access-and-dashboards.md](22-access-and-dashboards.md)).

**`report_files` stays Stage A's record.** It is the immutable list of what was downloaded. The warehouse never writes to it; ingest state lives in `ingest.*` ([20-schema.md](20-schema.md)).

## 2. Where it runs

- **The existing Postgres 16 instance**, with new schemas `ingest`, `stage`, `wh`, `mart` (and `app` for saved views) beside the app tables. Migrations go through Alembic as usual (CLAUDE.md rule 5).
- **There are no backups today.** `SYSTEM_DESIGN.md` §10 ("Backups: nightly `pg_dump` plus file storage sync", line 393) states intent only; the Makefile and `infra/` have neither. Raw files are the only source for every rebuild and every cross-check, so `make backup` and a restore drill are part of phase 1 ([30-delivery-phases.md](30-delivery-phases.md)).
- **A new compose service, `parser`.** It is a Dramatiq worker on its own queue, **`ingest`**, sharing the broker in `workers/broker.py`. It has no browser and no Xvfb, so it never takes one of the two headed RPA slots (CLAUDE.md rule 10).
- **How a load is queued:**
  1. After the transaction that records a file commits (`rpa/executor.py:331` `_record_file`), the executor enqueues an ingest message for it. Only (portal, report) pairs with an active mapping **and** `ingest.report_policies.feed_warehouse = true` are queued, so Sales files are never queued for an Ads mapping.
  2. A scheduler sweep finds `report_files` rows that qualify but have no load for the current parser and mapping set. This is the outbox safety net for a lost message or a crash between commit and enqueue.
- **How a load is claimed.** `SELECT … FOR UPDATE SKIP LOCKED` on `ingest.loads`, the pattern the scheduler already uses (`workers/scheduler.py:68`). Work is idempotent on (`report_file_id`, `parser_version`, mapping set hash): a second message for the same key does nothing.
- **Stage A has no lease mechanism to reuse.** Runs are Dramatiq messages; a login is guarded by a Redis account lock (`rpa/executor.py:79`, TTL 3600 s) and a run heartbeat (`rpa/executor.py:113`, TTL 300 s). The parser relies on the row lock above, not on these.
- **Mart refresh** runs as a job after each publish, and touches only the (brand, platform, dates) that load changed.
- A separate warehouse server (ClickHouse, Timescale, …) is **not** planned. The triggers for revisiting this are in [23-performance.md](23-performance.md) §4.

## 3. Load states (PRD B2)

Each attempt to bring one file into the warehouse is a row in **`ingest.loads`**. A file can have several loads: a rebuild under a new mapping or parser is a new load of the same file. The state is not kept on `report_files`, for three reasons:
- a rebuild needs a new load, while `report_files` holds one row per file;
- Sales files have no Ads mapping and must never show as quarantined;
- `report_files` stays Stage A's immutable record.

A file with no load is **extracted** (Stage A today). `ingest.loads.status`:

| Status | Meaning | Set by |
|---|---|---|
| `queued` | load created, not yet claimed | executor or sweep |
| `skipped_duplicate` | the file's sha256 equals that of a file already published for the same brand, portal, report and period; nothing to do (5 copies of one Blinkit file exist today) | parser |
| `parsed` | rows in `stage.parsed_rows` | parser |
| `mapped` | canonical rows written to `wh.fact_ad` with this load's `load_id` and `slice_id`, and each slice's content hash recorded. A slice whose hash equals its current version writes no facts. These facts are **not current** until the load publishes | parser |
| `validated` | every hard check passed ([21-validation-and-originals.md](21-validation-and-originals.md) §3) | parser |
| `approved` | a person has accepted it, or auto-approve applies | admin ❓Q18 |
| `published` | slices applied ([04](04-grain-and-double-counting.md) §5): each changed or new slice's `current_load_id` now points at this load, so its facts are current and visible in marts | system |
| `quarantined` | a hard check failed, or the parser raised (`parser_error`); stored with `quarantine_reason` and a re-pull suggestion. A quarantined load **supersedes nothing**; its facts are never current and may be purged | any step |

Auto-approve is suggested once a portal × report has 14 clean days. Until then an admin approves. The owner of this step is ❓Q18.

**What is pulled at all** is an admin setting per report, `ingest.report_policies` (feed on/off, cadence, split by day, restatement window). The scheduler turns enabled policies into runs through the existing `create_runs` path (`app/modules/runs/service.py:300`), so RBAC, the account lock and the 2 h run cap (`workers/tasks.py:39`) still apply. Defaults and costs are in [04](04-grain-and-double-counting.md) §3.

## 4. What Stage A already gives us (reuse, do not rebuild)

| Need | Already there |
|---|---|
| immutable raw file, checksum | `rpa/storage.py:179` `store()`: `shutil.copy2` at :183, then sha256. It does not refuse an existing destination; see A6 |
| actual period held | `report_files.period_start/end` (DECISIONS L282); see bug A3 below |
| requested period | `run_tasks.period_start/end` |
| versions, latest flag | `rpa/executor.py:331` `_record_file`, `is_latest` |
| header and its hash | `report_files.header_row`, `header_hash`, `header_changed` (FR-41); see A6 |
| preamble detection | `rpa/storage.py:47` `looks_like_header` |
| brand / category scoping | `app/core/rbac.py:111` `scope_to_user_brands(..., category_column=)`, `app/core/rbac.py:36` `not_found()` |
| download a file | `app/modules/files/router.py:150` (RBAC-scoped). For Zepto it serves a **stamped copy** (`router.py:71–75`; download `:176–182`, zip `:222–224`), so `?original=true` is added in phase 1 (A5) |
| run creation, locks, run cap | `app/modules/runs/service.py:300` `create_runs` |
| row claiming | `workers/scheduler.py:68` `with_for_update(skip_locked=True)` |
| filter bar | generic FilterBar + filter definitions (CLAUDE.md "UI quality bar") |
| charts | Apache ECharts, the decision already taken (CLAUDE.md "Stack") |

## 5. Stage A bugs and gaps to close first (phase 1)

Found on 2026-10-02 by checking every stored original and the Stage A code. Each would load wrong numbers into the warehouse with nothing downstream to detect them.

| # | Finding | Evidence |
|---|---|---|
| A1 | **Zepto split-by-day files filed under the wrong day.** In run 161 the `campaign`, `city`, `page` and `product` files hold the day of the **previous exporting task** of that report; `category` and `keyword` are correct. Range pulls are unaffected. Root cause is the report-centre collector (`rpa/adapters/zepto/ads.py` `_collect`): a failed row is never consumed (:963–970), a task gives up on the first sight of any failed row while its own row is still in progress (:1014–1017), and rows are matched by report type only (:994–995), oldest first, so the next task of that report takes the leftover row. The same bug raised false `EMPTY_REPORT` in runs 66 (the SP range 1–21 Sep) and 160. Phase 1 restores the legacy semantics (failed rows consumed once, drain before deciding, refuse an ambiguous match) and relabels the stored rows with a guarded data migration; the bytes are never touched | run 161: category filed for 09-17 sums to ₹3,075, the same as campaign filed for 09-18; campaign filed for 09-24 equals category filed for 09-22, skipping the failed 09-23 tasks. The pattern holds on all 10 days |
| A2 | A file filed as Zepto **SB city** holds SP city data: it has `Cpc` (SB has none), and its spend is 96.2% of SP campaign. Same collector bug as A1; phase 1 adds an ad-type guard (an SB file must not have `Cpc`, an SP file must) and relabels the row | storage `2/zepto/ads/2026-09-19_2026-09-21/run67/` |
| A3 | **Instamart period.** The adapter pulls the end date back to yesterday (`rpa/adapters/instamart/ads.py:1107` `clamp_to_complete_days`) but returns a plain path (`:1129`), so the executor files the **requested** period (`rpa/executor.py:316–328` `file_period`). | a range ending today would be stored as ending today while holding data through yesterday. **No stored file is affected today** (0 rows) |
| A4 | **No backups** of the Postgres DB or the storage volume. | Makefile and `infra/`; `SYSTEM_DESIGN.md:393` states intent only |
| A5 | **The original cannot be downloaded for Zepto.** Download and zip always serve the stamped copy, and the sha256 shown is the stored file's, so it never matches what the user receives. | `app/modules/files/router.py:71–75`, `:176–182`, `:222–224`; `stamp.py` |
| A6 | Smaller gaps: | |
| | · `read_header()` (`rpa/storage.py:74`) returns None for xlsx (`:84`). Zepto Ads, Blinkit and Instamart Sales therefore have `header_row = NULL`, and "Columns changed" never fires for them. | |
| | · `header_changed` compares only against the same period (`rpa/executor.py:359–383`). Every split-by-day file and every daily MTD file has a new period, so it never fires for them. FR-41 says "the last file of the same report type". | |
| | · The version key (brand, portal, report, period, `is_latest`) is not enforced in the database. | |
| | · The login lock's TTL of 3600 s (`rpa/executor.py:79`) is never renewed, while a run may last 2 h. | |
| | · A Blinkit request spanning two months returns only the latest month (`rpa/adapters/blinkit/ads.py:317` ignores the start). Whether the portal honours a **past-month** end at all is unconfirmed and needs a supervised probe before the month-close pull is built. | |
| | · `storage.store()` overwrites an existing destination in place (`shutil.copy2`, `rpa/storage.py:183`). When run 106 resumed after a lost worker, rows 13–16 and 17–20 ended up sharing one storage path; the sha256 matched, so nothing was lost. Phase 1 makes `store()` refuse to overwrite. | |

The CLAUDE.md "Scope right now" amendment (P4 in [00-README.md](00-README.md)) is approved for phases 0–2.
