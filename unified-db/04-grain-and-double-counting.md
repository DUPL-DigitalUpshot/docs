# 04 · Grain, double counting and restatements

This is where a unified store most easily shows wrong numbers. Every rule below comes from a measured failure on real files, re-checked on 2026-10-02 against every original in the storage volume.

## 1. One campaign, many reports, one spend

The same ad spend is reported again in each breakdown report: campaign, keyword, city, product and placement. Adding up all of a platform's files counts the spend once per report.

Every fact row carries a `breakdown`. The values are `campaign`, `keyword`, `search_query`, `product`, `category`, `city`, `placement`, `zone`, `order`, `halo`, `creative`, `booking`, `granular` or `account`. **A breakdown alone does not prevent double counting:** Instamart `auto_summary` and `auto_date` are both `campaign`, and Blinkit's headline spans four sheets.

**Rule:** totals and KPI tiles read only the platform's **headline sources**, an explicit set of (portal, report, sheet) in `wh.headline_sources` ([20-schema.md](20-schema.md)). Every other query names exactly one breakdown report. Summing two reports is impossible through the API.

| Platform | Headline sources (portal · report · sheet) | Why (measured) |
|---|---|---|
| Zepto | `zepto.ads` · `sp.campaign_performance`, `sb.campaign_performance` (+ `sd.campaign_performance` once verified) | SP category, page and product match it within ±₹3 on the same dates ([10](10-mapping-zepto.md) §4) |
| Blinkit | `blinkit.brandcentral` · `mtd_search_report` · Keyword Targeting, Category Targeting, Listing Spotlight, Product Recommendation | Σ daily spend = `MTD Claimables.served_budget_consumed` within ₹1 for 95% of campaigns; Product Booster runs higher and is flagged, not held ([11](11-mapping-blinkit.md)) |
| Instamart | `instamart.brandportal` · `auto_date` | summary, city, product, placement and granular agree exactly |
| FK Minutes | `fkminutes.ads` · `daily` | fsn and placement agree exactly |
| Flipkart marketplace | `daily` (no portal yet, P1; same site as `fkminutes.ads` with scope "Flipkart") | fsn, placement and order lines agree exactly |
| BigBasket | `performance_summary` + awareness `creative_performance` (+ `auction_booking` for awareness revenue and orders only ⚠) | performance reports agree to the paisa ([15](15-mapping-bigbasket.md) §4) |

## 2. Some breakdowns are partial by design

| Report | Share of headline spend | Reason |
|---|---|---|
| Zepto SP keyword | **53–83%**, varies by month and brand | auto and category campaigns have no keywords |
| Zepto SB category / product | 71% | banner traffic has no product |
| Zepto SP city | **−0.2% to −5.2%** short of campaign, drifting with the month | some traffic has no city |
| Instamart granular | **100%** in every complete pull | the "37%" seen earlier was a truncated download (23 k rows instead of 107 k for the same dates). Granular = `auto_date` is now a **hard** check, and that check is what catches truncation |
| Instamart search query | 98% | |
| FK Minutes keyword / search term | **40–83% / 78–86%**, depending on the account | top and bottom of search only |
| Flipkart keyword / search term | 41% / 63% (one account) | same reason |
| BigBasket keyword / search query | 47% / 80% | |

**Rules:**
- A drill-down from a total into a partial breakdown always shows the covered share ("keywords explain 61% of this spend") plus an "other / not broken down" remainder. The pieces never quietly add up to less than the whole.
- Relations live in `wh.reconciliation_rules`, keyed by **portal × report × ad_product**, because Zepto SP and SB invert. Each rule is one of two kinds:
  - **must equal** (within a tolerance in ₹): a miss holds the load ([21](21-validation-and-originals.md) §3);
  - **coverage**: the share is recorded and shown, never held. The ranges above are too wide for a fixed tolerance.

## 3. Day vs range rows, and what is pulled

Several reports hold one total for the whole requested range: every Zepto Ads report, plus Instamart summary, city, product and placement, FK fsn, placement, keyword and search term, and the BigBasket campaign and search-query reports.

