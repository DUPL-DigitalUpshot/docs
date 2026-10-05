# Unified Ads reporting DB (Stage B): review set

Status: **draft v2, reviewed 2026-10-02 against real files and Stage A code.** Nothing here is built. No code or tables exist yet.
This implements PRD §10 B1–B4 for **Ads**. Sales follows later on the same pattern, reusing the domain-agnostic `ingest` schema.

**Gate.** PRD:282 starts Stage B only after the step-7 sign-off. Before that, only working-flow item 2.4 (the unified format for Zepto) may run in parallel. This round therefore covers **phases 0–2** of [30-delivery-phases.md](30-delivery-phases.md): correct the design, fix the Stage A prerequisites, and build the ingest core for Zepto. Phases 3–6 wait for the gate.

## What we are building

Today Stage A downloads and keeps each platform's reports, but every platform names its columns differently and cuts its data differently. Stage B maps every column to one canonical name and stores only independent numbers (spend, impressions, clicks, revenue, units, orders, add-to-cart), so ROAS, CTR, CPC and the rest are computed correctly at any level. On top of that it serves brand dashboards that can show one brand or several, and one platform or several. Users pick their charts and filters, and every number links back to the untouched original file.

## What the review changed (2026-10-02)

The architecture stood. Several detailed rules broke on real data, and Stage A bugs would have loaded wrong numbers with nothing to detect them. The fixes (review findings D1–D12; the decisions in the next section keep their own numbers):

| # | Was | Now | Where |
|---|---|---|---|
| D1 | duplicate natural key inside a file → quarantine | declared grain per report; duplicate rows are **summed** to it; granular keeps a surrogate row key | [04](04-grain-and-double-counting.md) §4, [21](21-validation-and-originals.md) §3 |
| D2 | row-level supersede on a unique natural key with nullable columns | **slice-level** versioning with a content hash | [04](04-grain-and-double-counting.md) §5, [20](20-schema.md) |
| D3 | Instamart granular covers 37% | that file was truncated; granular = `auto_date` is a hard check | [04](04-grain-and-double-counting.md) §2, [21](21-validation-and-originals.md) §3 |
| D4 | restatement window T-15, Blinkit "15/38 matched" | Blinkit and Instamart restate the trailing ~3 days (window 5 d), FK Minutes revenue for more than 7 days (14 d ⚠); Zepto is unmeasured (5 d ⚠); window per portal | [04](04-grain-and-double-counting.md) §5 |
| D5 | Blinkit headline unverified | Σ daily spend = served budget within ₹1 for 95% of campaigns; a hard check, Product Booster flagged | [21](21-validation-and-originals.md) §3 |
| D6 | split a multi-brand file by alias | facts land only on `report_files.brand_id`; a brand mismatch quarantines | [03](03-dimensions.md) |
| D7 | Zepto pulled one day at a time | one report-day takes 22–45 s and a daily pull of all 18 reports 10.9–12.1 min per brand, so the default is **every Zepto Ads report daily, split by day**; admin-controlled pull policy per report; long backfills are chunked to fit the 2 h run cap | [04](04-grain-and-double-counting.md) §3, [01](01-architecture.md) §3 |
| D8 | coverage tolerances held loads | only "must-equal" relations hold; coverage only flags | [21](21-validation-and-originals.md) §3 |
| D9 | one breakdown per platform prevents double counting | headline = an explicit set of (portal, report, sheet) in `wh.headline_sources` | [04](04-grain-and-double-counting.md) §1 |
| D10 | `SUM()` keeps NULL semantics | `wh.metric_availability`; the API returns coverage per metric | [20](20-schema.md), [22](22-access-and-dashboards.md) §2 |
| D11 | one mapping row per source column | a `weight` per row; several rows may feed one target | [20](20-schema.md) |
| D12 | `load_status` on `report_files` | separate `ingest.loads`; `report_files` gets no new columns | [01](01-architecture.md) §3, [20](20-schema.md) |

Stage A bugs A1–A6 (the Zepto report-centre collector filing some split-by-day files under the wrong day, one "SB city" file holding SP data from the same bug, Instamart period, no backups, originals not downloadable for Zepto, smaller gaps such as `storage.store` overwriting in place) are listed in [01-architecture.md](01-architecture.md) §5 and fixed in phase 1.

## Decisions already taken

