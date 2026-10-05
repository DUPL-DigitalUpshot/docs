# Dashboarding and reporting flow

Status: architecture and implementation review, 4 October 2026.

This document describes the implemented Ads analytics path from a downloaded
portal report to a dashboard figure, how that figure changes, and how each
user audience works with it. It also distinguishes the implemented dashboard
product from reporting and release work that is still outstanding.

## 1. Current assessment

The dashboarding architecture is implemented and verified on the isolated
`an-builder` / `ui-navigation` line. It is not yet merged into `unified-db` or
deployed with live brand data. The synthetic preview is not production
evidence.

Architecture score: **8.5/10**.

Strong areas:

- immutable originals and checksums;
- versioned publication and restatement history;
- authoritative, published-only headline marts;
- NULL-preserving sums and correctly paired ratios;
- viewer-scoped queries with a read-only database role and row-level security;
- dashboard ownership, sharing, optimistic locking and version history;
- transactional mart-refresh delivery with retry and stale-work recovery;
- historical file-shape and control-total anomaly warnings;
- open-dashboard polling, manual refresh and visible refresh-pending state;
- source-file provenance for figures.

Outstanding areas:

- release migration and live-data acceptance;
- operational queue-lag metrics and alerting;
- atomic publication visibility across direct-fact and mart-backed widgets;
- non-Zepto warehouse readers;
- generated exports and scheduled report distribution;
- an explicit author/viewer policy for managers and executives.

## 2. End-to-end flow

```text
Portal schedules
    |
    v
Original file stored unchanged
report_files: path, checksum, brand, platform and period
    |
    v
Parser queue, with a 10-minute recovery sweep
    |
    v
stage.parsed_rows
    |
    v
Mapping and validation
    |
    v
Warehouse dimensions + fact_ad + versioned slices
    |
    v
Validated
    +-- Admin approval during the initial trust period
    `-- Automatic approval after 14 clean published days
    |
    v
Published current-slice pointers + durable refresh outbox row
    |
    v
Post-commit kick + scheduler retry
    |
    v
ad_daily / ad_daily_campaign / ad_period / freshness
    |
    v
Analytics query engine
    |
    v
Redis cache keyed by query and mart data version
    |
    v
