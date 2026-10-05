# 22 · Access, the metrics API, dashboards and saved preferences

## 1. Who can do what (UniQCAI roles + per-brand grants, PRD §4)

| Who | Unified-store abilities |
|---|---|
| Super admin, Admin | everything below, plus: the **mapping screen** (unmapped and new columns, edit a mapping, activate a version, rebuild); brand aliases; the **Loads** and **Warehouse feeds** screens (§7): approve or quarantine loads, set what feeds the warehouse; see every brand |
| toggle_admin | everything an Admin can (PRD:78), plus the visibility switchboard. The switchboard may hide or lock the analytics nav section per audience; that is presentation only, never access (PRD §4a) |
| Member with a **Manager** grant on a brand | dashboards and drill-downs for that brand; their own saved views and dashboards; see load status and freshness for that brand |
| Member with an **Executive** grant on a brand | dashboards and drill-downs for that brand; their own saved views and dashboards |
| Any grant limited to **Sales** (FR-5a) | **no** Ads metrics for that brand. The brand is listed only if another category grants it |

**Several brands at once.** A user selects any subset of the brands they hold grants on.
- Agency staff with grants on many brands see all of them.
- A client company that owns several brands gets a grant on each, and sees exactly those.
- There is no "organisation" entity. **An empty selection means no data, never "all brands".**

**Enforcement.** Every query goes through `scope_to_user_brands(query, user, category_column=…)` (`app/core/rbac.py:111`), with category = `ads`.
- A brand id the user cannot see returns **404 with the standard body** (`app/core/rbac.py:36` `not_found()`). It is never a 403, and never a partial answer that reveals the brand exists.
- The API intersects requested brand ids with the user's scope **on the server**. The UI hiding a brand is never the control.
- The admin screens of §7 are admin-only, and each endpoint gets an RBAC test (CLAUDE.md rule 2).

## 2. Metrics API

```
GET  /api/metrics/catalogue
     → metrics (from wh.metric_definitions), dimensions, charts this user may use,
       and per platform which metrics exist at headline (from wh.metric_availability),
       so the UI can say "not available for Blinkit"

POST /api/metrics/query
     { metrics: ["spend","roas","ctr"],
       dimension: "date" | "platform" | "brand" | "campaign" | "product" | "city" | "keyword" | …,
       filters: { brand_ids: [..], platforms: [..], ad_products: [..], date_from, date_to,
                  campaign_ids?, product_ids?, cities?, text?: "contains" filters for tables },
       compare: null | "previous_period" | "previous_year",
       breakdown: null  (= headline) | "keyword" | … ,
       sort, limit }
     → { rows, totals, compare_rows,
         coverage: { requested, collected,
                     missing: [ {platform, reason, days} ],
                     metrics: [ {metric, platform, available: bool, reason} ] },
         freshness: [ {brand_id, platform, data_through, last_published_at} ],
         provisional_days: [..], source_file_ids: [..], took_ms }
```

Rules:
- `metrics` and `dimension` are whitelisted. Free SQL is never accepted.
- The server picks the cheapest table that can answer: `mart.ad_daily` → `mart.ad_daily_campaign` / `_product` → `wh.fact_ad`.
- `breakdown: null` reads only `wh.headline_sources`. Summing two breakdown reports is impossible ([04](04-grain-and-double-counting.md) §1).
- **Coverage is per metric and platform.** `SUM()` drops NULLs silently, so a cross-platform total of clicks with Blinkit selected would be partial without saying so. Clicks, and so CTR and CPC, are not reported at headline by Blinkit, FK Minutes or BigBasket. The response lists each such pair in `coverage.metrics`, and the total is labelled partial.
- **Freshness** ("data through …", PRD B4) comes from `mart.freshness`: the last day with published headline data per brand and platform.
- The response says when an answer is partial (`coverage`). It never silently drops a platform.

> **2026-10-03:** §2–§5 are superseded by the analytics builder ([24](24-analytics-builder.md)): a free, no-code builder over one query spec (`POST /api/v1/analytics/query`), many chart types, shareable dashboards. The rules here — whitelisted fields, headline sources only for totals, coverage per metric and platform, freshness, RBAC, empty selection = no data — all carry over unchanged.

