# 13 · Flipkart Minutes Ads — column mapping

Portal `fkminutes.ads` (advertising.flipkart.com, "Select Report For: Minutes") · report keys `daily`, `fsn`, `attribution`, `zone`, `search_term`, `placement`, `keyword` · max 31 days per pull
Evidence: **no verified schema doc existed, and UniQCAI has produced no FK Minutes file yet** (every run so far stopped at `WRONG_ACCOUNT`). All evidence is from digitalUpshot `fk-minutes/reports_minutes/` (copied to `samples/fkminutes/reports_minutes/`): first checked 2026-10-01 on `2026-09-04_13-45-54/` (1–31 Aug 2026, Harvest Gold; daily 186 rows), re-checked 2026-10-02 on every pull, two accounts. Formula results are quoted below.
Markers: ✅ verified on real rows · ⚠ assumed · ❓Qn unknown → unified-db question n in [40-domain-expert-questions.md](40-domain-expert-questions.md) (not the PRD §12 list).

## 1. File format

| Property | Value |
|---|---|
| Format | CSV with a **2-row preamble**: `Start Time, 2026-08-01 00:00:00` and `End Time, …`. The keyword report adds 2 note rows (header on row 5): "Keyword Reports only capture performance at Top of Search (TOS) and Bottom of Search (BOS)" |
| Numbers | 4 decimal places as text (`793.2300`) |
| Date column | `Date` in daily, `date` in attribution. The other reports are **range totals** |
| Brand | no brand column → the brand comes from the connection |
| Column names | inconsistent spelling across reports: `Ad Spend` / `Ad spend`, `Ad Group ID` / `AdGroup ID`, `Units Sold (Direct)` / `Direct Units Sold` |
| Ad group columns | daily has `Ad Group ID` + `AdGroup Name`; keyword has `AdGroup ID` but **no name**; search_term has `AdGroup Name` but **no ID** ✅ |
| Empty files | `zone` is header-only (233 B) in **every** pull. Several pulls are header-only for all 7 reports (158–552 B) |

**Empty-file rule.** A file that parses, has a valid header and has zero data rows is **"no activity"**, not an error. The load is published with 0 facts (its slices still advance `last_observed_at`) and is **flagged** on the Loads list, because a whole pull of empty files can also mean the wrong account or a portal outage.

## 2. Reports and grain

| Report key | Declared grain (fact key) | Breakdown | Day? | Status |
|---|---|---|---|---|
| `daily` | Campaign ID × Ad Group ID × Date | `campaign` | **day** | ✅ unique on Campaign ID × Date already |
| `fsn` | Campaign ID × Ad Group ID × FSN | `product` | range | ✅ |
| `attribution` | FSN × date × campaign — units only | `product` (units) | **day** | ✅ |
| `placement` | Campaign ID × Ad Group ID × placement_type | `placement` | range | ✅ |
| `keyword` | Campaign ID × AdGroup ID × keyword × match type (TOS/BOS only) | `keyword` | range | ✅ |
| `search_term` | Campaign ID × AdGroup **Name** × Query | `search_query` | range | ⚠ no ad group ID in this report |
| `zone` | business zone × FSN | `zone` | range | ❓ empty in every pull |

**Ad group.** In all data checked, every campaign has exactly **one** ad group. The ad group stays in every key anyway, as a safeguard: Flipkart marketplace (14) on the same site does run several ad groups per campaign.

**Ad product at headline.** `daily` has no placement column, so headline facts carry `ad_product = 'all'`.

## 3. Column → canonical mapping

### Metrics

