# 20 · Database schema (Postgres 16)

Every table below arrives through an Alembic migration (CLAUDE.md rule 5). Names are proposals for review.

| Schema | Holds | Built in |
|---|---|---|
| `ingest` | mappings, loads, slices, checks, pull policies. Domain-agnostic, so Sales reuses it | phase 2 |
| `stage` | parsed source rows, rebuildable from raw | phase 2 |
| `wh` | Ads facts, dimensions, alias maps, restatements | phase 2 |
| `mart` | dashboard tables | phase 4 |
| `app` | saved views and personal dashboards | phase 5 |

`sheet` is `NOT NULL DEFAULT ''` everywhere it is part of a key. Postgres treats NULLs as distinct in a unique index, so a nullable key column would let duplicates through (see "Why not a row natural key" below).

## ingest — mappings

```sql
ingest.mapping_versions (
  id               bigserial PK,
  portal_key       text NOT NULL,
  report_key       text NOT NULL,
  sheet            text NOT NULL DEFAULT '',      -- Blinkit and BigBasket workbooks
  version          int  NOT NULL,
  grain            text[] NOT NULL,              -- declared grain: target keys that make a row;
                                                 -- '{}' = keep every source row (Instamart granular)
  status           text NOT NULL CHECK (status IN ('draft','active','retired')),
  notes            text,
  activated_at     timestamptz, activated_by int REFERENCES users(id),
  UNIQUE (portal_key, report_key, sheet, version)
)
-- one active version per (portal, report, sheet):
UNIQUE (portal_key, report_key, sheet) WHERE status = 'active'

ingest.column_mappings (
  id                 bigserial PK,
  mapping_version_id bigint NOT NULL REFERENCES ingest.mapping_versions(id),
  source_column      text NOT NULL,              -- exact header text, trimmed
  role               text NOT NULL CHECK (role IN
                       ('metric','ext','reported','dimension','date','brand','validator','ignore')),
                                                 -- 'metric' = Kind base in 02 §1
  target_key         text NOT NULL DEFAULT '',   -- '' only for role = ignore
  weight             numeric NOT NULL DEFAULT 1, -- +1 / −1: "Direct + Indirect", BigBasket revenue − other
  transform          text,                       -- pct_string | na_null | strip_prefix:<p> | date:<fmt> | text_number …
  status             text NOT NULL CHECK (status IN ('verified','assumed','unknown')),
  evidence           text,                       -- doc + check, e.g. "ROI=(D+I)/spend 186/186"
  question_ref       text,                       -- e.g. "Q3"
  UNIQUE (mapping_version_id, source_column, target_key)
)
```

Rules:
- **Every header must be mapped or explicitly ignored**, or the load holds. A new header stops the load and is listed on the admin mapping screen.
- **Several rows may feed one target, and one column may feed several targets.** A target's value is Σ (weight × transformed source value). If any source value is NULL, the target is NULL (NULL ≠ 0).
- `status = unknown` is allowed for `reported`, `validator` or `ignore` roles. It is never allowed for a `metric` role.
- Mappings are data, so admins can edit them and they are versioned (PRD B1). They are seeded from reviewed YAML in `backend/ingest/mappings/<portal>/<report>[.<sheet>].yaml`, generated from files 10–13 and tested against fixtures.
- **Format readers are code**, one per platform (`backend/ingest/formats/<platform>.py`): preamble detection by content, sheets, `NA` → NULL, `%`, enum prefixes, text numbers and the three date formats. They know no URLs or selectors (CLAUDE.md rule 3) and never import Playwright.

## ingest — loads, slices, checks, policies