## 3. Chart catalogue (v1) — users pick from these

| chart_key | Shows | Good for |
|---|---|---|
| `kpi_tile` | one metric, the change vs the comparison period, a sparkline, a provisional marker | the morning glance |
| `trend_line` | a metric over days or weeks, one line per brand or platform | "how am I growing" |
| `stacked_bar` | spend or revenue split by platform or brand | the mix across platforms |
| `ranked_table` | top N campaigns, products, keywords, cities or search queries; sortable; per-column filters (contains, >, <, between); column picker | the Excel-like analysis |
| `scatter` | spend vs ROAS per campaign or product | finding waste |
| `heat_table` | city × platform or brand × platform | geographic and brand comparison |

Each chart declares which metrics and dimensions it accepts. The API refuses any other combination. Ratios always come from sums (see [02-metric-dictionary.md](02-metric-dictionary.md)).

## 4. Default dashboard (everyone starts here)

1. **Filter bar:** brands (multi), platforms (multi), ad type, period (presets plus custom, IST), and a comparison.
2. **Freshness line:** "Data through 1 Oct" per platform, or the oldest of them with a hover list.
3. **KPI tiles:** Ad spend · Ad revenue · ROAS · Orders or units · CTR · CPC. A tile whose metric is missing for some selected platforms says so ("CTR: not available for Blinkit").
4. **Trend line** of spend and ROAS.
5. **Platform split** (stacked bar).
6. **Top campaigns** (ranked table).

Which KPIs are on the default is ❓Q1. Week start and provisional days are ❓Q15.

## 5. Personalisation

- **Saved views** (`app.saved_views`): a named filter state. It can be set as the user's default, and is reopened from a menu.
- **My dashboards** (`app.dashboards`, `app.dashboard_widgets`): add, remove and reorder widgets chosen from the catalogue. Each widget sets its metrics, dimension and filters.
- Dashboards are **personal** in v1. Sharing a dashboard with another user is a later decision. When it comes, the viewer always sees it through *their own* grants.
- The URL keeps carrying the live filter state, so a link works and the back button works. Saving a view stores that same state.

## 6. Status words in the UI

Every status is an icon plus a word:
- **Provisional**: inside the platform's restatement window.
- **Not available**: the platform doesn't report it.
- **Partial**: some platforms or days missing; hover lists them.
- **Restated**: the number changed after an earlier pull.
- **Data through 1 Oct**: freshness, when the latest day is older than yesterday for any selected platform.

No enum names, ids or portal keys appear outside a "Technical detail" disclosure.

## 7. Admin screens for the warehouse

These two admin pages arrive in phase 2 for Zepto and are specified in `docs/UI_PLAN.md` §3.14–3.15. The mapping screen, dashboards and "Source files" panel are added in phase 5; until then an unmapped column shows on the Loads screen, under its load's `header` check.

**Warehouse feeds** (`ingest.report_policies`):
- Grouped Platform → Category → Report, as everywhere else.
- Per report: a **feed toggle**, the restatement window, weekly reconciliation, the mapping status, and **the schedules that pull it**, with "create the recommended schedule" (daily previous day split by day, plus the Monday `week_to_date` range pull when weekly reconciliation is on). There is no cadence select: one scheduler (DECISIONS 2026-10-02).
- Each row shows its **estimated cost** in minutes per brand per day, from measured `run_tasks` durations. An admin can see, for example, that one Zepto report daily, split by day, costs about ½ min per brand, and all 18 about 11–12 min.
- A backfill longer than about a week of split-by-day Zepto pulls is offered as several runs, because one run must fit the 2 h cap ([04](04-grain-and-double-counting.md) §3).
- Changes are optimistic, with a toast and an audit entry.

**Loads** (`ingest.loads`, `ingest.checks`):
- A `DataTable` of loads with filters in the URL: platform, report, brand, status, period.
- Per load: status, the file (with its original download), hard and soft check results, slice outcomes (new, unchanged, restated, stale), and for a quarantined load its reason and re-pull suggestion.
- Actions: approve, quarantine with a reason, re-pull (through the existing Run now path).
