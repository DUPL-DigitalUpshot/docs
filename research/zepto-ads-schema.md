# Zepto Ads — report schema (verified)

Source: 12 exports from Zepto Ads, brand "Dinshaw's", window 2026-07-01 → 2026-08-19
Status: **ground truth** — column names below are read directly from the files, not inferred.
Covers: **Sponsored Products** (sections 1–4) and **Sponsored Brands** (section 5). Sponsored Display still needs the same capture.

---

## The six reports

| Report | Rows | Cols | Grain (verified unique) |
|---|---|---|---|
| `campaign_performance` | 20 | 21 | CampaignName |
| `category_performance` | 49 | 17 | Campaign_id × Category |
| `city_performance` | 6 | 15 | CityName (brand-level, no campaign) |
| `keyword_performance` | 1519 | 19 | KeywordName × KeywordMatchType × Campaign_id |
| `page_performance` | 12 | 15 | PageName (brand-level, no campaign) |
| `product_performance` | 169 | 20 | Campaign_id × ProductID |

Single sheet each (`Sheet1`), header in row 1, no merged cells, no nulls anywhere in the sample.

---

## Column inventory

### Shared metric block — present in all six reports (12 columns)

Column order within each file is: dimensions first, then metrics in **alphabetical order**.

```
Atc            int    add to cart
Clicks         int
Cpc            int    ROUNDED to whole rupees
Cpm            int    ROUNDED to whole rupees
Impressions    int
Orders         int    == Same_skus + Other_skus (verified on all 6 files, every row)
Other_skus     int    halo orders — other SKUs of the brand
Revenue        int    whole rupees
Roas           float  == Revenue / Spend (verified exact, 2 dp)
Robas          float  NOT derivable from any other column — see below
Same_skus      int    orders of the advertised SKU
Spend          int    whole rupees
```

Every report also carries `BrandID` (UUID) and `BrandName`.

### Per-report dimension and extra columns

**campaign_performance** (21 cols)

```
CampaignName                    str    ← no Campaign_id in this report
BrandID, BrandName
CampaignType                    str    AUCTION_UP_SELL | AUCTION_CROSS_SELL
[shared metric block]
Daily_budget                    float  average over active days, not the configured setting
New_to_brand_user_percentage    int    all zero in sample
Status                          str    ACTIVE | PAUSED
Unique_considerations           int    all zero in sample
Unique_reach                    int    all zero in sample
```

**category_performance** (17 cols)

```
BrandID, BrandName
Campaign_id      int
Campaign_name    str
Category         str    e.g. Cones, Kulfi, Tubs, Namkeens, Premium Chocolates
[shared metric block]
```

**city_performance** (15 cols)

```
CityName    str    LOWERCASE — hyderabad, nagpur, guntur, vijayawada, warangal, karimnagar
BrandID, BrandName
[shared metric block]
```

**keyword_performance** (19 cols)

```
KeywordName        str
KeywordMatchType   str    BROAD | PHRASE | EXACT
BrandID, BrandName
Campaign_id        int
Campaign_name      str
[shared metric block]
Ctr                float  == Clicks/Impressions*100, 2 dp
```

**page_performance** (15 cols)

```
PageName    str    see normalization note below
BrandID, BrandName
[shared metric block]
```

**product_performance** (20 cols)

```
ProductID      str    UUID
ProductName    str
BrandID, BrandName
Campaign_id    int
Campaign_name  str
Category       str
[shared metric block]
Ctr            float
```

---

## Findings that affect the parser

**1. There is no date column. Anywhere.**
The reporting period exists only in the filename (`*_20260701_20260819.xlsx`). Every row is a period aggregate, not a daily row. Consequences:

- Your fact table needs `period_start` / `period_end` injected by the extractor, not parsed from the data.
- You cannot build daily trends from these files. To get daily grain, the RPA must loop day-by-day and pull one export per day — which multiplies run time by the number of days and is the single biggest driver of extraction cost on Zepto. Confirm with the client whether the console offers a day-broken-out option before committing to the loop.
- Never rely on the filename alone; capture the date range you requested from the UI as extraction parameters.

**2. Naming is inconsistent between reports — do not write one generic parser.**
Dimension columns are PascalCase (`CampaignName`, `ProductID`, `KeywordMatchType`), metric columns are Capitalized_snake (`Same_skus`, `Daily_budget`). Worse, the campaign report calls it `CampaignName` and has **no campaign ID at all**, while every other report uses `Campaign_id` + `Campaign_name`. Join campaign-level attributes to the other reports on name, or capture the ID separately during extraction.

**3. `Robas` cannot be reconstructed.**
`Roas = Revenue / Spend` holds exactly. `Robas` does not — and it is sometimes *higher* than Roas (Cone/Category Targeting: Roas 2.23, Robas 2.30) and sometimes lower, so it is not a same-SKU subset. It must be extracted, never computed. Get the definition from the client or Zepto before it appears on any dashboard.

