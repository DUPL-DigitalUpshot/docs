# Swiggy Instamart Ads — report schema (verified)

Source: 7 CSV exports, brand "DEL MONTE FOODS PRIVATE LIMITED", 2026-08-01 → 2026-08-22
Status: **ground truth** — read directly from the files.
Companion docs: `zepto-ads-schema.md`, `blinkit-ads-schema.md`

---

## The seven reports

| report | rows | cols | grain |
|---|---|---|---|
| AUTO_SUMMARY | 160 | 28 | campaign |
| AUTO_DATE | 1,523 | 33 | campaign × date |
| AUTO_CITY | 5,400 | 30 | campaign × city |
| AUTO_PRODUCT | 257 | 31 | campaign × product |
| AUTO_PLACEMENT | 486 | 33 | campaign × ad property × keyword |
| AUTO_SEARCH_QUERY | 21,771 | 34 | campaign × date × search query |
| AUTO_GRANULAR | 23,083 | 34 | campaign × date × property × keyword × product × city |

**44 distinct column names** across the seven. Compare: Zepto 31, Blinkit 38.

---

## Before anything else — the files do not parse as CSVs

Every file has a **6-row preamble** before the real header:

```
row 0  Selected Filters
row 1  From Date,01/08/2026
row 2  To Date,22/08/2026
row 3  Ads Type,"Auto Suggest Ads, Brands in Focus, Browse Boost Item Ads, ..."
row 4  Campaign Name or ID,All Campaigns
row 5  (blank)
row 6  ← real header
```

A naive `read_csv` yields `Unnamed: 1…33` and every value typed as string. **Detect the header by content, not offset** — the first column is `CAMPAIGN_ID` on four reports and `METRICS_DATE` on three. Do not hardcode `skiprows=6`; Swiggy can add a filter line and silently shift it.

Keep the preamble. `Ads Type` enumerates Instamart's full ad-format taxonomy (~20 formats: Auto Suggest Ads, Brands in Focus, Browse Boost Item Ads, Collection Ads – Cart/Home Page, Display Ads, Frequently Bought Together, Guaranteed Top Slot, Household Favorites, L2 Banners, Pre Search Page Banner, Re-Order Ads, Search Boost Ads, Search Inline Banner, …). That is Instamart's equivalent of Zepto's SP/SB/SD axis, and it belongs in the capability matrix.

Also needing explicit handling: percentages are strings with `%` (`"4.93%"`), nulls are the literal `NA`, and enum values carry type prefixes — `CAMPAIGN_STATUS_PAUSED`, `BIDDING_STRATEGY_TYPE_CPM`, `KEYWORD_MATCH_TYPE_EXACT`. Strip the prefixes on load.

---

## `eCPM` is not a CPM

Verified on 13,484 rows: **`eCPM = TOTAL_BUDGET_BURNT / TOTAL_IMPRESSIONS`** — cost per *impression*. Matching against `burnt/impressions × 1000` succeeds on **0%** of rows.

Swiggy has mislabelled the column. Anything that maps `eCPM` into a shared `cpm` field alongside Zepto's `Cpm` and Blinkit's `CPM` will be wrong by a factor of 1,000. Store it as `cost_per_impression` and compute a true CPM if one is needed.

Similarly **`A2C_RATE = TOTAL_A2C / TOTAL_IMPRESSIONS`**, not per click (100% vs 5.3%). It is an impression-based rate despite reading like a funnel conversion rate.

Both are the same failure mode as Blinkit's CTR-on-Reach: **a shared column name is not evidence of a shared definition.**

---

## Independent vs derived

**Derived — all verified at 100%**

```
TOTAL_CTR              = TOTAL_CLICKS / TOTAL_IMPRESSIONS * 100
A2C_RATE               = TOTAL_A2C / TOTAL_IMPRESSIONS * 100
TOTAL_ROI              = TOTAL_GMV / TOTAL_BUDGET_BURNT
TOTAL_DIRECT_ROI_7_DAYS  = TOTAL_DIRECT_GMV_7_DAYS / TOTAL_BUDGET_BURNT
TOTAL_DIRECT_ROI_14_DAYS = TOTAL_DIRECT_GMV_14_DAYS / TOTAL_BUDGET_BURNT
eCPM                   = TOTAL_BUDGET_BURNT / TOTAL_IMPRESSIONS
eCPC                   = TOTAL_BUDGET_BURNT / TOTAL_CLICKS
```

Seven derived columns of 44. Instamart is the most redundant of the three platforms so far.

**Independent — must extract**

```
TOTAL_IMPRESSIONS
TOTAL_CLICKS
BRANDED_SEARCHES_CLICKS      no Zepto or Blinkit equivalent
TOTAL_A2C
TOTAL_CONVERSIONS
TOTAL_GMV
TOTAL_DIRECT_GMV_7_DAYS      three revenue windows, genuinely different
TOTAL_DIRECT_GMV_14_DAYS
TOTAL_BUDGET_BURNT           ← spend
TOTAL_BUDGET                 campaign setting
AD_RANK                      auction position, no equivalent elsewhere
CAMPAIGN_UPTIME_PERCENTAGE   AUTO_DATE only
BUDGET_EXHAUSTION_TIME       AUTO_DATE only — clock time, e.g. "10:21"
```

**Three attribution windows, not one.** `TOTAL_GMV` equals the 7-day figure on only 66% of rows; 7-day equals 14-day on 92%. Store all three.

**`BIDDING_TYPE` is per campaign** — `BIDDING_STRATEGY_TYPE_CPM` and `..._CPC` coexist in one account, which is why `eCPM` and `eCPC` are null on complementary subsets. Bidding type is a row-level condition in the capability matrix, not a platform-level one.

