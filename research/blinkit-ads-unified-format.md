# Blinkit Ads in the unified format — re-check after the legacy changes

How every Blinkit Ads sheet lands in the unified store (`wh.fact_ad` and its lookups), what works today, and what has to change before Blinkit ingest (phase 3) starts. Re-checked 2026-10-14 after the changes to `legacy/blinkit/report_engine.py`. The same findings as a page: [blinkit-ads-unified-format.html](blinkit-ads-unified-format.html).

**Method.** The real ingest code (`read_workbook`, `Mapping.from_yaml`, `map_table`, `file_checks`) was run **in memory** over every Blinkit month-to-date workbook we hold: 3 stored by UniQCAI and 4 downloaded by the legacy prototype. That covers 1 Aug → 13 Oct 2026 and two advertisers, FIELD FRESH FOODS PVT LTD and Dinshaw's Dairy Foods. Nothing was written to the database or storage. Design sources: [11-mapping-blinkit.md](../unified-db/11-mapping-blinkit.md), [02](../unified-db/02-metric-dictionary.md), [03](../unified-db/03-dimensions.md), [04](../unified-db/04-grain-and-double-counting.md), [16](../unified-db/16-cross-platform-matrix.md), [20](../unified-db/20-schema.md).

## 1. What the legacy changes mean for the format

**Nothing in the file layout changed.** The changes in `report_engine.py` and `tests/test_ads_report_checks.py` decide which files are *trusted*:

- **Email:** a mail is accepted only when its `Report_<start>_to_<end>.xlsx` range is this request's. A native preset may end one day early.
- **Downloads:** a download is kept only when it is whole: it matches Content-Length and is a real zip, not an error page.
- **MTD response:** the MTD response body is checked the same way, and a non-200 answer tries an earlier day.
- **Campaign types:** a campaign type that can't be selected now stops the run. Before, the run quietly fell back to "all types", which is what happened on 21 Aug.
- **Run folders:** each run gets its own folder, so a same-day manifest is no longer overwritten.

The unified format only needs the files to be what they claim. These changes make that hold for the prototype. The app adapter (`backend/rpa/adapters/blinkit/ads.py`) already checks the range on the dashboard mail and never filters campaign types.

## 2. The unified format, sheet by sheet

These results come from the dry run and are the same in all 7 files.

| Sheet | `ad_product` | `breakdown` / key | Grain (summed) | Base metrics filled | `reported` | `ext` | Checked, not stored |
|---|---|---|---|---|---|---|---|
| Keyword Targeting | `Keyword Targeting` | `keyword` / Keyword | day × campaign × keyword. 65–145 keys per file are summed from 2+ bid rows | impressions, spend, atc, atc_direct, revenue, revenue_direct, units, units_direct, ntb_users (100%) | bid_cpm, budget_total, most_viewed_position, on_hold_at | — | roas, roas_direct |
| Category Targeting | `Category Targeting` | `category` / Category Name | day × campaign × category (0–2 summed) | same 9 | same 4 | — | roas, roas_direct |
| Listing Spotlight | `Listing Spotlight` | `keyword` / Keyword (incl. an `Others` bucket) | day × campaign × keyword (none summed) | impressions, spend | bid_cpm, budget_total, on_hold_at, **reach, unique_clicks** | — | blinkit_ctr |
| Product Recommendation | — | — | **does not load** (§3, G1) | — | — | — | — |
| MTD Claimables (control) | Campaign Type value (`Product Booster`, `Listing Spotlight`, `Recommendation Ads`) | `campaign` | campaign, month to date | impressions | budget_total | claimables, served_budget | — |

**Campaign lookup (`wh.dim_campaign`).** The daily sheets give `platform_id`, `name` and `pacing`. `campaign_type` comes only from MTD Claimables.

**Against the cross-platform model.** Blinkit fills impressions, spend, ATC, revenue, units and new users. `clicks` and `orders` are always empty: Blinkit has no clicks on three of four sheets and reports units, not orders. So in cross-platform views CTR, CPC, conversion rate and cost per order show "not available for Blinkit". ROAS, CPM (realised = spend ÷ impressions × 1000), cost per unit and ATC compare safely. Direct/indirect is stored as `*_direct` with the "direct read as same-SKU" caveat ([02](../unified-db/02-metric-dictionary.md) rule 6).

## 3. Dry run: what works, what doesn't