```sql
ingest.loads (
  id                 bigserial PK,
  report_file_id     int  NOT NULL REFERENCES report_files(id) ON DELETE RESTRICT,
  parser_version     text NOT NULL,
  mapping_set_hash   text NOT NULL,              -- hash of the active mapping version ids used
  mapping_version_ids bigint[] NOT NULL,
  status             text NOT NULL CHECK (status IN ('queued','skipped_duplicate','parsed','mapped',
                       'validated','approved','published','quarantined')),
  quarantine_reason  text,                       -- the failing hard check_key (header, row_count,
                                                 -- control_total, formula, brand, date_in_period,
                                                 -- must_equal:<rule>) or parser_error
  repull_suggestion  text,                       -- e.g. "re-pull Instamart granular for 1–7 Sep"
  slice_summary      jsonb,                      -- per slice: key, content_hash, rows, outcome
                                                 -- (new | unchanged | restated | stale)
  rows_parsed int, rows_facts int,
  queued_at timestamptz NOT NULL, started_at timestamptz, finished_at timestamptz,
  approved_by int REFERENCES users(id), approved_at timestamptz, published_at timestamptz,
  UNIQUE (report_file_id, parser_version, mapping_set_hash)   -- idempotency key
)

ingest.slices (
  id                 bigserial PK,
  brand_id           int  NOT NULL REFERENCES brands(id),
  portal_key         text NOT NULL,
  report_key         text NOT NULL,
  sheet              text NOT NULL DEFAULT '',
  period_start       date NOT NULL,
  period_end         date NOT NULL,              -- = period_start for a day slice
  current_load_id    bigint NULL REFERENCES ingest.loads(id),  -- NULL until a load publishes it;
                                                 -- the row exists from map time so facts can carry slice_id
  content_hash       text NULL,                  -- of the current version, over its canonical rows
                                                 -- sorted by row_key
  first_observed_at  timestamptz NULL,
  last_observed_at   timestamptz NULL,
  restated_count     int NOT NULL DEFAULT 0,
  UNIQUE (brand_id, portal_key, report_key, sheet, period_start, period_end)
)

ingest.checks (
  id          bigserial PK,
  load_id     bigint NOT NULL REFERENCES ingest.loads(id),
  check_key   text NOT NULL,                     -- names in 21-validation-and-originals.md §3
  severity    text NOT NULL CHECK (severity IN ('hard','soft')),
  passed      bool NOT NULL,
  expected    numeric, observed numeric,
  detail      jsonb,                             -- aggregates only, never client rows
  at          timestamptz NOT NULL
)

ingest.report_policies (
  portal_key               text NOT NULL,
  report_key               text NOT NULL,
  feed_warehouse           bool NOT NULL DEFAULT false,  -- off: still downloaded and stored, no load
  restatement_window_days  int  NOT NULL DEFAULT 5,       -- seeded per portal: blinkit 5, instamart 5,
                                                         -- fkminutes 14, zepto 14 (orders grow > 7 days)
  reconcile_weekly         bool NOT NULL DEFAULT false,  -- the weekly range pull for tiling is wanted
  updated_by               int REFERENCES users(id),
  updated_at               timestamptz NOT NULL,
  PRIMARY KEY (portal_key, report_key)
)
```

Notes:
- Each change to `report_policies` also writes a row to the existing audit log. The cost shown on the "Warehouse feeds" screen is computed from measured `run_tasks` durations, not stored.
- **No cadence here** (DECISIONS 2026-10-02, "Warehouse feeds ride on the existing Schedules"): what is pulled and when is the Schedules' job. The recommended pull pattern ([04](04-grain-and-double-counting.md) §3) is offered on the Feeds screen as "create the recommended schedule". **Seeded:** every Zepto Ads report `feed_warehouse = true`, `reconcile_weekly = true`, window 14 (0013); other portals off until their ingest ships.
- **Facts are written at map time** to `wh.fact_ad`, with the load's `load_id` and `slice_id`, for every new or changed slice; an unchanged slice writes none. Publish only moves pointers and sets `superseded_at` ([04](04-grain-and-double-counting.md) §5). It never rebuilds rows from `stage.parsed_rows`, whose 90-day retention is therefore not load-bearing.
- A load is claimed with `SELECT … FOR UPDATE SKIP LOCKED` ([01-architecture.md](01-architecture.md) §2).

## stage

```sql
stage.parsed_rows (
  load_id         bigint NOT NULL REFERENCES ingest.loads(id),
  report_file_id  int    NOT NULL,
  sheet           text   NOT NULL DEFAULT '',
  row_no          int    NOT NULL,
  raw_row_json    jsonb  NOT NULL,      -- every column, original header text as the key
  loaded_at       timestamptz NOT NULL,
  PRIMARY KEY (load_id, sheet, row_no, loaded_at)
) PARTITION BY RANGE (loaded_at);       -- monthly, by load month
```

Kept so the original values, platform ratios included, stay queryable without re-opening the file. **Retention is 90 days**: older partitions are dropped, because they are rebuildable from raw.

## wh — registry

```sql
wh.metric_definitions (key PK, display_name, unit, kind base|ext|reported|derived,
                       formula text, additive bool, platform_key NULL, active bool)

wh.headline_sources   (portal_key, report_key, sheet NOT NULL DEFAULT '', platform_key,
                       active bool, notes,
                       PRIMARY KEY (portal_key, report_key, sheet))
                       -- the explicit set totals read (04 §1)

wh.reconciliation_rules (id PK, portal_key, report_key, sheet, ad_product, against_report,
                         metric, kind must_equal|coverage|range_tiling,   -- range_tiling: Σ day slices = range (0013)
                         tolerance_abs numeric NULL,      -- ₹, for must_equal
                         expected_coverage numeric NULL,  -- informational, for coverage
                         per_day bool)                    -- compare on each actual date

wh.brand_aliases      (portal_key, raw_value, brand_id → brands, created_by, created_at,
                       PRIMARY KEY (portal_key, raw_value))

wh.metric_availability  -- VIEW over the active mappings of wh.headline_sources:
                        -- (platform_key, portal_key, report_key, sheet, metric_key, available bool)
```