**Rules:**
- Facts carry `grain = day | range` plus `period_start` and `period_end`. Where the date of a row comes from is the date rule in [03-dimensions.md](03-dimensions.md).
- **Trend charts use day rows only.** A range row is never spread across its days (that would invent data). Range rows answer only questions for exactly their period, or longer periods built from non-overlapping ranges.
- **Overlapping ranges are never summed.** For a requested period, the planner picks either day rows or a set of range rows that tiles the period exactly. Anything else is reported in `coverage.missing`.

**What a Zepto pull costs (measured 2026-10-02 on `run_tasks`).** One report-day takes **22–45 s** (median ~30 s; an empty card waits out the 15 s no-data window). A daily pull of all 18 Zepto Ads reports (3 ad products × 6) took **10.9–12.1 min per brand** in three runs. So pulling every Zepto report one day at a time is affordable as a daily habit. At 30 brands that is about 6 h of browser time a day, or about 3 h across the 2 slots.

**Backfills must be chunked.** A 30-day split-by-day pull of all 18 reports is ~540 tasks ≈ 4.5 h, beyond the 2 h run cap (`workers/tasks.py:39`). A long backfill is therefore split into runs that each fit the cap, about one week of days per run.

What is pulled is an **admin setting per report**, `ingest.report_policies` (feed on/off, cadence, split by day, restatement window). It is shown on the "Warehouse feeds" screen with its cost in minutes per brand per day ([22](22-access-and-dashboards.md) §7). An admin can switch any report off or move it to weekly. Defaults:

| Reports | Default | Cost per brand |
|---|---|---|
| Zepto, **all 18 Ads reports** (`{sp,sb,sd}.{campaign,category,city,keyword,page,product}_performance`) | daily, split by day | ~11–12 min/day for all 18 (~30 s per report) |
| Zepto, all 18 Ads reports, **reconciliation** | one range pull per calendar week (cut at month ends), checked against that week's day files ([21](21-validation-and-originals.md), range tiling) | ~9 min/week |
| Blinkit `mtd_search_report` | daily MTD, plus a **month-close pull** of the previous month on the 1st–3rd, which captures the final restated values. Whether the portal honours a past-month end is unconfirmed; it needs a supervised probe first ([11](11-mapping-blinkit.md) §1) | one report/day |
| Instamart `auto_date`, FK Minutes `daily` | daily, over the restatement window (Instamart 5 days; FK Minutes 14 ⚠), so restatements are recaptured | one report/day |
| Instamart and FK breakdowns | weekly, as week tiles | one report per week each |

**Week tiles** are an option for any report, and the default only for the Instamart and FK breakdowns. They are calendar weeks cut at month ends: a week that spans two months is pulled as two ranges. Tiles never overlap, so any week and any calendar month is an exact union of tiles. Week start is ❓Q15.

Batching several Zepto reports in one request is feasible only the way the legacy engine did it: one ad type × one date × six **different** report types per batch (`legacy/zepto/report_engine.py` `request_reports`, `collect_batch`). It is an optimisation for later, not a need.

## 4. Declared grain and duplicate rows

A row-level natural key does not exist in the data:
- Blinkit Keyword and Category Targeting carry **one row per bid level** per day.
- Instamart `auto_search_query` needs KEYWORD and PRODUCT_NAME as well as the search query.
- Instamart `auto_granular` has **no** key at all: 269 byte-identical rows carry 8.8% of its spend, and they are real spend.

**Rules:**
1. Each mapping version **declares the grain** of its report: the list of dimension targets that make a row (for example date, campaign, ad group, keyword).
2. Rows that share the grain inside one load are **summed** for every additive metric. A duplicate is not an error. `reported.*` values are kept only where every summed row agrees.
3. A report with no usable grain (Instamart granular) keeps every source row, keyed by its row number.
4. Each fact row carries a `row_key`: the grain values for an aggregated report, the source row number for granular. `row_key` is unique within a load.

## 5. Slice versioning and restatements (PRD FR-28a, B3)

A **slice** is (brand_id, portal_key, report_key, sheet, period_start, period_end):
- a day-grain file has one slice per date present in it;
- a range file has one slice for its whole period.