`CAMPAIGN_UPTIME_PERCENTAGE` and `BUDGET_EXHAUSTION_TIME` are genuinely useful and unique to Instamart — "this campaign burned its budget by 10:21 and was dark for the rest of the day" is an actionable insight no other platform hands you.

---

## AUTO_GRANULAR — the trap

`AUTO_GRANULAR` looks like the atomic fact table that could generate all six other reports by aggregation. It cannot, and the way it fails is dangerous.

**Where it has data, it is exact.** Aggregating GRANULAR to campaign × city reproduces AUTO_CITY to the paisa on 1,696 of 1,702 shared cells.

**But it silently omits 63% of spend.**

| | spend | impressions | campaigns |
|---|---|---|---|
| SUMMARY / DATE / CITY / PRODUCT / PLACEMENT | ₹1,604,258 | 848,122 | 160 |
| SEARCH_QUERY | ₹1,572,364 | 813,895 | — |
| **GRANULAR** | **₹590,147** | **307,690** | **68** |

The five aggregate reports agree with each other **exactly** — same spend, impressions, clicks, GMV, A2C to the rupee. GRANULAR accounts for 37% of that.

It is a *filter*, not a truncation. Coverage is a steady 33–46% on every one of the 22 days, and it breaks down by ad property:

| AD_PROPERTY | GRANULAR | PLACEMENT | coverage |
|---|---|---|---|
| Keyword Based Ads | ₹585,487 | ₹1,279,510 | 45.8% |
| Re-Order Ads | ₹4,544 | ₹31,878 | 14.3% |
| Browse Boost Item Ads | ₹10 | ₹16 | 62.5% |
| **Search Inline Banner** | **₹106** | **₹292,854** | **0.0%** |

GRANULAR appears to include only rows where every dimension resolves — keyword *and* product *and* city — so banner and display formats, which have no keyword-product pair, drop out almost entirely, taking 92 of 160 campaigns with them.

**Rules that follow:**

1. **Never use GRANULAR as the source of truth for spend or revenue.** Use SUMMARY (or DATE for daily) as the spend baseline and GRANULAR only for the fine-grained slice questions it can answer.
2. **Never blend GRANULAR with the aggregate reports in one visual.** A dashboard drilling from a campaign total into a GRANULAR breakdown will show the pieces summing to a third of the whole.
3. Set the GRANULAR reconciliation tolerance to *coverage %*, not variance — and surface the uncovered share in the UI rather than hiding it.

This is also the strongest evidence yet for the grain-partitioned model: GRANULAR and SUMMARY are different grains with different completeness, and a single mixed-grain table invites exactly the mistake above.

---

## Canonical mapping

```
platform            = 'instamart'
ad_product          ← AD_PROPERTY (Keyword Based Ads | Search Inline Banner | Re-Order Ads | Browse Boost Item Ads | …)
report_type         ← summary | date | city | product | placement | search_query | granular
report_date         ← METRICS_DATE            (DATE, SEARCH_QUERY, GRANULAR only)
period_start/end    ← preamble From/To Date   (the other four reports)
campaign_id         ← CAMPAIGN_ID             UUID
campaign_name       ← CAMPAIGN_NAME
campaign_start/end  ← CAMPAIGN_START_DATE / CAMPAIGN_END_DATE
status              ← CAMPAIGN_STATUS         strip CAMPAIGN_STATUS_ prefix
bidding_type        ← BIDDING_TYPE            strip BIDDING_STRATEGY_TYPE_ prefix
budget_type         ← BUDGET_TYPE
brand_name          ← BRAND_NAME
city                ← CITY
keyword             ← KEYWORD
search_query        ← SEARCH_QUERY            SEARCH_QUERY report only
match_type          ← MATCH_TYPE              strip KEYWORD_MATCH_TYPE_ prefix
category_l1/l2      ← L1_CATEGORY / L2_CATEGORY
sku_id              ← PRODUCT_ID              PRODUCT report only
sku_name            ← PRODUCT_NAME
impressions         ← TOTAL_IMPRESSIONS
clicks              ← TOTAL_CLICKS
branded_clicks      ← BRANDED_SEARCHES_CLICKS
atc                 ← TOTAL_A2C
conversions         ← TOTAL_CONVERSIONS
revenue             ← TOTAL_GMV
revenue_7d          ← TOTAL_DIRECT_GMV_7_DAYS
revenue_14d         ← TOTAL_DIRECT_GMV_14_DAYS
spend               ← TOTAL_BUDGET_BURNT
budget_total        ← TOTAL_BUDGET
ad_rank             ← AD_RANK
uptime_pct          ← CAMPAIGN_UPTIME_PERCENTAGE
budget_exhaustion   ← BUDGET_EXHAUSTION_TIME
cost_per_impression ← eCPM        ** NOT a CPM **
```

Derive at query time: `ctr`, `a2c_rate`, `roi`, `roi_7d`, `roi_14d`, `cpc`.

---

## Questions for the client

1. What exactly does GRANULAR filter on? Confirm the 63% gap is by design, not an export bug.
2. Are `PRODUCT_ID`s available on GRANULAR (it carries `PRODUCT_NAME` only), or must products be joined by name?
3. What is `BRANDED_SEARCHES_CLICKS` measuring?
4. Does Instamart restate figures after the fact, as Blinkit does? Pull the same range on consecutive days and diff.
5. Is `AUTO_` in the filename the campaign type, the export mode, or the download automation? It matters for whether other export families exist.
