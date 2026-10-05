# 15 · BigBasket Ads — column mapping (on hold)

**Status: on hold, no portal key.** UniQCAI lists BigBasket as "Coming soon" (Google sign-in + 2FA) and has no `bigbasket.*` portal yet. A working standalone pipeline exists in digitalUpshot `big-basket/` (branch `feat/bigbasket-standalone`). It keeps the untouched download in `raw/` and, beside it, a copy with date columns stamped in by `bb_stamp.py`. **Stage B reads `raw/` only.**
Evidence: checked on 2026-10-01 against `big-basket/reports/20261001_123822/raw/` (1–30 Sep 2026, one brand), re-checked 2026-10-02.
Markers: ✅ verified · ⚠ assumed · ❓Qn unknown → unified-db question n in [40-domain-expert-questions.md](40-domain-expert-questions.md) (not the PRD §12 list).

## 1. File format

| Property | Value |
|---|---|
| Format | xlsx, one sheet, header row 1, no preamble |
| Date text | three formats: `YYYY-MM-DD`, `YYYY-MM-DD 00:00:00`, `YYYY-MM-DD 00:00:00.0` (creative) |
| File name | carries the range and the export date: `__R(20260901-20260930)__E(20261001)__ID(…)` → used as a cross-check only |
| Brand | `Brand Name` on product rows only; otherwise from the connection |

## 2. Reports and grain

| Report | Grain | Breakdown | Day? | Campaign family |
|---|---|---|---|---|
| performance_summary | account × date | `account` | **day** | performance |
| campaign_performance_report_performance_campaigns | campaign | `campaign` | range | performance |
| products | date × product × campaign | `product` | **day** | performance |
| categories | date × category × campaign | `category` | **day** | performance |
| keyword | date × keyword × campaign | `keyword` | **day** | performance |
| shopper_search_query (performance) | query × keyword × campaign | `search_query` | range | performance |
| purchased_product_report_performance_campaigns | date × campaign × advertised × purchased product (halo) | `halo` | **day** | performance |
| campaign_performance_report_awareness_campaigns | campaign | `campaign` | range | awareness |
| creative_performance_report | date × creative | `creative` | **day** | awareness |
| auction_booking_performance_report | date × booking | `booking` | **day** | awareness (auction) — **no spend column** |
| purchased_product_report_fta / awareness | date × booking/ad × purchased product | `halo` | day | awareness (empty in sample) |
| transaction_report_finance | wallet transaction | — | — | **not ads performance**; ignored in v1 |

## 3. Column → canonical mapping

| Source column | Target | Kind | Status |
|---|---|---|---|
| Ad Impressions / Impressions | `impressions` | base | ✅ |
| Clicks | `clicks` | base | ✅ campaign, auction, creative, search query reports; **not** in summary/products/categories/keyword |
| Ad Spend / Spend / Cost | `spend` | base | ✅ (auction_booking has none) |
| Ad Revenue / Revenue / Revenues | `revenue` | base | ✅ ROAS = Ad Revenue / Ad Spend: 30/30, 611/611, 300/300, 902/902 |
| Ad Revenue − Other SKU Ad Revenue | `revenue_direct` | base (two rows, weights +1 / −1) | ⚠ (products, categories); never negative in sample ✅ |
| Orders (SKU) / Orders | `orders` | base | ⚠ "per SKU" — orders or SKU-lines ❓Q8 |
| Same SKU Orders | `orders_direct` | base | ✅ categories; Same + Other SKU Orders = Orders (SKU) on 300/300 rows |
| Other SKU Orders | — | derived | = orders − orders_direct, not stored |
| Same Category Orders | `ext.same_category_orders` | ext | ⚠ |
| Same Category Ad Revenue | `ext.same_category_revenue` | ext | ⚠ |
| Add to Cart | `atc` | base | ✅ (products only) |
| Purchased Product Units / Orders (SKU) / Ad Revenue | `units` / `orders` / `revenue` at `breakdown = halo` | base | ✅ — the **only** source of `units` |
| Online Purchased Product Units / Orders (SKU) / Ad Revenue | `ext.online_units`, `ext.online_orders`, `ext.online_revenue` | ext | ❓Q22 |
| Offline Purchased Product Units / Orders (SKU) / Ad Revenue | `ext.offline_units`, `ext.offline_orders`, `ext.offline_revenue` | ext | ❓Q22 |
| ROAS, ROI | — | validator | ✅ 100% |
| CPM | — | validator | ✅ = spend/impr×1000 (300/300, 902/902, 7192/7192) |
| CTR, CTR % | — | validator | ✅ auction 142/142; search query 6208/7192 (rounding on tiny rows) |
| CPC | — | validator | ✅ |
| Current Daily Budget | `reported.daily_budget_setting` | reported | ✅ |
| Bid (auction booking) | `reported.bid` — unit unknown | reported | ⚠ |
| Top Search Keyword Impressions % | `reported.top_search_impr_pct` | reported | ✅ |
| Status, Campaign Creation Date, Campaign End Date, Page Type, Flight Start/End | `dim_campaign.*` | dimension | ✅ |
| Product ID, Product Name, Category, Keyword, Keyword ID, Match Type, Search Query, Creative Id, Booking Name | dimensions | dimension | ✅ |
| Creative Image Link | — | ignore (a URL) | ✅ |

## 4. Headline source and reconciliation (verified)

| Report | Spend | Revenue | Clicks |
|---|---|---|---|
| performance_summary (headline, performance ads) | ₹510,404.35 | ₹2,381,624 | — (not in report) |
| campaign_performance (performance) | ₹510,404.33 ✅ | ₹2,381,624 ✅ | 11,648 |
| products | ₹510,404.29 ✅ | ₹2,383,688 (+0.09%) | — |
| categories | ₹510,404.22 ✅ | ₹2,383,688 (+0.09%) | — |
| keyword | ₹241,779.95 (47% coverage) | ₹1,268,123 | — |
| shopper search query | ₹407,947.62 (80% coverage) | — | 10,418 |
| purchased_product (halo, performance) | — | ₹2,422,440 (+1.7%) | — |
| campaign_performance (awareness) | ₹109,679.27 | ₹630,366 | 3,402 |
| creative_performance (awareness, daily) | ₹109,679.23 ✅ | — | 3,402 ✅ |
| auction_booking (awareness, daily) | — (no spend column) | ₹630,366 ✅ | 3,402 ✅ |

Awareness impressions agree too: 1,395,643 in the campaign, creative and auction booking reports.

**Two campaign families, so the headline is a set of sources** (`wh.headline_sources`):
- **Performance ads:** `performance_summary`, daily. It has spend, impressions, revenue and orders, but **no clicks** and **no units**.
- **Awareness ads:** `creative_performance` for daily spend, impressions and clicks. ⚠ Proposed: `auction_booking` for daily revenue and orders only, since its revenue equals the awareness campaign report exactly. Its impressions and clicks repeat creative's, so they are not taken from it (metric-level source selection, or they would count twice).

What this means for the cross-platform view:
- `clicks` at headline: awareness only, so BigBasket clicks are **partial**.
- `units`: only at `breakdown = halo`, never at headline.

Whether awareness spend belongs in the brand's headline ROAS is ❓Q22.
