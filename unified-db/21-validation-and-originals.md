# 21 · Validation, and checking our numbers against the original files

The aim: anyone looking at a chart can open the exact file the platform gave us and see the same number.

## 1. The original is always kept and always downloadable

- Stage A already stores every file **byte-for-byte**, with a sha256 checksum (`rpa/storage.py:179` `store()`), and never rewrites it (CLAUDE.md rule 6). One gap: `store()` does not refuse an existing destination, and a resumed run once copied over a file with identical bytes; phase 1 makes it refuse (A6, [01](01-architecture.md) §5). Raw files are kept **for ever** ([23-performance.md](23-performance.md) §2).
- **Dates are not stored inside files.**
  - The period a file holds is a database fact: `report_files.period_start/end`.
  - The requested period is `run_tasks.period_*`.
  - The generated download name carries both dates: `<brand>_<platform>_<category>_<report>_<start>_<end>.<ext>`.
  - For Zepto, whose files have no date column, a date column is added **only to the download copy** (`app/modules/files/stamp.py`, DECISIONS:283): `Report_Date` for a one-day file, or `Report_Start_Date` + `Report_End_Date` for a range. The stored bytes and checksum are never touched.
- **Today the untouched Zepto original cannot be downloaded** (bug A5, [01-architecture.md](01-architecture.md) §5). Download and zip always serve the stamped copy, and the sha256 shown is the stored file's, so it never matches what the user receives. Phase 1 adds:
  - `GET /files/{id}/download?original=true`, which serves the stored bytes untouched, with an `X-Content-SHA256` header equal to `report_files.sha256`;
  - the same option on the zip download.
  A test downloads with `?original=true` and checks that the sha256 of the received bytes equals the stored one.
- The warehouse reads dates from `report_files` and from the file's own date column ([03-dimensions.md](03-dimensions.md), the date rule), never from a stamped copy. Stamped copies therefore cannot confuse it.
- Every fact row carries `load_id` and `report_file_id`, and every mart row carries `file_ids[]`. So every number leads to an original: fact → load → `report_file_id` → file.
- **An original is only as safe as its backup.** There is none today (bug A4). `make backup` and `make restore-check` (pg_dump plus an rsync or restic copy of the storage volume) and a restore drill are a phase 1 exit check.

## 2. "Source files" on every number

Every KPI tile, chart point and table row has a **Source files** action. It lists:
- the files behind the number: platform, report, period, extracted time, sha256;
- which version is current, and whether older versions exist;
- a download button for each file. It **defaults to the original** (`?original=true`). "With dates added" is the second option, for Zepto files only.

Downloads go through the existing files router, so the existing RBAC applies: a member cannot fetch a file outside their brands or categories.

This is the manual check the owner asked for. The client opens the platform's own export and compares it with what our chart shows.

## 3. Automatic checks on every load (before anyone sees it)

Each check writes a row to `ingest.checks` with its `check_key`, severity, expected and observed values. Details hold aggregates only, never client rows.

### Hard checks: a miss holds the load

The load goes to `quarantined` with a `quarantine_reason` and a re-pull suggestion. A quarantined load supersedes nothing ([04](04-grain-and-double-counting.md) §5).

| check_key | What | Why it is hard |
|---|---|---|
| `header` | every header has a row in the active mapping version (mapped or `ignore`), and every `metric` column of that version is present. A header change also sets FR-41's "Columns changed" | an unmapped column is listed on the admin mapping screen; nothing is guessed |
| `row_count` | rows parsed = data rows in the file (preamble excluded) | a reader that skips rows loads too little |
| `control_total` | Σspend, Σimpressions, Σrevenue in the raw file = Σ in the facts for that load. Summing duplicate rows to the grain ([04](04-grain-and-double-counting.md) §4) must not change these totals | the mapping lost or doubled money |
| `formula` | recompute the platform's own ratios from base columns: Zepto Roas, Cpc and Cpm (half-to-even); Blinkit Direct/Total RoAS; Instamart TOTAL_ROI, eCPM; FK ROI (Direct/Indirect), Action Rate, CVR; BigBasket ROAS, CPM. Fails above tolerance on more than 1% of rows | a column is mapped to the wrong target |
| `brand` | every raw brand value resolves through `wh.brand_aliases` to `report_files.brand_id` ([03](03-dimensions.md), the brand rule) | never guess a brand; never split a file |
| `date_in_period` | every date in a day-grain file falls inside `report_files.period` | the recorded period is wrong (bug A3) |
| `must_equal:<rule>` | "must equal" cross-report relations from `wh.reconciliation_rules`, on overlapping actual dates (below) | these relations are exact on every complete pull |