Notes:
- `wh.metric_availability` is what the API uses to report `coverage` per metric. Clicks, and so CTR and CPC, are missing at headline for Blinkit, FK Minutes and BigBasket.
- `wh.brand_aliases` maps one raw value on one portal to **one** brand, and is a check, never a router ([03-dimensions.md](03-dimensions.md), the brand rule). Blinkit's `Manufacturer` can name a company that owns several of our brands; how such a file should be treated is open (❓Q21). In v1 its facts land on the connection's brand, `report_files.brand_id`.

## wh — dimensions

```sql
wh.dim_campaign  (id PK, portal_key, platform_id NULL, name, brand_id, ad_product,
                  campaign_type, status, pacing, first_seen, last_seen)
                  UNIQUE (portal_key, platform_id) WHERE platform_id IS NOT NULL
                  UNIQUE (portal_key, brand_id, ad_product, name) WHERE platform_id IS NULL
                                                  -- name-only rows (Zepto campaign report)
wh.dim_ad_group  (id PK, campaign_id → wh.dim_campaign, platform_id NULL, name, first_seen, last_seen)
                                                  -- FK search term has a name and no id
wh.dim_product   (id PK, portal_key, platform_product_id, name, ean NULL, category_l1, category_l2, brand_id)
wh.dim_city      (id PK, name, aliases text[])
wh.dim_placement (id PK, portal_key, raw_value, name)
wh.dim_ad_product(portal_key, raw_value, house_group)
```

## wh — the fact table

```sql
wh.fact_ad (
  id               bigserial,
  load_id          bigint NOT NULL REFERENCES ingest.loads(id) ON DELETE RESTRICT,
  slice_id         bigint NOT NULL REFERENCES ingest.slices(id),
  report_file_id   int    NOT NULL REFERENCES report_files(id) ON DELETE RESTRICT,
  row_key          text   NOT NULL,     -- declared grain values, or the source row number (granular)
  date             date,                 -- NULL for range rows
  period_start     date NOT NULL,
  period_end       date NOT NULL,
  grain            text NOT NULL CHECK (grain IN ('day','range')),
  brand_id         int  NOT NULL,        -- always report_files.brand_id
  platform_key     text NOT NULL,
  portal_key       text NOT NULL,
  report_key       text NOT NULL,
  sheet            text NOT NULL DEFAULT '',
  ad_product       text NOT NULL DEFAULT 'all',   -- 'all' when the report has no ad-type split
  campaign_id      bigint NULL REFERENCES wh.dim_campaign(id),
  ad_group_id      bigint NULL REFERENCES wh.dim_ad_group(id),
  breakdown        text NOT NULL,
  breakdown_key    text NOT NULL DEFAULT '',
  match_type       text NOT NULL DEFAULT '',     -- exact | phrase | broad | auto; keyword grain only
  -- base metrics: NULL = not reported, 0 = reported zero
  impressions numeric(18,0), clicks numeric(18,0), spend numeric(14,2),
  atc numeric(18,0), atc_direct numeric(18,0),
  revenue numeric(14,2), revenue_direct numeric(14,2),
  orders numeric(18,0), orders_direct numeric(18,0),
  units numeric(18,0), units_direct numeric(18,0), ntb_users numeric(18,0),
  ext              jsonb NOT NULL DEFAULT '{}',   -- platform extension metrics (additive)
  reported         jsonb NOT NULL DEFAULT '{}',   -- never summed
  parser_version   text NOT NULL,
  mapping_version_id bigint NOT NULL,
  observed_at      timestamptz NOT NULL,          -- report_files.extracted_at
  superseded_at    timestamptz NULL,
  PRIMARY KEY (id, period_start)
) PARTITION BY RANGE (period_start);              -- monthly partitions
```

Indexes:
- `UNIQUE (load_id, row_key, period_start)`. This is `UNIQUE (load_id, row_key)`; Postgres requires the partition key in every unique index of a partitioned table, and `row_key` already fixes the period.
- `btree (brand_id, platform_key, report_key, period_start) WHERE superseded_at IS NULL`: candidate current rows.

