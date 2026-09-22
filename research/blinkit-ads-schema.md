# Blinkit Ads — report schema (verified)

Source: 2 exports, manufacturer "FIELD FRESH FOODS PVT LTD"
Status: **ground truth** — read directly from the files.
Compare against `zepto-ads-schema.md`. The two platforms are structurally very different.

---

## What arrived

**A. `85_Search_Reports_20260819.xlsx`** — 5 sheets, 2026-08-01 → 2026-08-19 (19 days). Reads like an account-manager / MTD report.

| sheet | rows | cols |
|---|---|---|
| MTD Claimables | 189 | 8 |
| Keyword Targeting | 5,158 | 22 |
| Category Targeting | 4 | 21 |
| Listing Spotlight | 271 | 15 |
| Product Recommendation | 1,014 | 22 |

**B. `Report_20260817_to_20260821.xlsx`** — 2 sheets, self-serve dashboard download, 2026-08-17 → 2026-08-20.

| sheet | rows | cols |
|---|---|---|
| BANNER_LISTING | 66 | 12 |
| PRODUCT_RECOMMENDATION | 192 | 17 |

**38 distinct column names** across both files, versus Zepto's 31.

The accompanying `manifest.json` records `run_at`, `range_spec: "thisweek"`, `date_range`, `campaign_types`, and a per-target status/file map. That manifest pattern is good and should be standardised across all five platforms. One inconsistency: it declares `campaign_types: ["Product Booster"]` while the file it points at contains `BANNER_LISTING` and `PRODUCT_RECOMMENDATION` — the manifest is describing the request, not the response. Record both.

---

## The five differences that break a shared Zepto/Blinkit parser

**1. Blinkit HAS a date column. Zepto does not.**
`date_ist` (ISO `2026-08-04`) in file A, `Date` (`17-08-2026`, DD-MM-YYYY) in file B. Two formats, two names, same concept.

This is the single biggest operational difference in the project: Blinkit gives daily grain in one pull, so no day-by-day extraction loop is needed. Blinkit extraction is therefore *much* cheaper per day of history than Zepto's.

**2. Blinkit's ad-product axis is the SHEET, not a column.**
Zepto ships one file per report type and separates Sponsored Products / Brands / Display by export. Blinkit ships one workbook with campaign types as sheets. `Campaign Type` values seen: `Product Booster`, `Recommendation Ads`, `Listing Spotlight`.

So the parser must derive `ad_product` from the sheet name on Blinkit and from the export batch on Zepto.

**3. There is no `Clicks` column on the sales-oriented sheets.**
Keyword Targeting, Category Targeting and Product Recommendation report **no clicks at all** — they are impression → ATC → sales. Only Listing Spotlight and BANNER_LISTING carry `Unique Clicks`, and it is *unique* clicks, not total.

Consequence: CPC does not exist and cannot be computed for most Blinkit inventory. Any cross-platform "CPC" column will be null for the majority of Blinkit rows. That is a real capability gap, not missing data.

**4. Attribution is Direct / Indirect, not same-SKU / halo.**
`Direct ATC`, `Indirect ATC`, `Direct Sales`, `Indirect Sales`, `Direct Quantities Sold`, `Indirect Quantities Sold`, `Direct RoAS`, `Total RoAS`.

Conceptually close to Zepto's `Same_skus` / `Other_skus`, but not proven equivalent. Map them at L2 with a documented lossy flag — do not silently merge them into one column.

**5. `CTR %` is computed against Reach, not Impressions.**
Verified: `CTR % = Unique Clicks / Reach × 100` matches on 98.9% of rows; against Impressions it matches 46%. Example — 1,035 impressions, 557 reach, 5 unique clicks, CTR 0.9% (5/557), not 0.48% (5/1035).

**Zepto's CTR is clicks/impressions. Blinkit's is unique-clicks/reach.** These are different metrics wearing the same name. Putting them in a shared `ctr` column and charting them side by side would be actively misleading. Either keep them platform-native, or define a house CTR from raw components and label it as yours.

---

## Independent vs derived — Blinkit

**Derived (verified 100% where present)**

```
Direct RoAS  = Direct Sales / Estimated Budget Consumed
Total RoAS   = (Direct Sales + Indirect Sales) / Estimated Budget Consumed
CTR %        = Unique Clicks / Reach * 100
```

Note Blinkit stores RoAS at **full float precision** (84.46153846153847), unlike Zepto's 2-dp rounding. No rounding rule to replicate — a small mercy.

**Independent (must extract)**

```
Impressions
Reach                       unique users — Zepto's Unique_reach was always 0; Blinkit populates it
Unique Clicks               Listing Spotlight / BANNER_LISTING only
Direct ATC, Indirect ATC
Direct Sales, Indirect Sales
Direct Quantities Sold, Indirect Quantities Sold
New Users / New Users Acquired
Estimated Budget Consumed   ← spend
Most Viewed Position        rank metric, no Zepto equivalent
Claimables                  MTD sheet
served_budget_consumed      MTD sheet
```

