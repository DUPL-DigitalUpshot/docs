# 11 · Blinkit Ads — column mapping

Portal `blinkit.brandcentral` · report key `mtd_search_report` (the only active Blinkit Ads spec)
Evidence: `docs/research/blinkit-ads-schema.md` (verified, 2 exports) + `samples/blinkit/` + the stored originals in the UniQCAI storage volume + digitalUpshot `blinkit/reports/`. Re-checked 2026-10-02 on 5 MTD files (Aug and Sep).
Markers: ✅ verified · ⚠ assumed · ❓Qn unknown → unified-db question n in [40-domain-expert-questions.md](40-domain-expert-questions.md) (not the PRD §12 list).

## 1. File format

| Property | Value |
|---|---|
| Format | xlsx workbook, **one sheet per campaign type**; header row 1 ✅ |
| Date column | **yes** ✅ — `date_ist` (ISO) in the MTD report, `Date` (DD-MM-YYYY) in the dashboard export |
| Grain | **daily** ✅ — no split-by-day loop needed |
| Period held | 1st of month → day clicked (`mtd_period`, DECISIONS L282); restated after the fact ✅ |
| Two-month request | a request spanning two months returns **only the latest month** ✅ (the adapter ignores the start, `rpa/adapters/blinkit/ads.py:317`) → the previous month is closed by a separate **month-close pull** on the 1st–3rd |
| Past-month end | whether the portal honours an end date in a **past** month is **unconfirmed**. The adapter picks the day from the calendar under its `%B %Y` header (`ads.py:352–358`). A supervised probe comes before the month-close pull is built, and every month-close file passes a post-download guard: max(`date_ist`) = the requested end, else the file is refused |
| Ad product | **the sheet name** (Keyword Targeting, Category Targeting, Listing Spotlight, Product Recommendation) |
| Money | float rupees; RoAS at full float precision |
| Mixed types | `latest on hold timestamp` holds timestamps and integer `0` → coerce |
| Repeats | storage keeps byte-identical repeats of one file (5 copies seen) → ingest skips a file whose sha256 equals the current slice's (`skipped_duplicate`) |

A second export exists — the self-serve dashboard download `Report_<from>_to_<to>.xlsx` (sheets PRODUCT_LISTING, PRODUCT_RECOMMENDATION, BANNER_LISTING). It is **not in the UniQCAI catalogue**. PRD FR-20 lists it. Its dashboard-only column names (§5 quirks 1–2) were confirmed in the re-check. ❓Q19 which export is authoritative.

## 2. Sheets and grain (MTD search report)

| Sheet | Source rows | Declared grain (fact key) | Breakdown | Clicks? |
|---|---|---|---|---|
| MTD Claimables | one per campaign, month-to-date | Campaign ID (control sheet) | — | no |
| Keyword Targeting | **one per bid level per day** ✅ | day × Campaign ID × Keyword | `keyword` | **no** |
| Category Targeting | one per bid level per day ✅ | day × Campaign ID × Category Name | `category` | **no** |
| Listing Spotlight | one per day × campaign × keyword ✅ | day × Campaign ID × Keyword | `keyword` | Unique Clicks only |
| Product Recommendation | one per day × campaign × subcampaign ✅ | day × Campaign ID × Subcampaign ID | `campaign` (sub-campaign key) | **no** |

**Duplicate rows are summed, not quarantined.** Keyword Targeting repeats the day × campaign × keyword key when a keyword ran at more than one bid: 78 of 5,158, 78 of 6,128, 17 of 2,750, 187 of 5,931 and 217 of 6,948 rows in the five files. The repeated rows differ in `CPM` (the bid) and in their metrics, so they are separate slices of delivery. Category Targeting does the same (3 of 45 rows in Sep). The parser **sums** them to the declared grain; `Match Type` is not needed in the key. Bid-level detail stays in `stage.parsed_rows`.

## 3. Column → canonical mapping

### Metrics

