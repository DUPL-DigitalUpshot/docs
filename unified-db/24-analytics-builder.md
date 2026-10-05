# 24 · The analytics builder: a no-code, PivotTable-style dashboard builder

Owner decisions 2026-10-03: a free builder (supersedes README D6), built now (phases 4–5, step-7 gate waived for these), and dashboards that can be shared — each viewer sees them through their own grants.

**The principle.** Users may ask almost anything; **the server decides how it is computed**. Freedom never yields a wrong number:
- ratios come from sums ([02](02-metric-dictionary.md));
- two breakdown reports are never added together ([04](04-grain-and-double-counting.md));
- NULL ≠ 0;
- coverage, provisional days and freshness are always shown ([22](22-access-and-dashboards.md) §2, §6);
- access is enforced on the server and again by row-level security.

The UI offers only what the server can answer correctly. Where a choice is valid but unusual, it says what it does instead of refusing.

## 1. Who uses it, and how deep

| Level | For | What they do |
|---|---|---|
| **Start** | everyone | Open the default dashboard or a template ("How is spend trending?", "Which campaigns waste money?", "Platform mix", "Top products"). Change brand, platform and period in the dashboard filter bar; every chart follows. |
| **Build** | most users | **Edit** a chart. The side panel shows a field list — Money · Volume · Rates · Time · Where · What — and four wells: **Rows / X**, **Split by / Series**, **Values**, **Filters**. Drag a field into a well, or click **+**. A chart-type strip marks ★ the recommended types. The preview updates as you go. |
| **Advanced** | power users | Per value: aggregation and **Show as** (% of total, % of row/column, running total, change vs previous period, rank). Top N + Other. Metric filters (spend > ₹5,000 per campaign). Any/all filter groups. Week start. Axis and number format. Dual axis. Reference lines. Sort by any metric. |

Everyone with an Ads grant builds: admins, managers and executives. Editing is a desktop task. On phones, dashboards are view-only in one column.

## 2. The query spec — one contract for UI, API and storage

```json
{ "v": 1, "source": "ads",
  "values":  [{ "metric": "spend", "agg": "sum", "show_as": null },
              { "metric": "roas",  "agg": "ratio" }],
  "rows":    [{ "dim": "date", "bucket": "week" }],
  "columns": [{ "dim": "platform" }],
  "filters": { "op": "and", "items": [
      { "dim": "brand",    "op": "in",       "values": [2] },
      { "dim": "campaign", "op": "contains", "value": "diwali", "enabled": true },
      { "metric": "spend", "op": ">", "value": 5000, "level": "campaign" } ] },
  "period":  { "type": "rolling", "unit": "day", "n": 30 },
  "compare": "previous_period",
  "sort":    [{ "by": "spend", "dir": "desc" }],
  "top":     { "n": 10, "other": true },
  "week_start": "mon" }
```

- **`period`** is one of the following. A rolling period stays relative when saved.
  - `{type: rolling, unit: day|week|month, n}`
  - `{type: preset, key: today|yesterday|wtd|mtd|qtd|ytd|last_week|last_month|last_quarter|last_year}`
  - `{type: custom, from, to}`
  - `{type: all}`
- **`compare`** is null, `previous_period` or `previous_year`.
- **The chart is stored next to the spec, never inside it** (`{type, options}`). Switching chart type only remaps wells to encodings, so nothing is rebuilt. Anything the new chart can't draw stays in the spec, greyed: "not used by a pie chart".
- **`v` versions the spec.** A server-side upgrader keeps every saved dashboard opening.

## 3. Fields

### 3.1 Metrics and their aggregations

| Kind ([02](02-metric-dictionary.md)) | Examples | Offered | Default |
|---|---|---|---|
| base money / count | spend, revenue, impressions, clicks, orders, units | **Sum**; average / min / max **per day, week or member** (the per-bucket sums, then averaged); count of members with data; % of total via Show as | Sum |
| derived rate | ROAS, CTR, CPC, CPM, CVR, CPO, AOV, ACOS | **From totals**: the ratio of the sums in every cell, subtotal and total. Under Advanced: *simple average of each day's rate*, labelled "unweighted" | From totals |
| derived difference | revenue (other SKUs), orders (other SKUs) | Sum of the difference; "not available" where direct isn't a subset (Instamart) | Sum |
| share | spend share, revenue share | from totals over everything selected | — |
| `ext` (one platform only) | Blinkit claimables, Instamart branded clicks | as base, **only while exactly one platform is selected**; otherwise greyed with the reason | Sum |
| `reported` | bids, budgets, ranks | never aggregated; shown only in tables at their own grain | — |

