# 10 · Zepto Ads — column mapping

Portal `zepto.ads` (brands.zepto.co.in) · report keys `{sp|sb|sd}.{campaign|category|city|keyword|page|product}_performance`
Evidence: `docs/research/zepto-ads-schema.md` (verified, 12 files, 1,775 rows) + the stored originals in the UniQCAI storage volume (96 xlsx, re-checked 2026-10-02) + digitalUpshot `login-zepto-webapp/reports/`. Some copies in `samples/zepto/` are **stamped** (they carry `Report_Date` columns); those columns are ignored, and the column inventory reads storage originals only.
Markers: ✅ verified on real rows · ⚠ assumed · ❓Qn unknown → unified-db question n in [40-domain-expert-questions.md](40-domain-expert-questions.md) (not the PRD §12 list).

## 1. File format

| Property | Value |
|---|---|
| Format | xlsx, one sheet (`Sheet1`), header row 1, no preamble |
| Numbers | stored as **text in every cell** ✅ (173,651 of 173,651 numeric cells), `Campaign_id` included. Parse every numeric column explicitly; money is whole rupees ✅ |
| Date column | **none** ✅. Period = `report_files.period_start/end`. The `Report_Date` / `Report_Start_Date` columns users see are added only to the download copy (`app/modules/files/stamp.py`) and never exist in the stored bytes |
| Grain | every row is a **total for the requested range** ✅ → daily facts need `supports_split_by_day` pulls (already declared on every Zepto spec) |
| Ad product | from the report key prefix: `sp` / `sb` / `sd` |
| Header detection | `read_header()` skips xlsx today → `header_row` is NULL (Stage A gap, fixed in phase 1; see [01-architecture.md](01-architecture.md)) |

## 2. Reports and grain

Every grain below was checked on the stored originals: **0 duplicate keys**.

| Report key | Grain (verified unique) | Breakdown | Has campaign id? |
|---|---|---|---|
| `*.campaign_performance` | CampaignName (31 files) | `campaign` | **No** — name only ✅ |
| `*.category_performance` | Campaign_id × Category | `category` | Yes |
| `*.city_performance` | CityName (brand-level) | `city` | No campaign |
| `*.keyword_performance` | KeywordName × KeywordMatchType × Campaign_id (all three are needed) | `keyword` | Yes |
| `*.page_performance` | PageName (brand-level) | `placement` | No campaign |
| `*.product_performance` | Campaign_id × ProductID | `product` | Yes |

## 3. Column → canonical mapping

### Metrics (shared block, all six reports)

| Source column | Target | Kind | Transform | Status |
|---|---|---|---|---|
| Impressions | `impressions` | base | text → int | ✅ |
| Clicks | `clicks` | base | text → int | ✅ |
| Spend | `spend` | base | text → int ₹ | ✅ |
| Revenue | `revenue` | base | text → int ₹ | ✅ (attribution scope ❓Q2) |
| Atc | `atc` | base | text → int | ✅ (meaning ❓Q8: Orders > Atc on 18/20 campaigns) |
| Orders | `orders` | base | text → int; = Same_skus + Other_skus ✅ | ✅ (orders or units? ❓Q8) |
| Same_skus | `orders_direct` | base | text → int | ✅ (same-SKU read as "direct", see [02](02-metric-dictionary.md) §1 rule 6) |
| Other_skus | — | derived | = orders − orders_direct | ✅ not stored |
| Roas | — | validator | = round(Revenue/Spend, 2) | ✅ |
| Cpc | — | validator | = round_half_even(Spend/Clicks) | ✅ (absent in SB) |
| Cpm | — | validator | = round_half_even(Spend/Impressions×1000) | ✅ |
| Ctr | — | validator | = round(Clicks/Impressions×100, 2) (keyword, product only) | ✅ |
| Robas | `reported.robas` | reported | float, never derived, never summed | ❓Q7 — not reproducible from any column |

### Campaign-report extras

| Source column | Target | Kind | Status |
|---|---|---|---|
| CampaignType | `dim_campaign.campaign_type` (`AUCTION_UP_SELL` / `AUCTION_CROSS_SELL` / `PCA`) | dimension | ✅ |
| Status | `dim_campaign.status` | dimension | ✅ |
| Daily_budget (SP) | `reported.daily_budget_avg` — an **average**, not the setting | reported | ✅ never summed |
| Daily_budget (SB) | `reported.daily_budget_setting` — the integer setting | reported | ✅ never summed |
| New_to_brand_user_percentage | `reported.ntb_pct` | reported | ✅ all zero in sample ❓Q9 |
| Unique_reach, Unique_considerations | `reported.unique_reach`, `reported.unique_considerations` | reported | ✅ all zero in sample |

### Dimensions

| Source column | Target | Transform | Status |
|---|---|---|---|
| BrandID, BrandName | brand check | must match the connection's brand, else quarantine | ✅ |
| CampaignName / Campaign_name | `dim_campaign.name` | trim | ✅ |
| Campaign_id | `dim_campaign.platform_id` | already text; keep as text | ✅ |
| Category (category report) | `breakdown_key` (category) | as-is | ✅ |
| Category (product report) | `dim_product.category_l1` — a **product attribute**, not a breakdown key | as-is | ✅ (research doc agrees) |
| CityName | `dim_city` | lowercase in source → alias map | ✅ |
| KeywordName, KeywordMatchType | `breakdown_key`, `match_type` | match → exact/phrase/broad | ✅ |
| PageName | `dim_placement` | normalise slugs, strip trailing UUIDs (`browse_category_product-<uuid>`) | ✅ |
| ProductID, ProductName | `dim_product` | UUID | ✅ |

