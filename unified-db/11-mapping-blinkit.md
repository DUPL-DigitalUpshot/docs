# 11 · Blinkit Ads — column mapping

Portal `blinkit.brandcentral` · report key `mtd_search_report` (the warehouse source, **fed since 2026-10-15**) · `dashboard_export` (in the catalogue, not fed; §1)
Evidence: `docs/research/blinkit-ads-schema.md` (verified, 2 exports) + `samples/blinkit/` + the stored originals in the UniQCAI storage volume + digitalUpshot `blinkit/reports/`. Re-checked 2026-10-02 on 5 MTD files (Aug and Sep).
**Re-checked 2026-10-14:**
- **Scope:** 15 workbooks (7 MTD, 8 dashboard; 1 Jul → 13 Oct 2026) from two advertisers. They are the 5 stored originals plus the 10 legacy downloads, including a run on the updated `legacy/blinkit/report_engine.py`.
- **Method:** the ingest code ran **in memory** over every MTD workbook (no database writes).
- **Write-up:** [docs/research/blinkit-ads-unified-format.md](../research/blinkit-ads-unified-format.md).
- **Headers:** no column changed between August and October.
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
| Missing sheets | a sheet with no rows is **left out** of the workbook (no Category Targeting in October; no PRODUCT_RECOMMENDATION in a short export). A missing sheet is not a download fault ✅ |
| Refresh | Blinkit refreshes its data **once a day, in the morning IST** ✅. Pulls taken hours apart within one refresh are identical |
| Advertiser | the MTD filename prefix is the advertiser ID (`85_…`, `14946_…`); UniQCAI stores the file without it. Inside the file only `Manufacturer` names the advertiser ✅ |

