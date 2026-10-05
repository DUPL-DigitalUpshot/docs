# 12 · Swiggy Instamart Ads — column mapping

Portal `instamart.brandportal` · report keys `auto_summary`, `auto_date`, `auto_city`, `auto_placement`, `auto_product`, `auto_granular`, `auto_search_query`
Evidence: `docs/research/instamart-ads-schema.md` (verified, 7 CSVs, one brand) + `samples/instamart/` + the stored originals in the UniQCAI storage volume + digitalUpshot `instamart/reports/`. Re-checked 2026-10-02 on every stored original and sample (6 pulls for reconciliation).
Markers: ✅ verified · ⚠ assumed · ❓Qn unknown → unified-db question n in [40-domain-expert-questions.md](40-domain-expert-questions.md) (not the PRD §12 list).

## 1. File format

| Property | Value |
|---|---|
| Format | CSV with a **6-row preamble** (Selected Filters, From Date dd/mm/yyyy, To Date, Ads Type, Campaign Name or ID, blank). Find the header **by content**, never `skiprows=6` ✅ |
| Header detection | `storage.read_header()` already skips the preamble ✅ |
| Percentages | strings such as `"4.93%"` in `TOTAL_CTR`, `A2C_RATE`, `CAMPAIGN_UPTIME_PERCENTAGE` → number ✅ |
| Nulls | the literal `NA` → NULL (never 0) ✅. Seen in `eCPM`, `eCPC`, `BUDGET_EXHAUSTION_TIME`, and 2 `AD_RANK` cells in granular |
| Enum prefixes | `CAMPAIGN_STATUS_`, `BIDDING_STRATEGY_TYPE_`, `KEYWORD_MATCH_TYPE_` → strip ✅. `BUDGET_TYPE` has **no** prefix |
| Date column | `METRICS_DATE` in date, search_query and granular. The other four are **range totals**; their period comes from `report_files` (the preamble From/To is used as a cross-check) |
| Brand | `BRAND_NAME` on every row. It has **one distinct value in every file** ✅. Facts land **only** on `report_files.brand_id`. A `BRAND_NAME` that does not match the connection's brand (through `wh.brand_aliases`) quarantines the load; a file is never split across brands |
| Max range | summary 365 d · date/city/placement/product 92 d · granular/search_query 31 d |

### Freshness and period hazards

- **Reports in one pull can lag by a day.** In one pull `auto_date` and `auto_placement` held data only to 20 Aug, while the other reports held 21 Aug. Cross-report checks therefore compare on the **overlapping actual dates** only, never on the requested period. A slice missing from a newer file keeps its current version.
- **Stage A period bug A3 (fixed in phase 1).** The adapter moves the end date back to yesterday (`rpa/adapters/instamart/ads.py:1107` `clamp_to_complete_days`) but returns a plain path (`:1129`), so the executor files the requested end date (`rpa/executor.py:316–328` `file_period`). Until the fix, `report_files.period_end` can be one day later than the data. **No stored file is affected today** (0 rows). Day-grain reports take their dates from `METRICS_DATE`, so only range reports are exposed.

## 2. Reports and grain

| Report key | Declared grain (fact key) | Breakdown | Day? | Status |
|---|---|---|---|---|
| `auto_summary` | CAMPAIGN_ID | `campaign` | range | ✅ |
| `auto_date` | CAMPAIGN_ID × METRICS_DATE | `campaign` | **day** | ✅ unique |
| `auto_city` | CAMPAIGN_ID × CITY | `city` | range | ✅ |
| `auto_placement` | CAMPAIGN_ID × AD_PROPERTY × KEYWORD | `placement` | range | ✅ unique |
| `auto_product` | CAMPAIGN_ID × PRODUCT_ID | `product` | range | ✅ |
| `auto_search_query` | CAMPAIGN_ID × METRICS_DATE × SEARCH_QUERY × KEYWORD × PRODUCT_NAME | `search_query` | **day** | ✅ — campaign × date × query alone repeats (421 to 7,159 duplicates per file) |
| `auto_granular` | **no natural key** → surrogate `row_key` = source row number | `granular` | **day** | ✅ |

**Granular has no natural key.** Even the full set of dimension columns repeats: 14,471 repeating groups, including 269 byte-identical rows that carry ₹172,570 (8.8% of spend). They are real delivery, not copies: summing every row is what reconciles to `auto_date` (§4). So granular keeps **every row**, keyed by row number, and is always summed.

**Ad product at headline.** `auto_date` has no `AD_PROPERTY` column (only `AD_PROPERTY_COUNT`), so headline facts carry `ad_product = 'all'`. The ad-type split exists only in `auto_placement`, `auto_search_query` and `auto_granular`, and the ad-type filter reports its coverage.

## 3. Column → canonical mapping

### Metrics