The "must equal" relations:
- FK Minutes `daily` = `fsn` = `placement` (±₹1);
- Instamart `auto_date` = summary = city = product = placement = **granular**. Granular = `auto_date` is what catches a truncated download;
- Zepto SB city, keyword and page = SB campaign;
- Zepto SP category, product and page ≈ SP campaign **per day** (±₹3). This catches files filed under the wrong day (bug A1): campaign, page and product shift together, but category does not, so category ≈ campaign fails on every affected day. A mislabelled SB file holding SP data (A2) fails the `header` check, because SB has no `Cpc`;
- Blinkit Σ daily spend = `MTD Claimables.served_budget_consumed` (±₹1). Product Booster campaigns run higher; they are flagged, not held.
- **Zepto range tiling, the independent check on every day file:** for each Zepto report, Σ of its day files over a calendar week (cut at month ends) = that week's **range pull** of the same report: impressions and clicks exactly, spend within max(±₹1 per day, ±₹0.50 per row of either side), because Zepto rounds every row. Orders are not compared: Zepto restates them for more than 7 days. A range with some days missing is still checked: the days present may not add up to more than the range. A range minus a range nested inside it is tiled too. Range pulls were never affected by the collector bugs; this is the comparison that found A1 (runs 64, 65, 68, 106 vs the day files). It does not depend on the report centre, row order or clocks, so it catches a mis-filed day even when every report of that day shifted together. It needs one range pull per report per week (18 reports × ~30 s ≈ 9 min per brand per week), seeded on in `ingest.report_policies`.

**Within one pull only** (2026-10-02, after adversarial verification). A must-equal relation holds or pulls back data only between files of the **same pull**: the same run, or the same chunked series; for a file without a run, `extracted_at` within 3 h. A1 happens inside one run, while reports pulled on different days legitimately differ by a few rupees. Across pulls the comparison is the soft check `drift:<rule>`: it records the gap, holds nothing, and the newest pull wins per slice.

A miss within a pull trusts neither side:
- the file that arrived is quarantined;
- that pull's current loads of the failing dates are **retracted** in one pass: the headline, the reports with a must-equal rule against it, and their coverage partners;
- a *dispute* on (brand, date, family, pull) holds the rest of that pull's files for the date;
- a held load acts on nothing; another pull is never touched, so the previous consistent pull comes back.

**Range tiling runs after the day files may already be published** (they are provisional for the restatement window anyway). A miss **retracts** every day load of that report inside the range, whichever side arrived second: the arriving day is quarantined with reason `must_equal:zepto_range_tiling`, the published days become `retracted`, and the range stays published. Retracted slices point back to their previous version (or to none). The marts are refreshed for those days, and the dates show as "Not available — being re-pulled". Retraction never deletes facts; it only moves `current_load_id`. Tiling alone cannot see a shift whose labelled days add up to less than every range containing them; the within-pull category ≈ campaign check removes those.

### Soft checks: shown on the load and on the dashboard

| check_key | What | Shown as |
|---|---|---|
| `coverage:<rule>` | coverage relations: keyword share, search-term share, Zepto SP city drift. The measured ranges are in [04](04-grain-and-double-counting.md) §2 | "keywords explain 61% of this spend" |
| `drift:<rule>` | a must-equal relation compared **across pulls** (the other report's current version came from an earlier pull). Records the gap per metric; never holds | "Differs from an earlier pull of a related report" |
| `null_rate` | share of NULLs per mapped metric, against that report's recent loads (PRD B2) | "Revenue empty on 40% of rows (usually 0%)" |
| `date_completeness` | for a day-grain report, every day in the period is present or explicitly empty | the missing days, in `coverage` |
| `empty_file` | a file with a valid header and no data rows (FK Minutes `zone` always; whole FK pulls sometimes). Published as "no activity" with 0 facts ([13](13-mapping-fk-minutes.md) §1) | "No activity in this file — check the account if the whole pull is empty" |
| `freshness_lag` (phase 3) | reports of the same pull end on different days. Instamart reports in one pull can differ by a day: `auto_date` held only 20 Aug while the others held 21 Aug | "Instamart city is a day ahead of its headline" |

There is **no duplicates check**. Rows sharing the declared grain are summed, not quarantined ([04](04-grain-and-double-counting.md) §4).

**Auto-approve** applies after 14 clean days per portal × report. Before that an admin approves (❓Q18).

The formula and cross-report checks were run on 2026-10-01 and 2026-10-02 against real files. The results are quoted in each platform's mapping file (10–15).

## 4. Restatement evidence

When a re-pulled slice changes, `wh.restatements` records the old value, the new value per key, both loads, both `report_file_id`s and both extraction times. Both originals stay downloadable. The client can see exactly when a platform changed its mind, and an admin can tell a platform restatement (`cause = platform`) from a mapping change (`cause = remap`).