**Campaign id gap:** `campaign_performance` has no id. Resolve `dim_campaign` by (brand, ad_product, name) and attach the id when the same name appears in another report of the same pull. ⚠

## 4. Headline source and reconciliation (verified tolerances)

Headline = **`campaign_performance`**, SP + SB (+ SD once verified).

| Report vs campaign total | SP | SB | Check |
|---|---|---|---|
| category | within ±₹3 | **71.44%** coverage | SP: hard · SB: coverage |
| product | within ±₹3 | **71.44%** coverage | SP: hard · SB: coverage |
| page | within ±₹3 | exact | hard |
| city | **−0.24% to −3.1%** (Jul/Aug) · **−3.4% to −5.2%** (Sep, storage) | exact | SP: coverage · SB: hard |
| keyword | covers **53–64%** (Jul/Aug) · **~83%** (Sep); auto/category campaigns have no keywords | exact | SP: coverage · SB: hard |

- Tolerances are per **ad_product × report**, not per report.
- **Hard** ("must equal") relations hold the load on a miss (see [21-validation-and-originals.md](21-validation-and-originals.md)). The per-day SP check (category / product / page ≈ campaign, ±₹3) still catches data hazard 1 below: category is filed under the right day while campaign is not, so category ≈ campaign fails on every affected day.
- **Coverage** relations are informational only. SP city drifts with the month, so it has no fixed tolerance.

## 5. Data hazards from Stage A (fixed in phase 1, caught by hard checks)

1. **Files filed under the wrong day (split by day).** In run 161 the `campaign`, `city`, `page` and `product` files hold the day of the **previous exporting task** of the same report; `category` and `keyword` are filed correctly. For example, category filed for 17 Sep sums to ₹3,075, the same as campaign filed for 18 Sep, and campaign filed for 24 Sep equals category filed for 22 Sep, because the 23 Sep tasks failed. Range pulls are unaffected. The cause is the report-centre collector (`_collect`, see [01-architecture.md](01-architecture.md) §5 A1), which also raised false `EMPTY_REPORT` in runs 66 and 160.
   - The per-day SP category ≈ campaign check (±₹3) fails on every affected day. In SB, keyword = campaign fails the same way. Page and product shift together with campaign, so their own checks pass; category is the one that catches it.
   - Phase 1 fixes the collector and relabels the stored rows with a guarded data migration (by id, sha256 and old period); the bytes are never touched. The days with no correct file left (campaign, page and product for 23 and 28 Sep; city for 18, 23 and 28 Sep; category and keyword for 23 Sep) and the SP range for 1–21 Sep (run 66) are re-pulled.
2. **Mislabelled file (same bug).** One stored "SB city" file holds SP city data: it has a `Cpc` column (SB has none) and its spend is 96.2% of SP campaign's (run 67). The SB mapping has no `Cpc` row, so the `header` check holds it, and SB city = SB campaign fails too. Phase 1 adds the same guard to the adapter and relabels the row as `sp.city_performance`.

## 6. Quirks the parser must handle

1. SB has **no `Cpc` column**.
2. Column order is **not** stable or sorted: dimension columns come first, but `Campaign_id`, `Campaign_name` and `Category` sort among the metrics (after `Atc`). **Address every column by name, never by position.**
3. 63% of keyword rows are impression-only (0 clicks, 0 spend) — keep them.
4. City list is open-ended (SB had Mumbai, SP did not).
5. **Sponsored Display is not verified.** The adapter rejects an unrecognised header and logs it (`zepto.header_unrecognised`); the mapping for `sd.*` stays `unknown` until one run is read.

## 7. Pull policy

One report-day takes **22–45 s** (median ~30 s; an empty card waits out the 15 s no-data window). A daily pull of all 18 reports measured **10.9–12.1 min per brand** (runs 155, 160, 169). The earlier "14–16 min per report" was the span of one report across the 30 daily tasks of run 161, not the time of one report.

The pull policy is admin-controlled (`ingest.report_policies`, see [04-grain-and-double-counting.md](04-grain-and-double-counting.md) §3). Defaults:

| Reports | Cadence | Cost per brand |
|---|---|---|
| all 18 reports, `{sp,sb,sd}.{campaign,category,city,keyword,page,product}_performance` | daily, split by day | ~11–12 min/day in total |

- An admin can switch any report off, or move it to **weekly tiles**: calendar weeks cut at month ends, so tiles answer both weekly and monthly questions exactly.
- A **backfill** is chunked. A 30-day split-by-day run of all 18 reports is ~540 tasks ≈ 4.5 h, beyond the 2 h run cap, so it is split into runs of about a week each.

## 8. Open questions

❓Q2 revenue scope · ❓Q7 what `Robas` is · ❓Q8 does `Orders` count orders or units (it exceeds Atc) · ❓Q9 NTB · ❓Q14 restatement window (not yet measured; 5 days ⚠).