**4. `Ctr` exists only in keyword and product reports.** Compute it for the other four rather than leaving nulls.

**5. `Cpc` and `Cpm` are integer-rounded.** For any aggregation, recompute from `Spend`/`Clicks` and `Spend`/`Impressions` — summing rounded CPCs will drift.

**6. Reconciliation tolerances, measured on this sample.**
Campaign totals: Spend 276,922 · Revenue 587,340 · Clicks 16,057 · Impressions 997,916 · Orders 13,048.

- category / page / product reports match campaign totals to within ₹2 (rounding). Enforce a tight check here — a real break means a broken extraction.
- **city_performance is short by ₹651 (0.24%)** — 276,271 vs 276,922, with 47 fewer clicks. Some traffic isn't city-attributed. Set the city tolerance at ~0.5%, not zero.
- **keyword_performance covers only 61% of spend** (168,533) because auto and category-targeting campaigns have no keyword rows — 18 of 20 campaigns appear. This is expected, not a bug. Do not build a reconciliation rule that expects keyword totals to match campaign totals.

**7. 63% of keyword rows are impression-only** — 954 of 1519 rows have zero clicks and zero spend. Keep them (they are the search-term discovery surface) but expect the keyword table to dominate row counts across the whole platform.

**8. `PageName` mixes human labels with raw slugs.**
Clean values: `Search Page`, `Category Page`, `Home Page`, `Cart Page`, `Product Details Page`, `Orders Page`, `Trending Page`, `Categories`, `Deeplink`.
Raw values leaking through: `post_search`, `page_in_page`, `browse_category_product-65ee1b69-4e24-45b9-ac84-aace3c0854d8`.
Build a `page_name_norm` lookup and a catch-all rule that strips trailing UUIDs, or your placement dimension will fragment as Zepto adds surfaces.

**9. Three columns are all-zero in the sample** — `New_to_brand_user_percentage`, `Unique_reach`, `Unique_considerations`. These are almost certainly Sponsored Brands / Sponsored Display metrics that appear in the Sponsored Products schema but stay empty. Keep the columns; don't build features on them until a Sponsored Brands export confirms they populate.

**10. `Daily_budget` is an average, not a config value.** Values like 1547.1764705882354 are `total / 17` artifacts. It is not the campaign's budget setting and should not be shown as one.

**11. Currency is whole rupees**, verified three ways (Cpc × Clicks ≈ Spend; Cpm × Impressions / 1000 ≈ Spend; Revenue / Spend = Roas). No paise, no decimals on money columns.

---

## Independent vs derived columns

Tested across all six files, 1,775 rows. Every derivation below reproduces the source value on **100% of rows**.

**Independent — must be extracted (8 metrics)**

```
Impressions    base count
Clicks         base count
Spend          base currency
Revenue        base currency
Atc            base count
Same_skus      base count — advertised SKU orders
Other_skus     base count — halo orders
Robas          NOT reproducible from anything else; ratio to Roas swings both sides of 1.0
```

Plus, campaign report only: `Daily_budget`, `New_to_brand_user_percentage`, `Unique_reach`, `Unique_considerations`.

**Derived — safe to drop and recompute (5 metrics)**

```
Orders  = Same_skus + Other_skus                    exact, integer
Roas    = round(Revenue / Spend, 2)                 exact
Ctr     = round(Clicks / Impressions * 100, 2)      exact
Cpc     = round(Spend / Clicks, 0)                  HALF-TO-EVEN, not half-up
Cpm     = round(Spend / Impressions * 1000, 0)      HALF-TO-EVEN, not half-up
```

**Rounding rule — this one bites.** Zepto rounds `.5` to the *even* neighbour, not away from zero: 42.5 → 42, but 13.5 → 14. Verified on all 63 exact ties in the sample; every one lands on the even side. That is Python/NumPy's default `round()`, which incidentally suggests their reporting backend is Python.

Consequences: `numpy.round` and Python's `round()` reproduce it for free. Excel/LibreOffice `ROUND()`, SQL Server `ROUND()`, and `decimal.ROUND_HALF_UP` do not — they disagree on 32 of 1,775 rows here. In Excel the working form is:

```
=IF(AND(MOD(v,1)=0.5, MOD(INT(v),2)=0), INT(v), ROUND(v,0))
```

That's 13 metric columns carrying 8 metrics' worth of information — about 38% redundancy.

Two rules that follow:

- **Store the 8, compute the 5 at query time.** The derived columns are only valid at the source grain. The moment you aggregate — roll cities into a national number, roll keywords into a campaign — `Roas`, `Cpc`, `Cpm` and `Ctr` must be recomputed from summed `Spend`/`Revenue`/`Clicks`/`Impressions`. Summing or averaging the stored values is wrong. `Orders` is the exception: it is additive.
- **Use the identities as extraction validators.** Recompute all five on ingest and compare against the source values. A mismatch means a parse error, a column shift, or a schema change — cheap, and it catches problems before they reach a dashboard.