| # | Decision |
|---|---|
| D1 | Built in this repo (UniQCAI) |
| D2 | Warehouse = **Postgres**: the existing instance, new schemas `ingest`, `stage`, `wh`, `mart` (and `app` for saved views). This supersedes DECISIONS 2026-09-21 L8 ("PostgreSQL is the app DB only"); owner approved 2026-10-02 |
| D3 | v1 = **Ads only** |
| D4 | Access = existing roles + per-brand grants (manager / executive, category-limited). Admins own the mappings |
| D5 | Multiple brands: agency staff see their granted brands; a client owning several brands sees only those. No organisation entity |
| D6 | ~~Dashboards are picked from a chart catalogue. No free pivot builder in v1~~ **Superseded 2026-10-03 (owner):** a free, no-code dashboard builder ([24](24-analytics-builder.md)); correctness is enforced by the server, not by limiting choices. Dashboards can be shared; each viewer sees them through their own grants |
| D7 | Originals are kept untouched, for ever, and always downloadable (`?original=true`). Periods come from `report_files`; for day-grain files the date column picks the day inside that period ([03](03-dimensions.md)) |
| D8 | What feeds the warehouse is an admin setting per report (`ingest.report_policies`), with its cost shown |

## Reading order

| File | What it answers |
|---|---|
| [01-architecture.md](01-architecture.md) | the layers, the ingest runtime, load states, what Stage A gives us, Stage A bugs to fix first |
| [02-metric-dictionary.md](02-metric-dictionary.md) | the canonical names: stored, extension, reported, derived |
| [03-dimensions.md](03-dimensions.md) | what you can slice and filter by; the date and brand rules |
| [04-grain-and-double-counting.md](04-grain-and-double-counting.md) | headline sources, partial reports, day vs range, grain, slice versioning, restatements |
| [10-mapping-zepto.md](10-mapping-zepto.md) | Zepto: every column → canonical |
| [11-mapping-blinkit.md](11-mapping-blinkit.md) | Blinkit |
| [12-mapping-instamart.md](12-mapping-instamart.md) | Instamart |
| [13-mapping-fk-minutes.md](13-mapping-fk-minutes.md) | Flipkart Minutes |
| [14-mapping-flipkart-marketplace-ads.md](14-mapping-flipkart-marketplace-ads.md) | Flipkart marketplace ads (no UniQCAI portal yet) |
| [15-mapping-bigbasket.md](15-mapping-bigbasket.md) | BigBasket (on hold) |
| [16-cross-platform-matrix.md](16-cross-platform-matrix.md) | **one-page view**: canonical field × platform |
| [20-schema.md](20-schema.md) | tables, keys, partitions, indexes |
| [21-validation-and-originals.md](21-validation-and-originals.md) | hard and soft checks, and the "Source files" link to originals |
| [22-access-and-dashboards.md](22-access-and-dashboards.md) | roles, metrics API, chart catalogue, admin screens, saved views |
| [23-performance.md](23-performance.md) | speed targets, data sizes, how we stay fast |
| [30-delivery-phases.md](30-delivery-phases.md) | phases 0–6, exit checks, required tests |
| [40-domain-expert-questions.md](40-domain-expert-questions.md) | **send this one** to the marketing expert |

## How to review the mapping files

Each mapping cell carries a marker:
- ✅ **verified**: checked on real rows, with the check quoted.
- ⚠ **assumed**: a reasonable reading that nobody has confirmed.
- ❓ **Qn**: blocked on question *n* in file 40.

| Platform | Evidence |
|---|---|
| Zepto, Blinkit, Instamart | existing verified docs in `docs/research/`, re-checked on 2026-10-02 against every original in the storage volume |
| FK Minutes, Flipkart marketplace, BigBasket | checked on 2026-10-01 against real downloads in the digitalUpshot workspace; the results are quoted in each file |

## Open items for the owner (not domain questions)

Question numbers below are of two kinds. "PRD Q*n*" is PRD §12. A bare "Q*n*" is file 40.

| # | Item | Why it matters |
|---|---|---|
| P1 | Should **Flipkart marketplace ads** (digitalUpshot `fk-ecommerce/`, a different business on the same login) get a UniQCAI portal? | today `flipkart.sellerhub` is a Sales portal with inactive reports, so these ads have nowhere to land |
| P2 | Should the Blinkit **dashboard export** (`Report_*.xlsx`: Product Listing, Recommendation, Banner) join the catalogue? PRD FR-20 names it; the adapter only has `mtd_search_report` | banner ads and the daily dashboard view are missing otherwise |
| P3 | Range-only breakdowns (Instamart city and product, FK fsn and placement…) | settled by P6: each report's cadence is an admin setting. Defaults: Zepto, every report daily, split by day; Instamart and FK Minutes breakdowns, weekly tiles. Weekly tiles stay an option for any report |
| P4 | Amend UniQCAI CLAUDE.md "Scope right now" ("no Stage B tables") and rule 6 | **approved 2026-10-02** for phases 0–2 |
| P5 | Who signs off phase 0 | per **PRD Q10** (PRD §12: who approves the Zepto gate), not file 40's Q10 |
| P6 | Pull policy is **admin-controlled per report** (`ingest.report_policies`: feed on/off, cadence, split by day, restatement window), shown with its cost | **approved 2026-10-02**, with the defaults in [04](04-grain-and-double-counting.md) §3 |
