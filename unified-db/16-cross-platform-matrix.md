# 16 · Cross-platform matrix — one canonical field, six platforms

The quick-scan view. For the detail behind any cell, see the platform's mapping file (10–15).
✅ verified · ⚠ assumed · ❓Qn unified-db question n in [40](40-domain-expert-questions.md) · **—** the platform does not report it (stored as NULL, shown as "not available").
**Cells describe the headline source** (bottom table). "breakdown only" means the field exists in a breakdown report but not at headline, so a headline tile shows it as not available.

## Base metrics (stored, additive)

| Canonical | Zepto | Blinkit | Instamart | FK Minutes | Flipkart marketplace | BigBasket |
|---|---|---|---|---|---|---|
| `impressions` | Impressions ✅ | Impressions ✅ | TOTAL_IMPRESSIONS ✅ | Views ⚠ | Views ⚠ | Ad Impressions / Impressions ✅ |
| `clicks` | Clicks ✅ | — (unique only) | TOTAL_CLICKS ✅ | Clicks — keyword breakdown only ✅ | Clicks ✅ | Clicks — awareness only; not in summary ⚠ partial |
| `spend` | Spend ✅ | Estimated Budget Consumed ✅ (= served ±₹1) ❓Q6 | TOTAL_BUDGET_BURNT ✅ | Ad Spend ✅ | Ad Spend / SUM(cost) ✅ | Ad Spend / Spend / Cost ✅ |
| `atc` | Atc ✅ ❓Q8 | Direct + Indirect ATC ✅ | TOTAL_A2C ✅ | Actions ⚠ ❓Q5 | — | Add to Cart — products breakdown only ✅ |
| `atc_direct` | — | Direct ATC ✅ | — | — | — | — |
| `revenue` | Revenue ✅ ❓Q2 | Direct + Indirect Sales ✅ | TOTAL_GMV ✅ ❓Q3 | Direct + Indirect Revenue ✅ | Total Revenue (Rs.) ✅ | Ad Revenue ✅ |
| `revenue_direct` | — | Direct Sales ✅ | DIRECT_GMV_14_DAYS ⚠ ❓Q3 | Direct Revenue ✅ | Direct Revenue — breakdown only (not in daily) ✅ | Ad Rev − Other SKU Ad Rev — breakdown only ⚠ |
| `orders` | Orders ✅ ❓Q8 | — | TOTAL_CONVERSIONS ⚠ ❓Q8 | — | — | Orders (SKU) ⚠ ❓Q8 |
| `orders_direct` | Same_skus ✅ | — | — | — | — | Same SKU Orders — breakdown only ✅ |
| `units` | — | Direct + Indirect Qty ✅ | — | Units Sold D+I ✅ | Total converted units ✅ | Purchased Product Units — halo only ✅ |
| `units_direct` | — | Direct Quantities Sold ✅ | — | Units Sold (Direct) ✅ | Direct Units Sold — breakdown only ✅ | — |
| `ntb_users` | — (a % only) | New Users ⚠ ❓Q9 | — | — | — | — |

## What each derived metric can show, per platform (at headline)

A derived metric shows only where every one of its inputs exists.

| Metric | Zepto | Blinkit | Instamart | FK Minutes | Flipkart mkt | BigBasket |
|---|---|---|---|---|---|---|
| ROAS = revenue/spend | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Direct ROAS | — | ✅ | ⚠ | ✅ | **not available** (breakdown only) | **not available** (breakdown only) |
| Revenue (other SKUs) = total − direct | — | ✅ | **not available** (TOTAL_GMV's window is unknown, ❓Q3; [02](02-metric-dictionary.md) §1 rule 4) | ✅ | breakdown only | breakdown only |
| CTR = clicks/impressions | ✅ | **not available** | ✅ | **not available** (keyword only) | ✅ | partial (awareness only) |
| CPC = spend/clicks | ✅ | **not available** | ✅ | **not available** (keyword only) | ✅ | partial (awareness only) |
| CPM = spend/impressions×1000 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| ATC rate = atc/impressions | ✅ | ✅ | ✅ | ⚠ ❓Q5 | — | breakdown only (products) |
| CPO = spend/orders | ✅ | — | ⚠ | — | — | ⚠ |
| Cost per unit = spend/units | — | ✅ | — | ✅ | ✅ | breakdown only (halo) |

**Reading the matrix:** ROAS and CPM work everywhere, so they make safe cross-platform headline KPIs. CTR and CPC are not available at headline for Blinkit and FK Minutes, and only partial for BigBasket. CPO exists on three platforms. A cross-platform tile for these metrics shows "not available for Blinkit, FK Minutes" (and the coverage it does have) instead of a misleading total.

## Same name, different meaning — never chart these together

| Name | Where | Actually means |
|---|---|---|
| CTR | Blinkit | unique clicks ÷ **reach** |
| eCPM | Instamart | spend ÷ impressions (**per impression**, not per 1000) |
| A2C_RATE | Instamart | ATC ÷ **impressions** |
| CVR | FK Minutes | units ÷ actions ×100 (can exceed 100) |
| Average CPB | FK Minutes | **not** spend ÷ actions (definition unknown) |
| CPM | Blinkit | the **bid**, not the realised rate |
| Daily_budget | Zepto SP | an **average**, not the setting (SB: the setting) |
| Conversion Rate | Flipkart mkt | a **fraction** (0.05), not a percentage |

## Headline source per platform

Each row is an explicit set of (portal, report, sheet) in `wh.headline_sources`.

| Platform | Headline source | Grain | `ad_product` at headline |
|---|---|---|---|
| Zepto | `{sp,sb}.campaign_performance` (+ `sd` once verified) | range → split by day | sp / sb / sd ✅ |
| Blinkit | `mtd_search_report`, the **four daily sheets** (verified vs `served_budget_consumed` ✅) | day | the sheet ✅ |
| Instamart | `auto_date` | day | `all` (no AD_PROPERTY) ✅ |
| FK Minutes | `daily` | day | `all` (no placement) ✅ |
| Flipkart marketplace | `daily` (no portal yet, see [14](14-mapping-flipkart-marketplace-ads.md)) | day | `all` ✅ |
| BigBasket | `performance_summary` + awareness `creative_performance` (+ `auction_booking` for awareness revenue ⚠) | day | performance / awareness |
