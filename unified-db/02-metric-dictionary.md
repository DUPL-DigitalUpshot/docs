# 02 · Canonical metric dictionary (Ads)

This is the single list of names the unified store and the dashboards use. Each platform's mapping file (10–15) maps its columns onto these names. A key that is not declared here cannot be used in a mapping.

## 1. Rules

1. **Store independent numbers only.** A ratio is never stored as a metric. ROAS, CTR, CPC, CPM and the like are computed from sums at query time, because a ratio is only valid at the grain it was computed at.
2. **Ratio of sums, never average of ratios.** ROAS for a month = Σrevenue / Σspend. It is not the average of the daily ROAS values.
3. **NULL ≠ 0.** NULL means the platform does not report this metric; 0 means the platform reported zero. A derived metric with any NULL input is "not available". It is never 0, and never computed from a partial set of platforms without saying so.
4. **"Indirect" is never stored.** indirect = total − direct, and only where direct is a **subset** of total: same attribution window, same scope. Where that is not known (Instamart: `TOTAL_GMV`'s window is unknown vs the 14-day direct, ❓Q3, see [12](12-mapping-instamart.md)), the indirect metric is marked **not available** for that platform. Instamart's direct never exceeds its total on any row checked, so the reason is the window, not a negative result.
5. **Platform-reported ratios are validators.** They are kept in `stage.parsed_rows.raw_row_json` and used to prove our maths matches the platform's (see [21-validation-and-originals.md](21-validation-and-originals.md)). They never reach a chart.
6. **"Direct" and "same-SKU" are one concept, with a caveat.** Blinkit and Flipkart say Direct / Indirect; Zepto and BigBasket say same-SKU / other-SKU. Both are stored as `*_direct`. They are close but **not proven equivalent** (`docs/research/blinkit-ads-schema.md` §4), so each mapping row that does this carries the note "direct read as same-SKU", and cross-platform `*_direct` charts show that caveat.
7. **Duplicate source rows are summed to the declared grain.** Each report declares its fact key in its mapping file. Rows that share the key are summed (Blinkit bid levels, Instamart granular). A `reported.*` value on a summed row is kept only when every summed row carries the same value; otherwise it is NULL on the fact, and the source rows stay in `stage.parsed_rows`.
8. **One target may have several source rows.** A mapping row carries a `weight` (+1 or −1), so "Direct + Indirect" and "Ad Revenue − Other SKU Ad Revenue" are data, not code.

### Kind vocabulary

Every row of a mapping table has one **Kind**:

| Kind | Stored where | Summed? |
|---|---|---|
| `base` | a column of `wh.fact_ad` (§2) | yes |
| `ext` | `wh.fact_ad.ext jsonb` (§3) | yes, one platform at a time |
| `reported` | `wh.fact_ad.reported jsonb` (§4) | **never** |
| `derived` | not stored; formula in `wh.metric_definitions` (§5) | computed from sums |

A source column that feeds no stored target is a `validator` (a platform ratio, rule 5), a `dimension`, or `ignore`.

In `ingest.column_mappings.role` ([20](20-schema.md)) the Kind `base` is spelled **`metric`**; `ext`, `reported`, `validator`, `dimension` and `ignore` keep their names, and `date` and `brand` are roles of their own. A `derived` metric has no mapping row.

## 2. Base metrics — stored, additive

| Key | Display name | Unit | Meaning |
|---|---|---|---|
| `impressions` | Impressions | count | times an ad was shown |
| `clicks` | Clicks | count | total (not unique) clicks on an ad |
| `spend` | Ad spend | ₹ | money consumed by ads, as the platform reports it |
| `atc` | Add to cart | count | cart additions attributed to ads |
| `atc_direct` | Add to cart (advertised SKU) | count | the part of `atc` on the advertised SKU |
| `revenue` | Ad revenue | ₹ | ad-attributed sales value, using the platform's headline attribution |
| `revenue_direct` | Ad revenue (advertised SKU) | ₹ | the part of `revenue` on the advertised SKU |
| `orders` | Orders | count | ad-attributed orders |
| `orders_direct` | Orders (advertised SKU) | count | the part of `orders` on the advertised SKU |
| `units` | Units sold | count | ad-attributed units |
| `units_direct` | Units sold (advertised SKU) | count | the part of `units` on the advertised SKU |
| `ntb_users` | New-to-brand customers | count | first-time buyers of the brand |

## 3. Platform extension metrics (`ext.*`) — stored, additive, single-platform only

These sit in `wh.fact_ad.ext jsonb`. They can be charted only while exactly one platform is selected.

| Key | Platform | Unit | Meaning |
|---|---|---|---|
| `revenue_direct_7d` | Instamart | ₹ | 7-day direct GMV |
| `branded_clicks` | Instamart | count | branded-search clicks ❓Q24 |
| `claimables` | Blinkit | ₹ | MTD control figure; = min(served, Total Budget) ❓Q6 |
| `served_budget` | Blinkit | ₹ | MTD `served_budget_consumed`, the control total for Σ daily spend ❓Q6 |
| `online_units`, `online_orders`, `online_revenue` | BigBasket | count / count / ₹ | halo purchases, online channel ❓Q22 |
| `offline_units`, `offline_orders`, `offline_revenue` | BigBasket | count / count / ₹ | halo purchases, offline channel ❓Q22 |
| `same_category_orders`, `same_category_revenue` | BigBasket | count / ₹ | attributed orders and revenue in the advertised product's category |
| `incentive_amount`, `service_fee` | Flipkart marketplace | ₹ | incentivised-spend credits and pre-tax ad service fees |

## 4. Reported values (`reported.*`) — stored as-is, never summed

`wh.fact_ad.reported jsonb`. These are shown only at the grain they came at, and never added up across rows or days. Budgets and bids are **campaign settings, never spend**.

| Key | Platform | Source column | Meaning |
|---|---|---|---|
| `robas` | Zepto | Robas | unknown ratio ❓Q7 |
| `ntb_pct` | Zepto | New_to_brand_user_percentage | share of new-to-brand users ❓Q9 |
| `unique_reach`, `unique_considerations` | Zepto | Unique_reach, Unique_considerations | unique users |
| `daily_budget_avg` | Zepto SP | Daily_budget | an **average** daily budget over the range, not the setting |
| `daily_budget_setting` | Zepto SB, BigBasket | Daily_budget (SB), Current Daily Budget | the daily budget setting |
| `budget_total` | Blinkit, Instamart | Total Budget / total_budget, TOTAL_BUDGET | total budget setting |
| `unique_clicks` | Blinkit | Unique Clicks | unique clickers |
| `reach` | Blinkit | Reach | unique users reached |
| `most_viewed_position` | Blinkit | Most Viewed Position | rank |
| `on_hold_at` | Blinkit | latest on hold timestamp | last time the campaign went on hold |
| `bid_cpm` | Blinkit | CPM | the CPM **bid**, not a realised rate |
| `bid_cpc` | Flipkart marketplace | AdGroup CPC | the CPC bid |
| `bid` | BigBasket | Bid (auction booking) | booking bid, unit unknown ⚠ |
| `ad_rank` | Instamart | AD_RANK | rank |
| `uptime_pct` | Instamart | CAMPAIGN_UPTIME_PERCENTAGE | share of the day the campaign was live |
| `budget_exhausted_at` | Instamart | BUDGET_EXHAUSTION_TIME | clock time the budget ran out |
| `targeting` | Instamart | TARGETING (granular) | targeting label ⚠ |
| `cpb` | FK Minutes | Average CPB / Average Cost per Basket | platform's cost per basket; ≠ spend / actions |
| `expected_roi` | Flipkart marketplace | Expected ROI | the advertiser's target ROI |
| `top_search_impr_pct` | BigBasket | Top Search Keyword Impressions % | share of impressions at top of search |

## 5. Derived metrics — formulas in `wh.metric_definitions`

| Key | Display | Formula | Format |
|---|---|---|---|
| `roas` | ROAS | Σrevenue / Σspend | 4.20× |
| `roas_direct` | ROAS (advertised SKU) | Σrevenue_direct / Σspend | 3.10× |
| `acos` | Ad cost of sales | Σspend / Σrevenue | 23.8% |
| `ctr` | Click-through rate | Σclicks / Σimpressions | 1.80% |
| `cpc` | Cost per click | Σspend / Σclicks | ₹6.40 |
| `cpm` | Cost per 1,000 impressions | Σspend / Σimpressions × 1000 | ₹120 |
| `atc_rate` | Add-to-cart rate | Σatc / Σimpressions | 0.90% |
| `cvr_orders` | Conversion rate | Σorders / Σclicks | 7.0% |
| `cpo` | Cost per order | Σspend / Σorders | ₹85 |
| `cost_per_unit` | Cost per unit sold | Σspend / Σunits | ₹40 |
| `aov` | Average order value | Σrevenue / Σorders | ₹310 |
| `revenue_indirect` | Ad revenue (other SKUs) | Σrevenue − Σrevenue_direct (rule 4) | ₹ |
| `units_indirect`, `atc_indirect`, `orders_indirect` | … (other SKUs) | total − direct (rule 4) | count |
| `spend_share` | Share of spend | Σspend(slice) / Σspend(all selected) | % |
| `revenue_share` | Share of ad revenue | Σrevenue(slice) / Σrevenue(all) | % |

The display names above are placeholders. The names clients expect (ROAS vs ROI vs ROBA vs ACOS) are ❓Q7.

## 6. Units and money

- All money is INR. No platform states a currency except Flipkart's "(Rs.)". Zepto money is whole rupees ✅. Instamart, Blinkit, Flipkart and BigBasket use decimal rupees.
- Money is stored as `numeric(14,2)`, never float.
- Rounding happens only in the UI. Zepto's own CPC and CPM round half-to-even; the validator reproduces that, while our own display uses ordinary rounding.

❓Qn in these files = unified-db question n in [40-domain-expert-questions.md](40-domain-expert-questions.md), not the PRD §12 list.
