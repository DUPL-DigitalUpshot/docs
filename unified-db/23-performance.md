# 23 · Performance — how fast, and how big

## 1. Budget

| Question | Target (p95, server time) | UI behaviour |
|---|---|---|
| Up to 3 months, headline (tiles, trend, platform split) | **< 500 ms** | instant |
| Up to 3 months, campaign or product table | < 1 s | instant |
| 6–12 months, headline | **< 3 s** | "Loading a longer period…" with progress after 1 s |
| Keyword / search query / city drill-down, > 6 months | may exceed 3 s | run as a background job with a progress bar, and notify when ready |

## 2. Size estimate

The scale is 30 brands × 5 portals (PRD §8, "Scale").

**Raw files** are kept for ever ([21](21-validation-and-originals.md) §1). Measured on the stored originals, 2026-10-02:

| Report | Measured size |
|---|---|
| Zepto SP, one-day pull | ~7 KB per report (keyword 24–40 KB); ~70 KB for all six SP reports |
| Blinkit `mtd_search_report` | ~32 KB per day of data it holds, up to ~820 KB at month end. Each daily pull re-sends the month, so a month of daily pulls is ~10 MB |
| Instamart `auto_search_query` | ~10 MB per brand per month |
| Instamart `auto_granular` | ~47 MB per brand per month, the largest by far |
| FK Minutes, 31-day pull | 0.9–1.4 MB |

At 30 brands this is **≈ 20–25 GB of raw files a year**, most of it Instamart granular. `SYSTEM_DESIGN.md` §10 sizes the Stage A host at 100 GB of disk, so disk size is reviewed within the first year of Stage B. A storage interface with an S3/MinIO backend, behind the same `storage.py` API, is a later option, not a v1 need.

**Tables:**

| Table | Rows per year | Basis |
|---|---|---|
| `mart.ad_daily` | ~55 k | 30 × 5 × 365 × ~1 ad type |
| `mart.ad_daily_campaign` | ~2–5 M | ~20–50 active campaigns per brand-platform |
| `mart.ad_daily_product` | ~5–10 M | |
| `wh.fact_ad`, all breakdowns, current rows | ~50–150 M | dominated by search queries. Samples: Instamart search query 21,771 rows for 22 days on one brand; Flipkart search term 133,913 rows for 7 days |
| `wh.fact_ad` incl. superseded | **×~1.05** | slice versioning writes new rows only when a slice's content changes ([04](04-grain-and-double-counting.md) §5). An unchanged re-pull writes nothing; restatements touch only the trailing ~3 days. Row-level supersede would have been ×1.2–1.5, and Blinkit's daily MTD far more |
| `stage.parsed_rows` | ≈ 90 days of loads | partitioned by load month and dropped after 90 days, because it is rebuildable from raw |
| `ingest.slices` | ~1 per (brand, report, sheet, day) for day-grain reports; ~1 per range otherwise | small |

The dashboards' tables (`mart.ad_daily*`) stay at millions of rows at most. A year of headline data for every brand is ~55 k rows, so 3-month and 12-month headline queries are trivially fast with a (brand_id, date) index.

## 3. How we keep it fast

1. **Dashboards never read `wh.fact_ad` for headline numbers**, only the marts.
2. **Incremental mart refresh** after each publish, for just the (brand, platform, date range) that load changed, as DELETE + INSERT in one transaction. An unchanged slice changes nothing, so it triggers no refresh.
3. **`wh.fact_ad` is partitioned by month.** Queries prune to the months asked for. Each partition has a BRIN index on `period_start` and a partial btree on (brand_id, platform_key, report_key, period_start) for current rows.
4. **Search-query volume.** Keep it at range grain unless daily search terms are explicitly needed (❓Q10). It is the main driver of row count. The pull policy ([04](04-grain-and-double-counting.md) §3) already defaults the Instamart and FK Minutes breakdowns, where search queries live, to weekly.
5. **Parsing never slows the downloads.** The `parser` service has its own Dramatiq queue (`ingest`) and no browser ([01-architecture.md](01-architecture.md) §2).
6. **Repeated dashboard queries** can be cached in Redis (already running), keyed by (query, brand scope, last publish time). The cache is invalidated on publish. This is optional, and only added if the budget is missed.

## 4. When to revisit the database choice

Consider a column store (ClickHouse or similar) only if one of these holds for two consecutive weeks:
- p95 of headline queries is over 1 s;
- `wh.fact_ad` is over 200 M current rows;
- analysts need ad-hoc SQL over full history.

None of these is expected at 30 brands.

## 5. How it is measured (phase 4 exit)

1. Load the real originals into a **throwaway Postgres container**, never the live `uniqcai` database.
2. Multiply them synthetically to 30 brands × 12 months.
3. Time 1-, 3-, 6- and 12-month queries for each chart in the catalogue with `EXPLAIN (ANALYZE, BUFFERS)`.
4. Record the results in this file.