| Source column | Target | Kind | Transform | Status |
|---|---|---|---|---|
| Impressions | `impressions` | base | int | ✅ |
| Estimated Budget Consumed | `spend` | base | float ₹ | ✅ the RoAS denominator; Σ daily = served within ₹1 for ~95% of campaigns (§4); billed spend ❓Q6 |
| Direct ATC + Indirect ATC | `atc` | base | two rows, weight +1 each | ✅ |
| Direct ATC | `atc_direct` | base | | ✅ |
| Direct Sales + Indirect Sales | `revenue` | base | two rows, weight +1 each | ✅ Total RoAS = (D+I)/spend |
| Direct Sales | `revenue_direct` | base | | ✅ (direct read as same-SKU, see [02](02-metric-dictionary.md) §1 rule 6) |
| Direct + Indirect Quantities Sold | `units` | base | two rows, weight +1 each | ✅ |
| Direct Quantities Sold | `units_direct` | base | | ✅ |
| New Users / New Users Acquired | `ntb_users` | base | two names, same field | ⚠ additive across days assumed ❓Q9 |
| — | `clicks` | base | **NULL** — Blinkit reports no total clicks | ✅ capability gap, not missing data |
| Unique Clicks | `reported.unique_clicks` | reported | never summed | ✅ |
| Reach | `reported.reach` | reported | unique users, never summed | ✅ |
| CTR % / CTR | — | validator | = Unique Clicks / **Reach** ×100 (98.9%) — **not** our CTR | ✅ ❓Q20 |
| Direct RoAS, Total RoAS | — | validator | = Direct Sales / spend; (D+I) / spend | ✅ 100% |
| CPM | `reported.bid_cpm` | reported | a **bid**, not a rate; never derive spend from it. It is what separates duplicate rows, so after summing it is kept only when one bid level ran (see [02](02-metric-dictionary.md) §4) | ✅ |
| Total Budget / total_budget | `reported.budget_total` | reported | campaign setting | ✅ |
| Most Viewed Position | `reported.most_viewed_position` | reported | rank | ✅ |
| Claimables | `ext.claimables` | ext | MTD sheet only. **= min(served_budget_consumed, Total Budget) on 693/693 rows** ✅ → the budget-capped billable amount | ✅ formula · billing meaning ❓Q6 |
| served_budget_consumed | `ext.served_budget` | ext | MTD sheet only; the control total for §4 | ✅ |

### Dimensions

| Source column | Target | Status |
|---|---|---|
| date_ist / Date | `date` (two formats) | ✅ |
| Manufacturer | brand check — Blinkit works at **manufacturer** level, not brand | ⚠ needs `wh.brand_aliases` when one manufacturer has several brands ❓Q21 |
| Campaign ID, Campaign Name, Campaign Type | `dim_campaign` | ✅ |
| Subcampaign ID | `breakdown_key` for Product Recommendation (part of the fact key) | ✅ |
| Asset, Title | `dim_campaign` sub-campaign attributes | ✅ |
| Keyword / Targeting Value, Match Type, Targeting Type | `breakdown_key`, `match_type` | ✅ |
| Category Name | `breakdown_key` (category) | ✅ |
| Pacing Type | `dim_campaign.pacing` | ✅ |
| latest on hold timestamp | `reported.on_hold_at` | ✅ coerce |

## 4. Headline source and reconciliation (verified 2026-10-02)

Headline = **sum of the four daily targeting sheets**, each its own `ad_product`. In `wh.headline_sources` this is four (portal, report, sheet) rows.

**Control check ✅.** Σ daily `Estimated Budget Consumed` per campaign equals MTD Claimables `served_budget_consumed` within ₹1 for:

| File | Campaigns within ₹1 |
|---|---|
| 1 | 184 / 189 |
| 2 | 190 / 198 |
| 3 | 44 / 44 |
| 4 | 117 / 122 |
| 5 | 133 / 140 |

- The exceptions are 5–8 campaigns per file, mostly **Product Booster**. There the daily sum is higher than served (1.04× to 45×).
- File totals of the daily sheets run 0–3.3% above served.
- **Rule:** Σ daily = served per campaign is a **hard** check (±₹1). Product Booster campaigns are exempt from the hold and flagged on the load.

**Restatement ✅.** Blinkit changes recent days after the fact, and only the trailing ~3 days:

| Pulls compared | Campaign-days differing | Where | Max | Total |
|---|---|---|---|---|
| 19-Aug vs 23-Aug | 141 / 1,754 | only 17–19 Aug | ₹24.60 | ₹508 |
| 22-Sep vs 25-Sep | 109 / 2,004 | only 20–22 Sep | ₹24.70 | ₹415 |

The earlier "15 of 38 matched, ±₹2.30" compared two **different exports** (MTD vs dashboard) and is withdrawn. The restatement window for `blinkit.brandcentral` defaults to 5 days (see [04-grain-and-double-counting.md](04-grain-and-double-counting.md)). A changed day supersedes its slice and is written to `wh.restatements`.

**Pull policy:** daily MTD, plus the month-close pull of the previous month on the 1st–3rd, which captures the final restated values of the month's last days. The month-close pull depends on the supervised probe and the max(`date_ist`) guard in §1.

## 5. Quirks

1. Two names for one concept: `date_ist`/`Date`, `Total Budget`/`total_budget`, `New Users`/`New Users Acquired`, `CTR %`/`CTR`.
2. Product Recommendation has different columns in the two exports (`Subcampaign ID`, `Asset`, `Title` vs `Targeting Type`). The mapping key is therefore portal × report × **sheet**.
3. Blinkit CTR and our CTR are different metrics. In cross-platform views Blinkit's CTR, CPC and conversion rate show as "not available".
4. Bid-level duplicate rows (§2) are normal; summing them is part of the mapping, not an error.

## 6. Open questions

❓Q6 billed spend (evidence above) · ❓Q9 NTB · ❓Q14 restatement window (measured ~3 days) · ❓Q19 which export · ❓Q20 whether to show Blinkit's own CTR · ❓Q21 manufacturer → brand.