- **NULL ≠ 0.** A cell with no reporting platform is blank, never 0.
- **Partial totals.** A total that leaves out a platform which doesn't report the metric is marked **Partial**, with a tooltip naming the platforms: "CTR: not available for Blinkit".
- **Metric names** follow [02](02-metric-dictionary.md) until ❓Q7 settles them.

### 3.2 Dimensions

| Group | Dimension | Notes |
|---|---|---|
| Time | date, bucketed day · week · month · quarter · year (IST) | week start Monday by default (❓Q15), set per chart |
| Where | brand, platform, ad type, city*, placement* | brand only within the viewer's grants |
| What | campaign, ad group, keyword*, search query*, product* | campaign and ad group by id; names from `wh.dim_*` |

\* **breakdown** dimensions. **At most one per chart**, because each fact row carries a single breakdown and the reports can't be combined ([04](04-grain-and-double-counting.md) §1). A chart may combine any number of spine dimensions (time, brand, platform, ad type, campaign, ad group) with that one breakdown.

### 3.3 Where numbers come from (decided by the server)
- **No breakdown dimension:** only `wh.headline_sources`, so totals never double count.
- **A breakdown dimension:** that platform's one breakdown report, plus:
  - its **coverage share** ("keywords explain 61% of this spend");
  - a **Not broken down** remainder row, so the column still adds up to the headline.
- **Trends** use day rows. Range rows answer only their exact period, or a period built from non-overlapping ranges. Otherwise the period is listed under `coverage.missing`.
- **Table choice**, cheapest first:
  - `mart.ad_daily` (brand × platform × ad type × day);
  - `mart.ad_daily_campaign`;
  - current rows of `wh.fact_ad` (partition-pruned) for breakdowns.

## 4. Filters

- **Dashboard filters** live in the URL, so links and Back work: brands, platforms, ad type, period, comparison.
  - Every chart follows them.
  - A chart can **add** filters or **override** the period. An override shows as a badge on the chart ("This chart: last 90 days").
- **Each filter is a chip.** Open it to edit; you can also disable it (kept, but not applied), reorder it or remove it. Kinds:
  - **Dimension:** *is any of*, *is not*, *contains*, *starts with*.
  - **Metric** (applied after aggregation, at a chosen level): *>*, *<*, *between*, *top / bottom N*.
  - **Combining:** clauses combine with AND; values inside one clause combine with OR. Advanced offers *any/all* groups.
- **Filter impact.** Each chip shows what it keeps, e.g. "keeps 64% of spend · 12 of 40 campaigns", from `POST /analytics/filter-impact`. A footer sentence explains the chart, e.g. "Ad spend by week · Dinshaw's · Zepto · 1–30 Sep 2026 · 3 filters".
- **Empty selection.** No brands selected means **no data**, never "all brands" ([22](22-access-and-dashboards.md) §1).

## 5. Charts

**Types:**
- KPI tile (value, change vs comparison, sparkline)
- line; area; stacked area
- bar (vertical or horizontal); stacked bar; 100% stacked
- combo (bars + line, dual axis)
- pie / donut
- scatter / bubble
- heatmap table
- **pivot table** (rows × columns × values, subtotals and grand totals recomputed correctly, expand/collapse, conditional colour, frozen headers)
- ranked table (per-column filters, column picker)

**Recommendations** are rules, shown with a ★ and never forced:

| You have | Recommended |
|---|---|
| a time dimension | line (area when one series is split) |
| one category, ≤ 8 members | bar; pie when one value |
| one category, > 8 members | ranked table or bar with Top 10 + Other |
| money + a rate | combo, rate on the right axis |
| two dimensions | heatmap or pivot table |
| two metrics, one category | scatter |
| one value, no dimension | KPI tile |

A 40-slice pie is still allowed. It comes with a hint: "Too many slices to read — try Top 8 + Other".

**What every chart shows:**
- **Provisional** days (hatched; inside the restatement window, `ingest.report_policies`);
- **Restated** markers;
- **Partial** and **Not available**;
- **Data through 1 Oct**.

**Source files:** clicking a point, bar or cell opens **Source files**, the original reports behind that number (`source_file_ids`), with *Download original*. This is the cross-validation path back to the untouched files ([21](21-validation-and-originals.md)).

**Accessibility:** every chart has **View as table**. Drag and drop works from the keyboard. Colours come from the series palette in THEME.md, AA-checked in light and dark mode.

## 6. Save, duplicate, reset, reuse, share

| Action | Behaviour |
|---|---|
| Save / Save as | Save as duplicates the dashboard. Saves are versioned. A stale save returns 409: "Someone else changed this dashboard — reload or save as a copy". |
| Reset | Back to the last saved version. Undo/redo while editing. "Unsaved changes" marker. |
| Duplicate a chart | Within the dashboard. |
| My charts | Save a chart, then add it to any dashboard. |
| Templates | Admins publish them; anyone starts from one. The default dashboard ([22](22-access-and-dashboards.md) §4) is a template. |
| Saved views | A named filter state on a dashboard, optionally the default. |
| Share | With named users, or "everyone with access to <Brand>". Read-only by default, with an optional *can edit*. The viewer's own grants apply: a brand they can't see drops out, and a Sales-only viewer sees no Ads data. |