**Odd one worth asking the client about:** `Orders` exceeds `Atc` on 18 of 20 campaigns (e.g. 2,116 orders vs 1,344 add-to-carts). That reads as `Orders` counting units sold while `Atc` counts cart events. Nail the definition down before either metric appears in a funnel visualization, because the funnel will look broken.

---

## Canonical mapping for the unified fact table

```
platform            = 'zepto'
ad_product          = 'sponsored_products'          -- also: sponsored_brands, sponsored_display
report_type         = campaign|category|city|keyword|page|product
period_start        ← injected by extractor
period_end          ← injected by extractor
brand_id            ← BrandID
brand_name          ← BrandName
campaign_id         ← Campaign_id            (NULL in campaign report — resolve by name)
campaign_name       ← CampaignName / Campaign_name
campaign_type_raw   ← CampaignType           (AUCTION_UP_SELL | AUCTION_CROSS_SELL)
status              ← Status
sku_id              ← ProductID
sku_name            ← ProductName
category            ← Category
city                ← CityName               (lowercase; title-case on load)
placement_raw       ← PageName
placement_norm      ← lookup
keyword             ← KeywordName
match_type          ← KeywordMatchType
impressions         ← Impressions
clicks              ← Clicks
ctr                 ← Ctr, else Clicks/Impressions*100
spend               ← Spend
cpc                 ← recompute Spend/Clicks
cpm                 ← recompute Spend/Impressions*1000
add_to_cart         ← Atc
orders_total        ← Orders
orders_same_sku     ← Same_skus
orders_halo         ← Other_skus
revenue             ← Revenue
roas                ← Roas
robas               ← Robas                  (extract only — definition pending)
daily_budget_avg    ← Daily_budget
new_to_brand_pct    ← New_to_brand_user_percentage
unique_reach        ← Unique_reach
unique_considerations ← Unique_considerations
raw_row_json        ← full source row
```

---

## Sponsored Brands — same six reports, different schema

One campaign (`Dinshaws KW targted SB ads`, PAUSED), 27 rows total: campaign 1 · category 4 · city 7 · keyword 5 · page 1 · product 9. Every identity above still holds — `Orders = Same + Other`, `Roas = Revenue/Spend`, `Ctr`, and half-to-even `Cpm` — on all 27 rows.

Six differences that break any "one Zepto parser" assumption:

**1. There is no `Cpc` column.** Sponsored Brands is a CPM buy, so the metric block is 11 columns, not 12. A parser that indexes columns by position, or asserts a fixed column count, breaks here.

**2. `CampaignType` is `PCA`** — a completely different vocabulary from Sponsored Products' `AUCTION_UP_SELL` / `AUCTION_CROSS_SELL`. Don't build an enum from the SP values.

**3. `Daily_budget` is a clean integer** (6100) rather than SP's averaged float. Same column name, different semantics and dtype across ad products.

**4. `PageName` has exactly one value, `Search Page`.** SB serves on search only, against SP's twelve placements.

**5. Reconciliation inverts.** For SP, category/product matched the baseline and city was short. For SB it is the reverse:

| report | SP variance | SB variance |
|---|---|---|
| category | within rounding | **−28.6%** |
| product | within rounding | **−28.6%** |
| city | −0.24% | exact |
| keyword | −61% | exact |
| page | within rounding | exact |

SB banner traffic has no product or category attached, so ~29% of its spend is unattributable at those grains; and because SB is keyword-targeted only, its keyword report is complete where SP's covers 61%. **Tolerances must be defined per `ad_product` × `report_type`, not per report type alone** — one shared rule set will fire false alarms on half these combinations.

**6. `New_to_brand_user_percentage`, `Unique_reach` and `Unique_considerations` are still zero.** My earlier guess that these were Sponsored Brands metrics was wrong. They are zero in both ad products, so either they populate only for Sponsored Display, or they require something not enabled on this account. Worth asking Zepto directly rather than assuming.

Also: SB's city list includes **Mumbai**, which SP's does not. The city dimension is not a fixed set — load it dynamically.

---

## What to capture next

To close out Zepto, pull the same six (or however many exist) for **Sponsored Display** — expect placement and audience dimensions, and check whether it is where `Unique_reach` / `Unique_considerations` finally populate.

Worth asking Zepto directly, since neither export answered them:

- what `Robas` actually measures
- what conditions populate `Unique_reach`, `Unique_considerations`, `New_to_brand_user_percentage`
- whether `Orders` counts units or orders, given it exceeds `Atc`

Then run the identical header-inventory exercise on Blinkit, Instamart, Flipkart Minutes and BigBasket. Zepto's structure — a shared alphabetical metric block plus per-report dimensions, no dates, orders split same/halo — is a reasonable starting hypothesis for Blinkit, but Flipkart's is definitely different (`Views` not Impressions, `ROI` not ROAS, direct/indirect rather than same/other SKU).
