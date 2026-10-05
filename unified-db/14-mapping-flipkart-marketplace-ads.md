# 14 · Flipkart marketplace Ads — column mapping (not yet in UniQCAI)

**Status: no UniQCAI portal, and no `platform_key`.** These files come from the digitalUpshot `fk-ecommerce/` pipeline, for a separate business on the same login (sports goods). In UniQCAI, `flipkart.sellerhub` is a **Sales** portal whose report types are declared inactive, so it is not the home for these.

**Where it would land.** The source is **advertising.flipkart.com — the same site as `fkminutes.ads`**. The only difference is the "Select Report For" scope: `Flipkart` instead of `Minutes` (`rpa/adapters/fkminutes/ads.py`, `SCOPE` and `SCOPE_VALUE_RE`, ~L102–108). So open item P1 (see [00-README.md](00-README.md)) is not "there is nowhere to put it". It is a choice between:
- **(a)** a scope on the existing `fkminutes.ads` portal, or
- **(b)** a sibling portal on the same adapter (same login, OTP and health), with its own `platform_key` (Flipkart marketplace, not Minutes).

Either way, the report keys `daily`, `fsn`, `placement`, `keyword` and `search_term` **collide** with `fkminutes.ads`, so they need a scope prefix or a separate portal key. The facts also need a platform of their own, because Minutes and marketplace are different businesses. Whether this belongs in UniQCAI is a product question for the owner.

Evidence: checked on 2026-10-01 against digitalUpshot `fk-ecommerce/reports/2026-08-25_07-19-27/` (18–24 Aug 2026), re-checked 2026-10-02.
Markers: ✅ verified · ⚠ assumed · ❓ unknown.

## 1. File format

Same family as FK Minutes: a 2-row `Start Time` / `End Time` preamble, plus 2 note rows on keyword. Some headers have a **leading space** (` Direct Units Sold`), so trim every header. Spend is called `Ad Spend` in some reports, `SUM(cost)` in others and `Ad Spends` in incentivised.

## 2. Reports and grain

| Report | Declared grain (fact key) | Breakdown | Day? |
|---|---|---|---|
| daily | Campaign ID × Date (no ad group column) ✅ unique | `campaign` | **day** |
| fsn | Campaign ID × AdGroup ID × Sku Id | `product` | range |
| campaign | **order line**: Campaign ID × AdGroup Name × Listing ID × advertised FSN × purchased FSN × order_id × Date | `order` | **day** |
| placement | Campaign ID × AdGroup Name × Placement Type ✅ unique | `placement` | range |
| keyword | Campaign ID × AdGroup ID × keyword × match type (TOS/BOS) | `keyword` | range |
| search_term | Campaign ID × AdGroup ID × Query | `search_query` | range |
| incentivised | Campaign ID × Date × Incentive Type | — (spend credits) | day (empty in samples) |

**Ad group is part of every breakdown key.** Unlike FK Minutes, 2 of 35 campaigns run more than one ad group. `daily` has no ad group, so headline facts have `ad_group_id = NULL` and `ad_product = 'all'`. Placement and campaign carry the ad group **name** only.

## 3. Column → canonical mapping

| Source column | Target | Kind | Status |
|---|---|---|---|
| Views | `impressions` | base | ⚠ |
| Clicks | `clicks` | base | ✅ |
| Ad Spend / SUM(cost) | `spend` | base | ✅ |
| Total Revenue (Rs.) | `revenue` | base | ✅ ROI = Total Revenue / spend 214/214, 322/322 |
| Direct Revenue + Indirect Revenue | `revenue` (where there is no Total column) | base (two rows, weight +1 each) | ✅ ROI = (D+I)/spend 174/174, 8556/8556 |
| Direct Revenue | `revenue_direct` | base | ✅ placement, keyword, search_term only — **not** in daily or fsn |
| Total converted units / Direct + Indirect Units Sold | `units` | base | ✅ |
| Direct Units Sold | `units_direct` | base | ✅ not in daily |
| ROI, Direct ROI | — | validator | ✅ |
| Expected ROI | `reported.expected_roi` (a target the advertiser sets) | reported | ✅ |
| Click Through Rate in %, Average CPC | — | validator | ✅ 198/198, 174/174 |
| Conversion Rate | — | validator | ⚠ looks like a **fraction, not a %** (0.0512 vs 5.12) |
| AdGroup CPC | `reported.bid_cpc` (a bid) | reported | ✅ |
| Incentive Amount, Ad Service Fees Pre Tax | `ext.incentive_amount`, `ext.service_fee` | ext | ❓ empty in samples |
| order_id, Listing ID, Advertised / Purchased FSN ID | order-level attribution (`breakdown = order`) | dimension | ✅ |
| Sku Id | `dim_product.platform_product_id` (a seller SKU or EAN, **not** an FSN) | dimension | ✅ |

## 4. Headline source and reconciliation (verified)

Headline = **daily** (₹60,575.99 spend, ₹399,619 revenue). Daily has `Total Revenue` and `Total converted units` only, so **`revenue_direct`, `units_direct` and Direct ROAS are not available at headline**. They exist only in the placement, keyword and search_term breakdowns.

| Report | Spend | Revenue | vs daily |
|---|---|---|---|
| fsn | ₹60,575.99 | ₹399,619 | exact ✅ |
| placement | ₹60,575.99 | ₹399,619 | exact ✅ |
| campaign (order lines) | — | ₹399,619 | exact ✅ — every attributed rupee is traceable to an order |
| keyword | ₹24,853.52 | ₹30,226 | 41% coverage |
| search_term | ₹37,929.76 | ₹129,762 | 63% coverage |

Hard checks: fsn = placement = daily (±₹1); campaign revenue = daily revenue. Keyword and search_term are coverage reports.