## 7. Security

- **RBAC.** Every query uses `scope_to_user_brands(…, category_column=ads)` with the viewer's scope. Sharing never widens it. An unknown or unseen brand id returns 404 with the standard body.
- **Row-level security** (defence in depth, agreed 2026-10-03):
  - Analytics queries run as a read-only role, `uniqcai_reader`.
  - Policies on `mart.*` and `wh.fact_ad` admit only `brand_id = ANY(current_setting('app.allowed_brands'))`. The request sets that value with `SET LOCAL` from its RBAC scope.
  - If application code ever forgets the scope, the database still returns nothing.
  - The ingest and owner roles are unchanged.
- **No free SQL.** Fields come from a whitelist and the compiler builds SQLAlchemy Core. Statements have a timeout.

## 8. Storage

- **`mart` schema:**
  - `mart.ad_daily` and `mart.ad_daily_campaign` (NULLs preserved);
  - `mart.ad_period` (exact-period range rows);
  - `mart.freshness`;
  - `mart.refresh_log`.
  
  Refresh is incremental per (brand, platform, date range): delete + insert in one transaction. The parser runs it after every publish, retraction or restatement, so a published import shows in charts within seconds. A test asserts mart totals = current `wh.fact_ad` headline totals.
- **`app` schema:**

  | Table | Holds |
  |---|---|
  | `app.dashboards` | owner, name, description, layout, filters, is_template, version |
  | `app.dashboard_versions` | the last N saves |
  | `app.widgets` | title, chart, spec, grid position |
  | `app.saved_charts` | reusable charts |
  | `app.dashboard_shares` | user, or brand + audience; can_edit |
  | `app.saved_views` | named filter states |

  Every write is audited.

## 9. API (`/api/v1/analytics`)

| Endpoint | Does |
|---|---|
| `GET /catalogue` | metrics (with kind, unit, allowed aggregations), dimensions (spine / breakdown), per-platform availability, chart types with their wells, recommendation rules |
| `POST /query` | spec → `{rows, totals, compare_rows, coverage, freshness, provisional_days, restated, source_file_ids?, took_ms}`; refusals carry `{detail, code}` |
| `POST /filter-impact` | spec + a filter → what it keeps |
| `GET/POST/PATCH/DELETE /dashboards…` | CRUD, versions, duplicate, reset, shares, saved views, templates, my charts |

**Limits:**
- a cap on cells (50,000), with Top N enforced and the cap explained;
- results cached by (spec hash, viewer scope, data version from `mart.refresh_log`).

**Budgets** are those of [23](23-performance.md): headline ≤ 3 months < 500 ms, tables < 1 s, 12 months < 3 s.

## 10. Defaults for open questions (changeable later)

| Question | Default |
|---|---|
| ❓Q1 default KPIs | Ad spend · Ad revenue · ROAS · Orders · CTR · CPC ([22](22-access-and-dashboards.md) §4) |
| ❓Q7 metric names | as in [02](02-metric-dictionary.md) |
| ❓Q13 comparisons | previous period, previous year; no targets yet |
| ❓Q15 week start | Monday, configurable per chart; provisional = the report's restatement window |
| ❓Q17 export | CSV / XLSX of any chart's table view (phase 6) |

## 11. Tests

- **Correctness:**
  - A reference oracle runs ≥ 500 random specs over Zepto data, each against hand-written SQL on current `wh.fact_ad`.
  - Totals and subtotals equal headline totals.
  - A rate equals the ratio of sums in every cell.
  - A breakdown shows its remainder row.
  - NULL is never 0.
  - A grep test fails on any `COALESCE(…,0)` in analytics SQL.
  - Mart = facts after publish, retract and restatement.
- **Security:**
  - RBAC tests for every endpoint.
  - The reader role without `app.allowed_brands` sees 0 rows.
  - A shared dashboard shows a viewer only their brands.
  - Sales-only sees nothing; empty selection = no data.
- **Performance:** the budgets met on a throwaway 30-brand × 12-month database, with EXPLAIN recorded.
- **UX (Playwright):**
  - Build a chart from blank in under a minute.
  - Switch through every chart type with the spec intact.
  - Add, disable, reorder and remove filters, with impact shown.
  - A rolling period stays relative after reopening.
  - Save, duplicate, reset, undo.
  - Share to a manager.
  - The no-jargon scan; 390 px view-only; keyboard drag and drop.