Dashboard widgets
```

### 2.1 Original storage

`report_files` is the immutable inventory of downloaded files. It records the
storage path, checksum, source identity, brand, period and extraction time.
Older versions remain available when a report is downloaded again. See
`backend/app/modules/runs/models.py`.

### 2.2 Parsing and canonical storage

Only a report with an enabled warehouse feed and active mapping is eligible.
The parser verifies the stored checksum, keeps parsed source rows in staging,
maps dimensions and metrics, and writes facts associated with a load and
slice. Facts do not become visible merely because they were written. See
`backend/ingest/loader.py`.

### 2.3 Validation and publication

File checks and cross-report checks run before publication. A hard failure
quarantines the load and can retract affected counterpart data. During the
trust period an admin approves a validated load. After 14 clean published
days, a feed can be approved automatically.

Duplicate rows at a mapping grain that forbids summing are a named hard
`duplicate_grain` failure. Once five comparable published loads exist, the
loader also compares each new file with up to 20 recent loads of the same
brand, portal, report and period length. An unexpectedly empty file, a row
count below 20% or above 500% of the median, or a spend/revenue/impression/
click/order total outside that range is recorded as a soft review warning.
These historical checks flag unusual business movement without automatically
discarding potentially legitimate data.

Publication moves each slice's `current_load_id`. A changed file creates a
restatement; older facts and source evidence remain stored. Retraction points
the slice back to the previous valid load or to no current load. See
`backend/ingest/publish.py`.

### 2.4 Mart refresh

Moving a current headline slice writes or widens an
`ingest.mart_refresh_outbox` row in the same transaction. A post-commit broker
message starts it quickly. The scheduler dispatches pending, failed and stale
work every minute, while the daily reconcile remains an independent drift
repair. The worker rebuilds only the affected brand, platform and date range,
then completes the outbox row in the same transaction as the mart refresh. A
fact enters a mart only when:

- its load is published;
- its slice points to that load as current;
- it is not superseded; and
- its report/sheet is an active headline source.

Each successful refresh updates `mart.freshness`, allocates a new data version
and writes `mart.refresh_log`. Advisory locks serialize refreshes of the same
brand/platform pair. See `backend/app/modules/analytics/marts.py`.

### 2.5 Query execution

The analytics service intersects requested brands with the viewer's Ads
grants. It then opens a read-only transaction as `uniqcai_reader`, sets the
allowed brand IDs locally, and relies on forced PostgreSQL row-level security
as a second boundary.

Headline queries use marts and may be cached in Redis for five minutes. The
cache key includes the mart data version, so a completed refresh causes a new
query key immediately. Breakdown and extended-metric queries read current
warehouse facts directly and are not cached. See
`backend/app/modules/analytics/service.py` and
`backend/app/modules/analytics/reader.py`.

### 2.6 Dashboard persistence

A dashboard stores definitions, not result snapshots:

- name and description;
- dashboard filters;
- grid layout;
- chart presentation options; and
- one query specification per widget.

Opening a dashboard runs each widget under the current viewer's grants. A
share therefore grants access to the dashboard definition but never expands
data access. Saves use optimistic locking and retain the latest 20 versions.
See `backend/app/modules/dashboards/models.py` and
`backend/app/modules/dashboards/service.py`.

## 3. How figures update

1. A new or corrected portal report is downloaded and stored.
2. The parser validates and maps it into warehouse facts.
3. Approval publishes it by moving the relevant current-slice pointers.
4. Publication commits a scoped refresh-outbox row and sends a post-commit
   broker kick.
5. The worker rebuilds affected mart rows and increments the data version.
6. The next widget query uses the new data version and cannot reuse the old
   cache key.
7. Open widgets poll every 30 seconds; users can also refresh the dashboard
   immediately.
8. While work is incomplete the UI says `Updating data`, and its Data details
   names the affected platform and pending time.

This path remains eventually consistent because publication and mart refresh
are separate transactions. It no longer depends on broker delivery for
correctness: the database row is the record of work, failed work backs off and
retries, stale dispatched/processing rows become eligible again, and daily
reconciliation is a second repair path. Pending work is also part of the query
cache identity, so the UI cannot silently reuse a pre-publication cached answer
after publication.

There is also a short consistency window in which breakdown or extended
queries can see newly current facts while a headline KPI still reads the old
mart version.

## 4. Figure status vocabulary

| Status | Meaning |
|---|---|
| Data through | Latest published day for the selected brand/platform, including a valid published empty report |
| Partial | Some expected platform inputs or days are missing, or a derived ratio is available for only part of the selected scope |
| Provisional | The selected date is still inside the platform's expected restatement window |
| Restated | A figure in the selected period changed after it was first published |
| Not available | The selected platform does not supply the metric required by the chart |

These are figure-quality indicators, not workflow tags. Their detailed dates,
platforms and missing coverage belong in the chart's Data status details.

## 5. User and role model

`admin`, `super_admin`, `toggle_admin` and `member` are account roles.
`manager` and `executive` are per-brand grant levels. They are not currently
separate dashboard-authoring permissions.

| Persona | Implemented dashboard/reporting behaviour |
|---|---|
| Admin | Operates warehouse feeds and loads; approves, quarantines and retries data; queries all brands; builds and shares dashboards; publishes templates |
| Manager | Queries only granted brands/categories; builds and shares personal dashboards; edits a shared dashboard when `can_edit` is granted; cannot approve warehouse loads |
| Executive | Normally consumes templates, shared dashboards and saved views, but currently may also build dashboards and edit `can_edit` shares because any Ads grant qualifies |
| Member without Ads access | Cannot access the analytics catalogue, query engine or dashboard builder |
| Shared viewer | Sees the dashboard definition, but every widget silently drops brands outside the viewer's own grants |

Private dashboards remain private even from admins. Only the owner may share
or delete a dashboard. An editor may change its contents but cannot change its
audience. Admins may publish a dashboard they can see as a template.

## 6. Implemented dashboard capabilities

- global and brand-scoped dashboard routes;
- KPI, time-series, comparison, distribution and table visualisations;
- dashboard-level and chart-level filters;
- desktop grid editing and mobile view-only rendering;
- chart editor, My charts and reusable saved views;
- save-as, undo/redo/reset and dirty-navigation protection;
- optimistic conflict handling and version restore;
- person and brand/audience sharing;
- admin-published templates;
- full-screen data-table view;
- source-file provenance and original-file download;
- data-through, missing coverage, provisional and restated indicators;
- refresh-pending state, 30-second polling and manual dashboard refresh;
- hard duplicate-grain protection and soft historical anomaly warnings.

## 7. Reporting boundary

The current product is an interactive dashboarding system. It is not yet a
complete reporting/distribution system.

Not implemented:

- dashboard CSV or XLSX export;
- PDF report generation;
- scheduled email or link delivery;
- subscriptions and alert thresholds;
- frozen month-end report snapshots;
- delivery history, failure handling or recipient audit;
- report approval/certification workflow.

The existing source-file download is provenance for a chart value, not a
formatted business report.

## 8. Operational and product risks

### High priority

1. The feature line is not merged, migrated or deployed with live brand data.
2. Direct-fact and mart-backed widgets can briefly show different publication
   states.
3. Refresh queue age is visible to users but has no operational alert/SLA.
4. The warehouse loader currently has only a `zepto.ads` format reader.
5. Exported and scheduled reporting remains absent.

### Product decisions required

1. Decide whether executives are allowed to build and edit dashboards or are
   view-only consumers.
2. Decide whether managers may publish team dashboards or only owners/admins.
3. Define a freshness SLA per platform and what the UI shows when it is missed.
4. Define whether executive reports must be certified or frozen at month end.
5. Define export formats, delivery schedules, recipient controls and retention.

## 9. Path to 10/10

1. Merge into `unified-db`, back up the database, rehearse migrations and run a
   live Zepto acceptance check.
2. Add queue-lag metrics, an SLA and operational alerting; decide whether push
   invalidation should supplement the current 30-second polling.
3. Give direct-fact and mart-backed queries one publication snapshot boundary.
4. Add explicit dashboard capabilities such as viewer, author, publisher and
   data-operator instead of deriving all authoring rights from Ads access.
5. Implement CSV/XLSX/PDF generation, scheduled delivery and delivery history.
6. Activate and verify the remaining platform readers and headline mappings.
7. Add certified dashboard/report versions for executive and month-end use.
8. Run cold-cache, concurrent-load and production-cardinality benchmarks in
   the deployment environment.

## 10. Verification evidence

The recorded isolated A5/A6 verification includes:

- 2,301 backend tests passed, 16 skipped;
- 888 frontend tests passed across 76 files;
- 15 real-service browser workflows passed;
- all 16 chart encodings rendered;
- manager-only data and provenance checks;
- Sales-only access denial checks;
- frontend types, lint and production build passed.

This verifies the isolated implementation snapshot. It does not replace the
remaining merge, migration, live-data and deployment acceptance work. See
`docs/PROGRESS.md` for the evidence paths and later UI verification updates.

### Phase 1-3 hardening verification (4 October 2026)

- 2,321 backend tests passed, 16 skipped, against isolated PostgreSQL and
  Redis with migration 0019 applied from scratch.
- 897 frontend tests passed across 77 files; typecheck, lint and production
  build passed.
- Focused regressions cover lost broker messages, retries, atomic completion,
  RLS visibility, pending cache identity, duplicate grain and historical
  empty/row/metric anomalies.
- `make backup` created `backups/20261004T023148Z`; `make restore-check`
  restored its database into a throwaway database and verified all 170 stored
  files against their SHA-256 hashes.

## 11. Merge and release handoff

The integration branch is `ui-navigation`. At verification time `unified-db`
is its direct ancestor, so the merge is a fast-forward with no conflict or
uncommitted work. The final feature commits are intentionally ordered:

1. navigation scope and wording;
2. dashboard/editor usability and freshness UI;
3. migration 0019 plus backend consistency hardening; and
4. architecture decisions and verification evidence.

Migration history must remain unchanged: independent revisions 0016 and 0017
join at 0018, and 0019 follows 0018. Do not renumber or re-parent revisions.

Release remains separate from the merge. Take a fresh backup, prove its
restore, fast-forward `unified-db`, run `alembic upgrade head`, and only then
restart API, parser and scheduler processes that import the outbox model. Check
the migration-aware health endpoint, `make mart-status`, one live Zepto pull,
the Needs attention queue and an open dashboard's refresh transition. The
backup recorded above proves the mechanism, but it is not a substitute for a
new backup immediately before deployment.