`ingest.slices` holds one row per slice key, with `current_load_id`, `content_hash`, `first_observed_at`, `last_observed_at` and `restated_count`. The content hash is taken over the slice's canonical rows, sorted by `row_key`.

**Facts are written when the load is mapped, and become current when it publishes.** At map time the parser writes each new or changed slice's facts to `wh.fact_ad`, carrying the load's `load_id` and `slice_id`. A slice whose hash equals its current version writes no facts. A fact is **current** only while its slice's `current_load_id` equals its `load_id` and its `superseded_at` is NULL. The facts of a load that is not yet published, or is quarantined, are therefore never current, and a quarantined load's facts may be purged. Publishing never rebuilds rows from `stage.parsed_rows`, whose 90-day retention must not be load-bearing.

**When a load publishes, for each of its slices** (each slice row locked with `FOR UPDATE`, and the comparison made against the current version at that moment, so two loads of the same slice publish one after the other; a load's facts never depend on another load, so nothing is re-mapped):
1. **Same hash** as the current version → only `last_observed_at` moves. No facts were written for it. This is what bounds Blinkit: a daily MTD pull re-sends every earlier day of the month, about 15 times on average.
2. **Different hash** → in one transaction: set `superseded_at` on the current facts of that slice, point `current_load_id` at the new load, and write `wh.restatements` (old and new load, per-key metric deltas).
3. **A new slice** → point `current_load_id` at the load.

**And always:**
- A fact's values are never updated. The only change ever made to a fact row is setting `superseded_at`, and superseded facts are kept.
- The winner is the newest `report_files.extracted_at`, never the largest number. A rebuild under a new mapping loads the current file again, so it qualifies; its row in `wh.restatements` has cause `remap`, not `platform`.
- A load whose file is older than the one behind the current version leaves the slice as it is (outcome `stale`); any facts it wrote for that slice never become current.
- A slice missing from a newer file keeps its current version. It is never deleted (Instamart reports in one pull can lag by a day).
- A **quarantined load supersedes nothing**, so a truncated download can never replace good data.
- A file whose sha256 equals that of a file already published for the same brand, portal, report and period is not loaded at all (`skipped_duplicate`).

**Measured restatements (2026-10-02):**
- **Blinkit** changes only its trailing ~3 days, by up to ₹24.70. In two pairs of pulls, 141 of 1,754 and 109 of 2,004 campaign-days differed, all of them in the last 3 days. The earlier "15 of 38 matched, ±₹2.30" compared two different exports, not two pulls of the same one.
- **Instamart** restates too: the trailing ~3 days, by up to ₹90.
- **FK Minutes** never changed spend, but attributed revenue (direct + indirect) kept growing: +13% to +17% for a month re-pulled a few days later, and 24 Aug grew +19.5% between the day being 7 and 11 days old ([13](13-mapping-fk-minutes.md)). ⚠ Proposed: a 14-day window for `fkminutes.ads` until ❓Q14 is answered.
- **Zepto** is not yet measured (❓Q14). ⚠ Default 5 days until two pulls of the same days are compared.

**Rules:**
- The restatement window is set **per portal**, on its reports in `ingest.report_policies.restatement_window_days`: Blinkit 5 days, Instamart 5, FK Minutes 14 ⚠, Zepto 5 ⚠ (unmeasured). It is not T-15 everywhere. Stage A's "Refresh last 15 days" preset (FR-28a) still works; it simply re-observes more slices.
- Days inside the window are drawn as **provisional** (icon + word).
- `wh.restatements` lists every slice whose numbers changed, with the old value, the new value and both source files, so a client question like "why did last Tuesday change?" can be answered with evidence.

## 6. Things that look additive but are not

| Value | Why it can't be summed |
|---|---|
| Reach, unique clicks, unique users | the same person is counted on several days |
| Ranks and positions | they are orders, not amounts |
| Percentages without their numerator | there is nothing to add up |
| Budgets and bids | settings, not consumption |

These are `reported.*` and are shown at their own grain only. See [02-metric-dictionary.md](02-metric-dictionary.md) §4.