**`CPM` is a bid, not a computed rate.** `spend = CPM × impressions / 1000` holds exactly for Category Targeting and Product Recommendation (100%) but only 78–84% for Keyword Targeting and Listing Spotlight, where the bid changed within the aggregation window. Treat `CPM` as an independent campaign setting and **never derive spend from it**.

**`Claimables` ≠ `served_budget_consumed`** on 48% of rows despite looking identical in the sample head. Two genuinely different numbers. Get the definition before either is reported.

---

## The finding that matters most for the pipeline

**The two exports disagree on overlapping campaign-days.**

For the three dates present in both files (17–19 Aug), 38 campaign-days can be compared. Only **15 match exactly**. Differences run up to ₹2.30 per campaign-day — for example campaign 469845 on 17 Aug: ₹408.55 in the MTD file, ₹410.85 in the dashboard export.

The MTD file was generated 19 Aug; the dashboard export 21 Aug. So **Blinkit restates figures after the fact** — late attribution, reconciliation, or claw-back. That has three hard consequences:

1. **Yesterday's number is not final.** Any daily figure must be treated as provisional for some settling window. Find out how long it takes to stabilise — pull the same date range on three consecutive days and diff.
2. **Ingestion must be idempotent upserts**, keyed on (platform, campaign_id, date, report_type, targeting_value), with the later extraction overwriting the earlier. Append-only loading will double-count.
3. **Pick one source of truth per metric.** Two exports covering the same campaign-day with different numbers will otherwise produce two different dashboards, and the client will notice.

Worth checking whether Zepto restates too — we cannot tell from a single pull, and it is the same question. Add a `extracted_at` column and keep prior versions during the pilot.

---

## Naming inconsistencies within Blinkit itself

| concept | variants seen |
|---|---|
| date | `date_ist` (ISO), `Date` (DD-MM-YYYY) |
| budget | `Total Budget`, `total_budget` |
| new users | `New Users`, `New Users Acquired` |
| CTR | `CTR %`, `CTR` |
| targeting | `Keyword` + `Match Type` vs `Targeting Type` + `Targeting Value` |

The same campaign type (Product Recommendation) has **different columns in the two exports**: file A adds `Subcampaign ID`, `Asset`, `Title`; file B has `Targeting Type` instead. So even within one platform and one campaign type, the schema depends on which export you pulled — the capability matrix needs an `export_source` axis, not just platform × ad_product × grain.

`latest on hold timestamp` is mixed-type (timestamp strings and integer `0`). Coerce explicitly or it will break typed loading.

---

## Canonical mapping

```
platform            = 'blinkit'
ad_product          ← sheet name / Campaign Type (Product Booster | Recommendation Ads | Listing Spotlight)
export_source       ← which export produced the row (mtd_report | dashboard)
report_date         ← date_ist / Date          ** Blinkit has real daily grain **
extracted_at        ← manifest run_at          ** required: figures get restated **
campaign_id         ← Campaign ID
campaign_name       ← Campaign Name
subcampaign_id      ← Subcampaign ID
advertiser          ← Manufacturer
keyword             ← Keyword / Targeting Value (when Targeting Type = Keyword)
match_type          ← Match Type
targeting_type      ← Targeting Type
category            ← Category Name
creative_asset      ← Asset / Title
pacing_type         ← Pacing Type
bid_cpm             ← CPM                      ** a bid, not a computed rate **
budget_total        ← Total Budget / total_budget
impressions         ← Impressions
reach               ← Reach
unique_clicks       ← Unique Clicks            ** null on most sheets **
atc_direct          ← Direct ATC
atc_indirect        ← Indirect ATC
units_direct        ← Direct Quantities Sold
units_indirect      ← Indirect Quantities Sold
revenue_direct      ← Direct Sales
revenue_indirect    ← Indirect Sales
new_users           ← New Users / New Users Acquired
spend               ← Estimated Budget Consumed
most_viewed_position← Most Viewed Position
claimables          ← Claimables               (MTD only)
served_budget       ← served_budget_consumed   (MTD only)
```

Derive at query time: `roas_direct`, `roas_total`, `ctr_blinkit` (unique clicks / reach).

---

## Questions for the client

1. How long until a Blinkit day's figures stop moving?
2. Which export is authoritative — the MTD file or the dashboard download?
3. What is `Claimables` versus `served_budget_consumed`?
4. Is there a city / dark-store report, and a SKU-level report? Neither appeared here.
5. Is total (non-unique) click data available anywhere, or is unique-clicks-on-reach all Blinkit offers?