| File | Data | Keyword file → stored rows | Product Recommendation | Brand check (no rule / with rule) | Σ daily = served within ₹1 (Product Recommendation added back from the raw sheet) |
|---|---|---|---|---|---|
| stored 09-22 | 09-01 → 09-22 | 5,931 → 5,744 | fails | fail / pass | 117/122 |
| stored 09-25 | 09-01 → 09-25 | 6,948 → 6,731 | fails | fail / pass | 133/140 |
| stored 10-12 | 10-01 → 10-12 | 5,091 → 4,966 | fails | fail / pass | 121/122 |
| legacy 85_08-19 | 08-01 → 08-19 | 5,158 → 5,080 | fails | fail / pass | 184/189 |
| legacy 85_08-23 | 08-01 → 08-23 | 6,128 → 6,050 | fails | fail / pass | 190/198 |
| legacy 14946_08-30 (Dinshaw's) | 08-01 → 08-30 | 2,750 → 2,733 | fails | fail / pass | 44/44 |
| legacy 85_10-13 | 10-01 → 10-13 | 5,666 → 5,530 | fails | fail / pass | 123/124 |

"With rule" means the expected brand set to the file's Manufacturer. All other checks pass: header, row count (except the failing sheet), control totals, formula, dates inside the period.

## 4. Gaps between the design and what would run (most serious first)

**G1. Product Recommendation can't be loaded.**
- `Subcampaign ID`, `Asset` and `Title` map to `subcampaign_id`, `asset` and `title`. Those targets have no home in `backend/ingest/canonical.py` (`_HOMES`), so `map_table` stops the sheet in all 7 files.
- **Consequence 1:** the headline loses all recommendation spend (e.g. ₹2.24 lakh in the 09-25 file).
- **Consequence 2:** the planned ±₹1 control would fail for every Recommendation Ads campaign. Without that sheet the control drops to 83–98%; with it, 95–100%.
- **Fix, tested in memory:** map `Subcampaign ID` → `ad_group_id` and `Asset` → `ad_group_name`, and ignore `Title` (always `#-NA`). Every row then maps (6/6, 432/432, 369/369 in the stored files), and only the brand check fails, as expected. This is a YAML-only change; `wh.dim_ad_group` already exists.
- [11](../unified-db/11-mapping-blinkit.md) §3 describes sub-campaign attributes on `dim_campaign`, which the code doesn't support. The ad-group route fits the existing schema.

**G2. The brand check fails on every file.**
- Both Blinkit connections have an empty `portal_brand_selector`, and the file names the advertiser, not the brand (`no_expected_brand`).
- Setting the selector to the Manufacturer string makes it pass on both advertisers.
- One manufacturer can still map to only one brand (❓Q21). "Del Monte" (id 1) and "Delmonte" (id 5) are one client on one login and should be merged first.

**G3. `ad_product` has two vocabularies and no house groups.**
- The daily sheets produce the sheet name. MTD Claimables produces Blinkit's Campaign Type.
- `wh.dim_ad_product` is empty, so no Blinkit value maps to a house group.
- Proposed rows:

  | Raw value | House group |
  |---|---|
  | Keyword Targeting, Category Targeting, Product Booster | Search / Product listing |
  | Listing Spotlight | Banner / Display |
  | Product Recommendation, Recommendation Ads | Recommendation |

- Without them the control can't be compared per ad type, and cross-platform ad-type filters can't group Blinkit.

**G4. Blinkit headline and control are not seeded.**
- `wh.headline_sources` has **no Blinkit rows**; [11](../unified-db/11-mapping-blinkit.md) §4 calls for the four daily sheets.
- `wh.reconciliation_rules` has none either: all 88 rules are Zepto's. The "Σ daily spend = served_budget_consumed ±₹1" hard check is designed but not seeded.
- The remaining misses (0–8 per file) are Product Booster or Listing Spotlight campaigns. `served_budget_consumed` counts from the campaign's **last budget reset**, not always the 1st. So keep the design's "flag, don't hold" rule for those, and widen it to Listing Spotlight.

**G5. `wh.metric_availability` has no Blinkit rows.** So the "not available for Blinkit" coverage for clicks, CTR, CPC, orders and conversion rate isn't stated yet ([20](../unified-db/20-schema.md) expects it).

**G6. The restatement window is too short for outcomes.**
- `ingest.report_policies` has 5 days for both reports. Spend and impressions settle in 2–3 days, but sales, ATC, units and new users change for **7 days** (once 8).
- [04](../unified-db/04-grain-and-double-counting.md) and [11](../unified-db/11-mapping-blinkit.md) §4 still say ~3 days, measured on spend only.
- **Proposed:** 10 days.

**G7. Values the code would reject.**
- Match Type `SMART` and `NA` appear in the July/August dashboard exports. `normalise_match_type` accepts only EXACT, PHRASE, BROAD and AUTO, so either value on a mapped sheet stops the load. Add them, or map them to `''` with a note, before mapping the dashboard export.
- Spend floats carry noise (e.g. 1292.2279999999997). The column is `numeric(14,2)`, so round on load and keep the check tolerance.

**G8. The dashboard export (not fed today, correctly).**
- It is the same data as the MTD report (KT+CT = PRODUCT_LISTING, LS = BANNER_LISTING, PR = PRODUCT_RECOMMENDATION, identical per key at the same refresh). It must never feed alongside it.
- If it ever becomes the source for days the MTD doesn't cover, it needs:
  - exact-duplicate removal (the 1st of the month repeats in two-month exports)
  - `DD-MM-YYYY` dates
  - the Asset → Targeting Type label map, which merges two Repeat Order assets
- It has **no Manufacturer column**, so it gets no brand check. A wrong-account export can't be told apart (CLAUDE.md rule 9).

**G9. [11-mapping-blinkit.md](../unified-db/11-mapping-blinkit.md) is out of date:**
- §1 says the dashboard export is not in the catalogue; it is, with `feed_warehouse=false`.
- §3 sends sub-campaign attributes to `dim_campaign` (G1).
- §4 has the ~3-day restatement window (G6).
- §4 doesn't mention the budget reset behind `served_budget_consumed` (G4).
- §5 is missing the `Others` bucket, the new match types and the duplicated 1st-of-month rows.

## 5. Decisions needed before phase 3

| # | Decision | Recommendation |
|---|---|---|
| 1 | Sub-campaign home (G1) | `ad_group_id` / `ad_group_name` (YAML only) |
| 2 | Manufacturer → brand (G2, Q21) | merge Del Monte 1/5; set the selector to the Manufacturer string |
| 3 | `wh.dim_ad_product` groups (G3, Q10) | the table in G3 |
| 4 | Seed headline sources, the control rule and metric availability (G4, G5) | four daily sheets; ±₹1 hard, Product Booster and Listing Spotlight flagged |
| 5 | Restatement window (G6, Q14) | 10 days (measured minimum 8, §6) |
| 6 | Source of truth (Q19) | MTD report; the dashboard export only for days the MTD can't give |

Related: [blinkit-ads-columns.md](blinkit-ads-columns.md) · [blinkit-ads-storage.html](blinkit-ads-storage.html) · [blinkit-ads-schema.md](blinkit-ads-schema.md).

## 6. Per-day pulls, 1 Sep – 14 Oct 2026 (pulled 2026-10-15)

**What was pulled.** One Overview export (`dashboard_export`) **per day** for Delmonte (brand 5): 44 runs (232–275), all succeeded in about 30 s each, 44 stored single-day files (9–60 KB, 15,688 rows). They ran through the app's own run path (`create_runs` + `enqueue`) with `date_start = date_end`. `feed_warehouse` is false, so nothing was loaded (0 ingest loads). The MTD report can't be pulled per day: it always holds the 1st of the month up to the chosen day.

**Single-day exports are exact.**
- Every file holds only its own day.
- Each sheet has one header layout across all 44 files.
- The probe day (1 Oct) equals the stored 1–12 Oct export key for key (302/302, 16/16, 6/6).
- Against all five earlier pulls (Sept MTD to 22 and 25 Sep, Oct MTD to 12 Oct, the two multi-day dashboard exports) there were **no missing and no extra campaign-days**. Per-day files partition the data exactly.

**What the days hold.**
- PRODUCT_LISTING and BANNER_LISTING are present on all 44 days.
- PRODUCT_RECOMMENDATION is present on 31 days; no recommendation campaign ran after 1 Oct.
- **Category targeting is inside PRODUCT_LISTING** (Targeting Type `Category`, Match Type `NA`), on 1–7 Sep only. That is the same week as the MTD Category Targeting sheet.
- Recommendation targeting types: `Recommendations`, `Similar Products Recommendation`, `Next Product Recommendation`, `Repeat Order Suggestion`, `Retargeting`.

**Restatement, measured on settled data.** All of September is long settled in a file pulled on 15 Oct. Per campaign-day:

| Earlier pull | Campaign-days | Delivery changed (days back) | Outcomes changed (days back) | Changed 8+ days back |
|---|---|---|---|---|
| MTD to 22 Sep (pulled 23 Sep) | 2,004 | 109 (0–2) | 315 (0–7) | 0 |
| MTD to 25 Sep (pulled 26 Sep) | 2,310 | 131 (0–2) | 359 (0–7) | 0 |
| MTD to 12 Oct (pulled 13 Oct) | 1,287 | 84 (0–2) | 385 (0–7) | 0 |
| Dashboard 1–12 Oct (pulled 13 Oct) | 1,287 | 84 (0–2) | 385 (0–7) | 0 |
| Dashboard 29 Sep–13 Oct (pulled 14 Oct) | 1,424 | 54 (0–2) | 304 (0–7) | 0 |

- **Delivery** (impressions, spend, reach, unique clicks) settles after **2 days**. Total spend moved by about 0.01%.
- **Outcomes** (sales, ATC, units, new users) settle after **7 days**. The largest change was ₹9,740 on one campaign-day; totals grew 0.9–2.4%; 3–10% of the changed campaign-days went down.
- **Nothing changed 8 or more days back**, across about 3,000 older campaign-days. The single day-8 case seen earlier, in a Dinshaw's export without an extraction time, did not recur.
- The restatement window needs **≥ 8 days**. The proposed 10 leaves two days' margin; today's 5 days misses outcome changes on days 5–7.

**Identical rows are real.** A single-day file (7 Oct) holds one pair of identical PRODUCT_LISTING rows. Summed, they equal the MTD Keyword Targeting row for that key (58 impressions, ₹71.80). Dropping one would lose 2 impressions and ₹2.60. So identical rows inside an export **are summed**, like bid-level rows. Only the repeated 1st of the month in an export **spanning two months** is a true duplicate. Rule: never request the dashboard export across a month boundary.

**The dashboard export in the unified format** (in-memory dry run with research-draft mappings derived from the MTD ones; nothing in the repo changed):

| Pass | Result |
|---|---|
| As stored | **Every sheet is rejected** (119 of 119): `not a date (expected yyyy-mm-dd)`. The mapping `date` transform reads only ISO; the export writes `DD-MM-YYYY` |
| Dates converted in memory | All sheets map, except PRODUCT_LISTING on 1–7 Sep: `unknown match type 'NA'` (the category rows) |
| Grain | PRODUCT_LISTING (date, campaign, targeting value), 252 keys summed from bid rows. BANNER_LISTING (date, campaign, targeting value), none summed. PRODUCT_RECOMMENDATION (date, campaign, targeting type), 9 summed |
| Brand check | "passes" on all 112 sheets **only because the export has no Manufacturer column**: no protection against a wrong-account file |
| `ad_product` | `PRODUCT_LISTING` / `BANNER_LISTING` / `PRODUCT_RECOMMENDATION`: a third vocabulary. PRODUCT_LISTING also mixes keyword and category targeting, so it should come from Targeting Type (Keyword → Keyword Targeting, Category → Category Targeting) to match the MTD sheets |
| Against the MTD report | The same keyword rows from the two exports are **identical on all 1,227 settled rows** (8+ days old). Every difference is within the 0–7-day restatement window, and neither side has rows the other lacks |

**What this changes.**
1. **The unified format holds for both exports.** Settled, the dashboard export and the MTD report produce the same canonical rows, so either can be the source, but never both together.
2. **Restatement window:** measured, 8 days minimum; 10 recommended (G6).
3. **Before the dashboard export could feed the warehouse:**
   - a `DD-MM-YYYY` date transform (code)
   - Match Type `NA` accepted (code, as G7)
   - `ad_product` from Targeting Type
   - no requests across month boundaries
   - a decision on its missing brand check (CLAUDE.md rule 9)
   
   The MTD report has none of these problems, which supports keeping it as the source (Q19).
4. **Per-day pulls are useful for backfill and audits** (one stored file per day, 30 s each), even though the MTD report is the planned daily source.