| Source column | Target | Kind | Transform | Status |
|---|---|---|---|---|
| TOTAL_IMPRESSIONS | `impressions` | base | int | ✅ |
| TOTAL_CLICKS | `clicks` | base | int | ✅ |
| TOTAL_BUDGET_BURNT | `spend` | base | ₹ | ✅ |
| TOTAL_A2C | `atc` | base | int | ✅ |
| TOTAL_CONVERSIONS | `orders` | base | int | ⚠ orders or units ❓Q8 |
| TOTAL_GMV | `revenue` | base | ₹ | ✅ TOTAL_ROI = TOTAL_GMV / spend (100%); window ❓Q3 |
| TOTAL_DIRECT_GMV_14_DAYS | `revenue_direct` | base | ₹ | ⚠ 14-day chosen pending ❓Q3 |
| TOTAL_DIRECT_GMV_7_DAYS | `ext.revenue_direct_7d` | ext | ₹ | ✅ differs from TOTAL_GMV on 34% of rows |
| BRANDED_SEARCHES_CLICKS | `ext.branded_clicks` | ext | int (absent in search_query) | ❓Q24 meaning |
| TOTAL_CTR | — | validator | = clicks / impressions ×100 | ✅ 100% |
| A2C_RATE | — | validator | = A2C / **impressions** ×100 (not per click) | ✅ |
| TOTAL_ROI, TOTAL_DIRECT_ROI_7/14_DAYS | — | validator | = GMV / spend | ✅ |
| eCPM | — | validator | = spend / impressions — **cost per impression, not per 1000** | ✅ never map to `cpm` |
| eCPC | — | validator | = spend / clicks | ✅ NA on CPM-bid campaigns |
| TOTAL_BUDGET | `reported.budget_total` | reported | campaign setting | ✅ |
| AD_RANK | `reported.ad_rank` | reported | never summed | ✅ |
| CAMPAIGN_UPTIME_PERCENTAGE | `reported.uptime_pct` | reported | auto_date only | ✅ |
| BUDGET_EXHAUSTION_TIME | `reported.budget_exhausted_at` | reported | clock time "10:21" | ✅ |
| AD_PROPERTY_COUNT, CITY_COUNT, KEYWORD_COUNT, PRODUCT_COUNT, L1/L2_CATEGORY_COUNT | — | ignore | counts of setup, not performance | ✅ |

**No "indirect" revenue for Instamart.** TOTAL_GMV's attribution window is unknown (❓Q3), so TOTAL_GMV − TOTAL_DIRECT_GMV_14_DAYS would mix two windows. `revenue_indirect` is therefore marked **not available** for Instamart (see [02](02-metric-dictionary.md) §1 rule 4). The reason is the unknown window, not the arithmetic: direct GMV (7- or 14-day) never exceeds TOTAL_GMV on any row checked (0 exceptions across the stored originals, `samples/instamart/` and the digitalUpshot pulls; at least 850 k rows, re-checked 2026-10-02) ✅.

### Dimensions

| Source column | Target | Status |
|---|---|---|
| METRICS_DATE | `date` | ✅ |
| CAMPAIGN_ID (UUID), CAMPAIGN_NAME | `dim_campaign` | ✅ |
| CAMPAIGN_START_DATE, CAMPAIGN_END_DATE, CAMPAIGN_STATUS, BIDDING_TYPE, BUDGET_TYPE | `dim_campaign.*` (prefixes stripped where present) | ✅ |
| BRAND_NAME | brand check against the connection's brand (§1) | ✅ |
| AD_PROPERTY | `ad_product` (Keyword Based Ads, Search Inline Banner, Re-Order Ads, …) — placement, search_query, granular only | ✅ |
| CITY | `dim_city` | ✅ |
| KEYWORD, MATCH_TYPE | `breakdown_key`, `match_type` | ✅ |
| SEARCH_QUERY | `breakdown_key` (search_query) | ✅ |
| PRODUCT_ID, PRODUCT_NAME | `dim_product`. PRODUCT_ID exists **only in auto_product** ✅; search_query and granular carry the name only | ✅ |
| L1_CATEGORY, L2_CATEGORY | `dim_product.category_l1/l2` | ✅ |
| TARGETING (granular) | `reported.targeting` | ⚠ |

## 4. Headline source and reconciliation (verified 2026-10-02)

Headline = **`auto_date`** (daily). Compared on overlapping actual dates (§1):

| Report | vs `auto_date` spend | Check |
|---|---|---|
| summary, city, product, placement | **exact** in 5 pulls ✅ | hard |
| **granular** | **100%** in 6 pulls ✅ | **hard** |
| search_query | 96.05% to 99.55% ✅ | coverage |

- **Granular is complete.** The earlier "37% coverage" (₹590,147) came from a **truncated download**: 23,083 rows / 7.8 MB, against 107,236 rows / 36.3 MB for the same dates. The old rule "never drill into granular" is withdrawn.
- Because granular = `auto_date` is a hard check, a truncated granular download is quarantined and supersedes nothing.

**Restatement ✅.** Instamart restates the trailing ~3 days: 18 of 69, 28 of 1,523 and 28 of 1,276 overlapping campaign-days differed between pulls, by up to ₹90. The restatement window for `instamart.brandportal` defaults to 5 days, so the daily `auto_date` pull covers the last 5 days.

## 5. Open questions

❓Q3 attribution window · ❓Q8 conversions = orders? · ❓Q14 restatement window (measured ~3 days) · ❓Q23 how deep to drill into granular · ❓Q24 branded searches · ❓Q25 what `AUTO_` means.