**What "current" means.** A fact is current only when its slice's `current_load_id` = its `load_id` **and** its `superseded_at` IS NULL. `superseded_at IS NULL` alone also matches facts of loads that are mapped but not yet published, or quarantined, so every read of current facts joins `ingest.slices` on that condition. Marts are built from current facts only. A quarantined load's facts are never current and may be purged; superseded facts are kept, with their `superseded_at`.
- `btree (slice_id) WHERE superseded_at IS NULL`: supersede a slice in one statement.
- `BRIN (period_start)` on each partition.
- `btree (report_file_id)` and `btree (load_id)` for lineage and the "Source files" link.

**Why not a row natural key.** The first draft had a partial unique index on (platform, portal, report, ad_product, brand, campaign, breakdown, breakdown_key, period) `WHERE superseded_at IS NULL`. It fails three ways:
1. `campaign_id` is nullable, and Postgres treats NULLs as distinct. City and page rows with no campaign would never collide, so they would never be deduplicated.
2. Ad group was missing from the key, and the data has no row key anyway ([04](04-grain-and-double-counting.md) §4).
3. A daily Blinkit MTD pull would supersede each day about 15 times.

Versioning is therefore per **slice** ([04](04-grain-and-double-counting.md) §5): an unchanged slice writes no rows, a changed one supersedes all of its rows at once.

**Foreign keys to `report_files` use `ON DELETE RESTRICT`.** `report_files.brand_id` cascades from `brands`. Brands are archived, never deleted (`DELETE /brands/{id}` answers 409, `app/modules/brands/router.py:201`). If a brand row is ever deleted by hand, RESTRICT stops the cascade instead of silently dropping facts and their lineage.

## wh — restatements

```sql
wh.restatements (
  id                  bigserial PK,
  slice_id            bigint NOT NULL REFERENCES ingest.slices(id),
  old_load_id         bigint NOT NULL REFERENCES ingest.loads(id),
  new_load_id         bigint NOT NULL REFERENCES ingest.loads(id),
  old_report_file_id  int NOT NULL, new_report_file_id int NOT NULL,
  cause               text NOT NULL CHECK (cause IN ('platform','remap')),
  deltas              jsonb NOT NULL,   -- per row_key and metric: old, new
  at                  timestamptz NOT NULL
)
```

## mart — what dashboards read (phase 4)

```sql
mart.ad_daily           (date, brand_id, platform_key, ad_product,          <base metrics>, ext, file_ids int[], provisional bool)
mart.ad_daily_campaign  (date, brand_id, platform_key, ad_product, campaign_id, <base metrics>, file_ids int[])
mart.ad_daily_product   (date, brand_id, platform_key, product_id,           <base metrics>, file_ids int[])
mart.ad_period          (period_start, period_end, brand_id, platform_key, breakdown, breakdown_key, <base metrics>, file_ids)
                        -- range-grain rows, for exact-period questions only
mart.freshness          (brand_id, platform_key, data_through date, last_published_at)   -- PRD B4
mart.refresh_log        (id, triggered_by_load_id, brand_id, platform_key, date_from, date_to, rows, took_ms, at)
```

Rules:
- Marts hold **only current, published rows from `wh.headline_sources`**, except `ad_period` and the drill-down marts.
- A refresh rebuilds one (brand, platform, date range) with DELETE + INSERT in one transaction.
- Metric columns keep NULL semantics and are never filled with `COALESCE(...,0)`. `SUM()` drops NULLs silently, so a total over platforms where one does not report the metric is partial. The API checks `wh.metric_availability` and reports it in `coverage` ([22](22-access-and-dashboards.md) §2).

## app — per-user preferences (phase 5)

```sql
app.saved_views       (id PK, user_id → users, name, page, filter_state jsonb, is_default bool, created_at, updated_at)
app.dashboards        (id PK, owner_user_id → users, name, is_default bool, created_at, updated_at)
app.dashboard_widgets (id PK, dashboard_id → app.dashboards ON DELETE CASCADE, position int,
                       chart_key text,       -- from the server-side chart catalogue
                       metrics text[],       -- keys from wh.metric_definitions
                       dimension text, breakdown text, filters jsonb)
```

Brand ids in `filters` and `filter_state` are **re-intersected with the viewer's current grants on every query**. A brand whose grant was revoked simply disappears from the result. The response never says it existed.

## report_files — no new columns

`report_files` stays Stage A's immutable record. Ingest state lives in `ingest.loads` ([01-architecture.md](01-architecture.md) §3). The only change is in phase 1, created after the A1/A2 relabel migration. Existing rows satisfy it: 0 violations in 157 rows, 133 of them latest (2026-10-02).

```sql
CREATE UNIQUE INDEX report_files_one_latest
  ON report_files (brand_id, portal_key, report_key, period_start, period_end)
  NULLS NOT DISTINCT                     -- a NULL period must still collide
  WHERE is_latest;
```