| Source column | Target | Kind | Transform | Status |
|---|---|---|---|---|
| Views | `impressions` | base | int | ⚠ "Views" taken as ad impressions |
| Ad Spend / Ad spend | `spend` | base | ₹ | ✅ |
| Actions | `atc` | base | int — basket additions (the placement report calls its cost "Cost Per Basket Addition") | ⚠ ❓Q5 |
| Clicks (keyword report only) | `clicks` | base | int | ✅ only at keyword breakdown; NULL elsewhere |
| Direct Revenue + Indirect Revenue | `revenue` | base | two rows, weight +1 each | ✅ ROI = (D+I)/spend 44/44, 742/742 |
| Direct Revenue | `revenue_direct` | base | | ✅ ROI (Direct) = Direct Revenue / spend 186/186 |
| Units Sold (Direct) + (Indirect) · Direct + Indirect Units Sold | `units` | base | two rows, weight +1 each | ✅ |
| Units Sold (Direct) / Direct Units Sold | `units_direct` | base | | ✅ |
| Indirect Units Sold (keyword, search_term) | feeds `units` only | base (weight +1) | never stored alone | ✅ |
| Units (attribution) | `units` at product × day | base | = Direct + Indirect (21,733 = 21,733) | ✅ |
| ROI (Direct), ROI (Indirect), ROI, Direct ROI | — | validator | revenue / spend | ✅ 100% |
| Action Rate | — | validator | = Actions / Views ×100 | ✅ 186/186 |
| CVR | — | validator | = (Direct + Indirect units) / Actions ×100, so it **can exceed 100** | ✅ 186/186 |
| Average CPC (keyword) | — | validator | = spend / clicks | ✅ 44/44 |
| Click Through Rate in % | — | validator | = clicks / views ×100 | ✅ 47/47 |
| Direct Conversion Rate in % | — | validator | = direct units / clicks (keyword) or / actions (search_term) ×100 | ✅ |
| Indirect Conversion Rate in % (search_term) | — | validator | = indirect units / actions ×100 | ✅ 2,686/2,686 |
| Average CPB (Cost Per Basket Addition), Average Cost per Basket | `reported.cpb` | reported | **does not equal spend / actions** (matches on only 4/81, 1/42 and 0/28 rows) | ❓ definition unknown; never derived |

### Dimensions

| Source column | Target | Status |
|---|---|---|
| Date / date | `date` | ✅ |
| Campaign ID (12-char code), Campaign Name | `dim_campaign` | ✅ |
| Ad Group ID / AdGroup ID, AdGroup Name | `wh.dim_ad_group` (resolved by ID where present, by name in search_term) | ✅ |
| FSN ID / FSN, Product Name | `dim_product` (FSN = Flipkart product id) | ✅ |
| placement_type | `dim_placement` | ✅ |
| attributed_keyword, keyword_match_type | `breakdown_key`, `match_type` | ✅ |
| Query | `breakdown_key` (search_query) | ✅ |
| Business Zone | `breakdown_key` (zone) — not a city; a zone dimension waits for ❓Q12 | ❓Q12 |

## 4. Headline source and reconciliation

Headline = **`daily`**. Harvest Gold, 1–31 Aug 2026 (checked 2026-10-01):

| Report | Spend | Revenue (D+I) | vs daily |
|---|---|---|---|
| daily | ₹249,884.20 | ₹1,164,683 | — |
| fsn | ₹249,884.20 | ₹1,164,683 | **exact** ✅ |
| placement | ₹249,884.20 | ₹1,164,683 | **exact** ✅ |
| keyword | ₹208,199.20 | ₹1,015,131 | 83% |
| search_term | ₹208,199.20 | ₹1,015,445 | 83% |

**Coverage is account-specific** (re-check 2026-10-02). On the second account, keyword covers **40–43%** of daily spend and search_term **78–86%**, and the two differ from each other. The equal 83% above is a property of that one account, not a rule.

Control rule: fsn and placement must equal daily within ₹1 (hard). Keyword and search_term are coverage reports (informational) and are never reconciled to 100%.

**Restatement ✅ (revenue and units, not spend).** Re-check 2026-10-02 on repeated `daily` pulls of the same campaign-days:

| Pulls compared | Campaign-days | Spend | Revenue (D+I) |
|---|---|---|---|
| account 1: 31 Aug (24–30 Aug) vs 4 Sep (1–31 Aug) | 42 | 0 differ | 42 differ; **+17.4%** in total, +14.7% to +20.3% per day |
| account 2: 31 Aug (29–30 Aug) vs 4 Sep (1–31 Aug) | 8 | 0 differ | 7 differ; **+13.0%** in total |
| account 2: two pulls on 4 Sep, 2 h apart (24–30 Aug vs 1–31 Aug) | 28 | 0 differ | 10 differ; +1.7% in total |
| repeated pulls on 31 Aug, same range | 36–42 | 0 differ | 0 differ |

- Attributed revenue for 24 Aug grew +19.5% between the day being 7 and 11 days old, so the window is longer than the 5-day default. ⚠ Proposed until ❓Q14 is answered: a **14-day** restatement window for `fkminutes.ads`, with the daily pull re-reading the last 14 days (`report_policies.restatement_window_days`).
- The two same-day pulls had different ranges, so a range effect (revenue counted only up to the requested end date) is not ruled out. ❓ to verify with two same-range pulls on one day.

## 5. Open questions

❓Q5 Actions vs clicks · ❓Q12 zones · ❓Q14 restatement window (revenue still changing after 7 days) · plus: what "Average CPB" really measures (ask Flipkart).
