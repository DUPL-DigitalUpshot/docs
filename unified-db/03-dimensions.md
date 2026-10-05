# 03 · Dimensions — what you can slice and filter by

| Dimension | Source | Normalisation | Notes |
|---|---|---|---|
| **Date** | see the date rule below | IST calendar date | never read from the stamped download copy |
| **Brand** | `report_files.brand_id`, always. A brand column in the file (Instamart `BRAND_NAME`; Blinkit `Manufacturer`; BigBasket `Brand Name`) is a **check**, not a source | raw value → `wh.brand_aliases` → must equal the file's brand | see the brand rule below |
| **Platform** | `report_files.platform_key` | — | zepto, blinkit, instamart, fkminutes, (bigbasket) |
| **Portal** | `report_files.portal_key` | — | shown under "Technical detail" only |
| **Ad type** (`ad_product`) | Zepto key prefix (SP/SB/SD); Blinkit sheet; Instamart `AD_PROPERTY`; FK placement family; BigBasket performance/awareness. **`all`** when the headline report has no ad-type split (Instamart `auto_date`, FK `daily`) | `wh.dim_ad_product` maps each platform's value to a house group: *Search / Product listing*, *Recommendation*, *Banner / Display*, *Brand* | ❓Q10 confirm the groups. Filtering by ad type with such a platform selected reports it in `coverage` (rule 2) |
| **Campaign** | platform campaign id; Zepto `campaign_performance` has a name only | `wh.dim_campaign` (portal, platform_id) with name history | campaign names change, ids don't |
| **Ad group** | ad group id where the report has one; FK search term has `AdGroup Name` and no id | `wh.dim_ad_group` (portal, campaign, platform_id or name) | part of the grain key wherever the report carries it |
| **Keyword**, **match type** | Keyword / KeywordName / attributed_keyword / Targeting Value | match → `exact` / `phrase` / `broad` / `auto` | |
| **Search query** | SEARCH_QUERY / Query / Search Query | lower-case, trimmed | the highest-volume dimension |
| **Product** | ProductID (Zepto UUID), PRODUCT_ID (Instamart), FSN, Product ID (BigBasket), Sku Id (Flipkart seller SKU) | `wh.dim_product` (portal, platform_product_id) + EAN where known | a cross-platform product master is **not in v1** ❓Q11 |
| **Category** | platform's own category text | none in v1 | categories differ per platform |
| **City** | CityName (lowercase), CITY | `wh.dim_city` with an alias map (case, spelling) | Flipkart **zones** are a separate dimension ❓Q12 |
| **Placement / page** | PageName, AD_PROPERTY, placement_type, Placement Type, Page Name | slug clean-up (Zepto `browse_category_product-<uuid>`) | |

## The date rule

The period always comes from `report_files.period_start/end`, the period the file **actually holds** (DECISIONS L282). Inside it:

1. **Day-grain files** (a date column per row: Blinkit daily sheets, Instamart `auto_date` and granular, FK `daily`). The date column defines the **day slice** of each row. Every date must fall inside `report_files.period`; a date outside it quarantines the load.
2. **Range files** (no date column: every Zepto Ads report, Instamart summary, city, product and placement, FK fsn, placement, keyword and search term). The whole file is one range slice, and its period is `report_files.period_start/end`. A Zepto file pulled with split by day is a range file whose period is one day.
3. A date is **never** read from the stamped download copy, and nothing is ever stamped into a stored file. This is how decision D7 in [00-README.md](00-README.md) reads: the period from `report_files`, the day from the file's own date column where it has one.

Bug A3 ([01-architecture.md](01-architecture.md) §5) makes Instamart's recorded period wrong today. It is fixed in phase 1, before Instamart is loaded.

## The brand rule

1. **Facts land only on `report_files.brand_id`.** That is the brand Stage A filed the file under, and the brand whose grants decide who may open it.
2. Where a file carries a brand column, **every** raw value must resolve through `wh.brand_aliases` to that same brand. An unknown value, or one that resolves to another brand, **quarantines** the load. A row is never guessed into a brand.
3. **A file is never split across brands.** Splitting would leave facts whose "Source files" link points at a file the viewer's grants cannot open. Every Instamart file seen so far holds one `BRAND_NAME`, and Stage A files it under one brand, so nothing is lost.
4. Blinkit's `Manufacturer` can name a company that owns several of our brands. Whether such a file should ever feed more than one brand is open (❓Q21). In v1 its facts land on the connection's brand ([20-schema.md](20-schema.md), `wh.brand_aliases`).

## Rules

1. A **dimension value never invents a row.** If Zepto has no city breakdown for a campaign, that campaign does not appear in a city chart. It is never shown as "Unknown city: ₹X" unless the report itself has an unattributed row.
2. **Filters that one platform cannot answer are stated.** Filtering by city with Flipkart Minutes selected shows "Flipkart Minutes has no city breakdown". Filtering by ad type with Instamart selected says its headline has no ad-type split (`ad_product = all`). Neither quietly drops the platform from the total. (This is the same `coverage` mechanism as [22-access-and-dashboards.md](22-access-and-dashboards.md).)
3. **Every alias map is admin data with an audit trail.** These are `wh.brand_aliases`, `wh.dim_city.aliases` and `wh.dim_ad_product`. Changing one creates a mapping version and loads the affected files again.