**The dashboard export.**
- **What it is:** the self-serve download `Report_<from>_to_<to>.xlsx`, sheets PRODUCT_LISTING, BANNER_LISTING and PRODUCT_RECOMMENDATION. It has been in the UniQCAI catalogue since 2026-10-14 (email delivery), with `feed_warehouse = false`. PRD FR-20 lists it.
- **Same data as the MTD report** ✅. KT+CT = PRODUCT_LISTING, LS = BANNER_LISTING, PR = PRODUCT_RECOMMENDATION, identical per key at the same refresh. It must **never feed alongside** the MTD report.
- **What it lacks:** `Manufacturer` (so no brand check, and a wrong-account export can't be detected; CLAUDE.md rule 9), budget, the on-hold time and Subcampaign ID.
- **Duplicate rows:** an export spanning two months repeats the 1st of the month as **exact duplicate rows**.
- **Per-day pulls work** ✅ (2026-10-15: 44 single-day exports, 1 Sep – 14 Oct). A range with start = end returns exactly that day and partitions the data with no gaps against every earlier pull. Category targeting sits **inside PRODUCT_LISTING** (Targeting Type `Category`, Match Type `NA`), so `ad_product` should come from Targeting Type, not the sheet name.
- **Not loadable as is:** the `Date` column is `DD-MM-YYYY`, which the mapping `date` transform rejects on every sheet, and Match Type `NA` stops the category days. With both fixed in memory, its canonical rows equal the MTD report's on every settled key (1,227 of 1,227).
- **Proposed grains:** PRODUCT_LISTING and BANNER_LISTING (date, campaign, targeting value); PRODUCT_RECOMMENDATION (date, campaign, targeting type). Summed.
- **No mapping yet.** ❓Q19 which export is authoritative; the working answer is the MTD report, which needs none of these fixes. Evidence: [blinkit-ads-unified-format.md](../research/blinkit-ads-unified-format.md) §6.

## 2. Sheets and grain (MTD search report)

| Sheet | Source rows | Declared grain (fact key) | Breakdown | Clicks? |
|---|---|---|---|---|
| MTD Claimables | one per campaign, month-to-date | Campaign ID (control sheet) | — | no |
| Keyword Targeting | **one per bid level per day** ✅ | day × Campaign ID × Keyword | `keyword` | **no** |
| Category Targeting | one per bid level per day ✅ | day × Campaign ID × Category Name | `category` | **no** |
| Listing Spotlight | one per day × campaign × keyword ✅ | day × Campaign ID × Keyword | `keyword` | Unique Clicks only |
| Product Recommendation | one per day × campaign × subcampaign ✅ | day × Campaign ID × Subcampaign ID | `campaign`, sub-campaign as the **ad group** (§3) | **no** |

**Duplicate rows are summed, not quarantined.** Keyword Targeting repeats the day × campaign × keyword key when a keyword ran at more than one bid: 78 of 5,158, 78 of 6,128, 17 of 2,750, 187 of 5,931 and 217 of 6,948 rows in the five files. The repeated rows differ in `CPM` (the bid) and in their metrics, so they are separate slices of delivery. Category Targeting does the same (3 of 45 rows in Sep). The parser **sums** them to the declared grain; `Match Type` is not needed in the key. Bid-level detail stays in `stage.parsed_rows`. The 2026-10-14 dry run summed 65–145 keys per Keyword Targeting file, 1 Aug → 13 Oct ✅.

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
| Total Budget / total_budget | `reported.budget_total` | reported | campaign setting: the **daily** budget on the daily sheets; on MTD Claimables the sum of daily budgets over active days (92%) | ✅ |
| Most Viewed Position | `reported.most_viewed_position` | reported | rank | ✅ |
| Claimables | `ext.claimables` | ext | MTD sheet only. **= min(served_budget_consumed, Total Budget) on 693/693 rows** ✅ → the budget-capped billable amount | ✅ formula · billing meaning ❓Q6 |
| served_budget_consumed | `ext.served_budget` | ext | MTD sheet only; the control total for §4. Counts spend since the campaign's **last budget reset**, not always the 1st: every mismatch checked equals the spend up to a reset date | ✅ |

### Dimensions

| Source column | Target | Status |
|---|---|---|
| date_ist / Date | `date` (two formats) | ✅ |
| Manufacturer | brand check — Blinkit works at **manufacturer** level, not brand | ⚠ needs `wh.brand_aliases` when one manufacturer has several brands ❓Q21. Today both Blinkit connections have an empty `portal_brand_selector`, so every file fails with `no_expected_brand`; with the selector set to the Manufacturer string the check passes (both advertisers, in memory) |
| Campaign ID, Campaign Name, Campaign Type | `dim_campaign` | ✅ |
| Subcampaign ID | **proposed:** `ad_group_id` → `wh.dim_ad_group.platform_id` (part of the fact key through the declared grain) | ⚠ the shipped YAML targets `subcampaign_id`, which has no home in `ingest/canonical.py` (`_HOMES`): `map_table` stops the sheet in all 7 MTD files. Changing the target to `ad_group_id` loads every row (tested in memory); YAML only |
| Asset | **proposed:** `ad_group_name` (placement: Cart, Similar, Next Product, Repeat Order…) | ⚠ same as above (target `asset` has no home) |
| Title | ignored | always `#-NA` in every file ✅ |
| Keyword / Targeting Value, Match Type, Targeting Type | `breakdown_key`, `match_type` | ✅ Match Type is EXACT in every MTD file; the dashboard export also has `SMART` (July) and `NA` (category rows), which `normalise_match_type` rejects today (§5) |
| Category Name | `breakdown_key` (category) | ✅ |
| Pacing Type | `dim_campaign.pacing` | ✅ |
| latest on hold timestamp | `reported.on_hold_at` | ✅ coerce |

## 4. Headline source and reconciliation (verified 2026-10-02, re-checked 2026-10-14)

Headline = **sum of the four daily targeting sheets**, each its own `ad_product`. In `wh.headline_sources` this is four (portal, report, sheet) rows. **Not seeded yet:** `wh.headline_sources`, `wh.reconciliation_rules` (all 88 rules are Zepto's) and `wh.metric_availability` have no Blinkit rows; they are seeded with phase 3.

**`ad_product` values.** The daily sheets give the sheet name (`Keyword Targeting`, `Category Targeting`, `Listing Spotlight`, `Product Recommendation`). MTD Claimables gives Blinkit's Campaign Type (`Product Booster`, `Listing Spotlight`, `Recommendation Ads`). `wh.dim_ad_product` is empty. **Proposed** house groups (❓Q10):

| Raw value | House group |
|---|---|
| Keyword Targeting, Category Targeting, Product Booster | Search / Product listing |
| Listing Spotlight | Banner / Display |
| Product Recommendation, Recommendation Ads | Recommendation |

With these rows the control can be compared per ad type.

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
- **Re-check 2026-10-14** (7 MTD files, 1 Aug → 13 Oct, both advertisers):
  - With all four daily sheets, 95–100% of campaigns agree within ₹1. Without Product Recommendation, which can't load today (§3), it is only 83–98%, so **that mapping fix comes before this rule is seeded**.
  - The remaining 0–8 misses per file are Product Booster or Listing Spotlight campaigns, explained by the budget reset (§3, `served_budget_consumed`).
  - **Proposed:** extend the flag-not-hold exemption to Listing Spotlight.

**Restatement ✅.** Blinkit changes recent days after the fact. Measured on 2026-10-02 (**spend only**), only the trailing ~3 days changed:

| Pulls compared | Campaign-days differing | Where | Max | Total |
|---|---|---|---|---|
| 19-Aug vs 23-Aug | 141 / 1,754 | only 17–19 Aug | ₹24.60 | ₹508 |
| 22-Sep vs 25-Sep | 109 / 2,004 | only 20–22 Sep | ₹24.70 | ₹415 |

**Re-check 2026-10-14, all metrics.** Delivery (impressions, spend, reach) changes for 2 days, once 3. **Outcomes (sales, ATC, units, new users) change for up to 7 days**, once 8 by +1 unit; nothing changed after that.

**Confirmed 2026-10-15 on settled data.** The 44 per-day pulls of 15 Oct were compared with five earlier pulls (MTD 09-22, 09-25, 10-12; dashboard 10-01..12 and 09-29..10-13):
- Delivery changed only 0–2 days back.
- Outcomes changed 0–7 days back, on 304–385 campaign-days per pull.
- **None changed 8 or more days back**, across about 3,000 older campaign-days.
- Spend totals moved about 0.01%; sales grew 0.9–2.4%.
- **Measured on:** the stored 10-12 pull vs the legacy 10-13 pull, legacy 08-19 vs 08-23, and the dashboard pairs.
- **Changes:** mostly increases. 3–10% are decreases, and one key moved by up to ₹4,426.

The earlier "15 of 38 matched, ±₹2.30" compared two **different exports** (MTD vs dashboard) and is withdrawn. A changed day supersedes its slice and is written to `wh.restatements`.

The restatement window for `blinkit.brandcentral` is **5 days** in `ingest.report_policies` (see [04-grain-and-double-counting.md](04-grain-and-double-counting.md)). That covers delivery but **not outcomes**. The measured minimum is 8 days. **Proposed: 10 days** (owner decision, ❓Q14).

**Pull policy:** daily MTD, plus the month-close pull of the previous month on the 1st–3rd, which captures the final restated values of the month's last days. The month-close pull depends on the supervised probe and the max(`date_ist`) guard in §1.

## 5. Quirks

1. Two names for one concept: `date_ist`/`Date`, `Total Budget`/`total_budget`, `New Users`/`New Users Acquired`, `CTR %`/`CTR`.
2. Product Recommendation has different columns in the two exports (`Subcampaign ID`, `Asset`, `Title` vs `Targeting Type`). The mapping key is therefore portal × report × **sheet**.
3. Blinkit CTR and our CTR are different metrics. In cross-platform views Blinkit's CTR, CPC and conversion rate show as "not available".
4. Bid-level duplicate rows (§2) are normal; summing them is part of the mapping, not an error.
5. Listing Spotlight folds low-volume keywords into a keyword named `Others`. BANNER_LISTING names them, and their totals reconcile.
6. Match Type `SMART` and `NA` (dashboard export, July/August) are not in `normalise_match_type` (EXACT, PHRASE, BROAD, AUTO), so either one on a mapped sheet would stop the load. Add them before mapping the dashboard export.
7. Money floats carry noise (e.g. 1292.2279999999997). `wh.fact_ad.spend` is `numeric(14,2)`: round on load.
8. Identical rows inside an export are **real**: Blinkit can split one bid level into two identical halves. Summed, a single-day pair equals the MTD row (58 impressions, ₹71.80), so they are summed like bid rows. The exception is a dashboard export **spanning two months**, which repeats the 1st of the month as true duplicates. So never request the dashboard export across a month boundary; per day or within one month is safe (§1).

## 6. Open questions

❓Q6 billed spend (evidence above) · ❓Q9 NTB · ❓Q10 ad-type house groups (§4) · Q14 restatement window (decided 2026-10-15: 10 days) · Q19 which export (decided 2026-10-15: MTD) · ❓Q20 whether to show Blinkit's own CTR · ❓Q21 manufacturer → brand.

## 7. Before Blinkit ingest (phase 3) — status 2026-10-15

Found by the 2026-10-14 dry run; details in [blinkit-ads-unified-format.md](../research/blinkit-ads-unified-format.md). Phase 3 was approved for Blinkit Ads on 2026-10-15 (DECISIONS) and built the same day.

| # | Change | Where | Status |
|---|---|---|---|
| 1 | Product Recommendation: `Subcampaign ID` → `ad_group_id`, `Asset` → `ad_group_name`, `Title` ignored | mapping YAML | ✅ v2 active (`make seed-mappings apply=1 activate=1`) |
| 2 | Brand: merge the duplicate Del Monte brand records, then set `portal_brand_selector` to the Manufacturer string | data | ✅ migration 0024; selector `FIELD FRESH FOODS PVT LTD` on connections 6 and 11 |
| 3 | Seed `wh.dim_ad_product` (§4), `wh.headline_sources` (four daily sheets), the Σ daily = served rule and `wh.metric_availability` (no clicks, CTR, CPC or orders) | seeds | ✅ migration 0025, except the Σ daily = served rule: later, and soft (Served Budget restarts with a budget top-up; DECISIONS 2026-10-15) |
| 4 | Restatement window 5 → 10 days | `ingest.report_policies` | ✅ migration 0025 |
| 5 | Accept or map Match Type `SMART` / `NA` | `ingest/canonical.py` | Deferred with item 6: every MTD file has `EXACT`. A future MTD file with `SMART` is held as `parser_error` on the Loads screen, never loaded wrong |
| 6 | Only if the dashboard export is ever fed: a `DD-MM-YYYY` date transform, `ad_product` from Targeting Type, no month-spanning requests, and a decision on its missing brand check | `ingest/mapping.py`, mapping YAML, catalogue | Not fed (DECISIONS 2026-10-15) |

**First load (2026-10-15).** 11 MTD files of Delmonte (brand 5): 1–22 Sep, 1–25 Sep and 1–12 Oct, with their repeat downloads.
- **Checks:** all 11 loads validated, with every hard and soft check passed; all were published.
- **Restatement:** the 25 Sep pull restated 20 day-slices of the 22 Sep pull (cause `platform`; late ATC, revenue and small spend corrections). This is the phase-3 exit check.
- **Reconciliation:** Σ daily spend = MTD Served Budget within ₹1 for 254 of 262 campaigns (96.9%). Of the 8 others, 2 are Listing Spotlight rounding of ₹1–2 and 4 are Keyword Targeting budget top-ups; the one-day Overview exports confirm our daily sums to within ₹4.
- **Marts and dashboards:** current facts equal `mart.ad_daily` on every sheet. Analytics lists Blinkit's four ad types; clicks, orders, CTR, CPC, CPO and AOV show as not reported for Blinkit.
- **Known gap:** 26–30 Sep, where no MTD file covers those days; a later Overview backfill fills it.
