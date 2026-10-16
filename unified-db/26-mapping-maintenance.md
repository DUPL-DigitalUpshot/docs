# 26 · Maintaining column mappings (admin-maintained, versioned)

**Status: designed 2026-10-15, not built.** It is part of the phase-5 "mapping screen" ([22](22-access-and-dashboards.md) §7, [30](30-delivery-phases.md)). Owner decisions: admins draft, super admins activate; record the design now, build later (DECISIONS 2026-10-15).

**Why.** Platforms rename report columns without notice, and every platform adds its own. When a column changes, an admin should fix it from the UI by pointing the new column at one of our existing fields. It should not take a developer, a YAML edit and hand-written SQL.

## 1. What exists today

| Piece | Where | State |
|---|---|---|
| Mapping versions (draft / active / retired; one active per portal × report × sheet) | `ingest.mapping_versions`, migration `0012_unified_ads_store.py:190-208`; model `backend/app/modules/warehouse/models.py:91` | built |
| Column rows (source → role, target, transform, weight, status, evidence) | `ingest.column_mappings`, `0012:212-227`; model `models.py:130` | built |
| Loads read the **database**, not the YAML | `Mapping.from_db` `backend/ingest/mapping.py:133`; `active_mappings()` `backend/ingest/loader.py:137` | built |
| Each fact records its version | `wh.fact_ad.mapping_version_id` (`0012:477`); loads keep `mapping_version_ids` and `mapping_set_hash` | built |
| A newly active version reloads the report's files | scheduler sweep → `loader.sweep` (`loader.py:779-821`, every 10 min); restatement cause `remap` (`backend/ingest/publish.py:510`) | built |
| A renamed column holds the load | hard `header` check with `unmapped` / `missing` / `duplicated` names (`backend/ingest/checks.py:141-171`) | built |
| The only writer of mappings | `make seed-mappings [apply=1]` → `backend/app/cli/seed_mappings.py` (v1 active; later changes become drafts) | built |
| View / edit / preview / activate / roll back | — | **missing** |
| Showing which columns changed | the names are kept in `ingest.checks.detail`, but the UI says only "Columns changed" (`frontend/src/lib/words.ts:343`) and suggests "Re-pull" (`publish.py:110`) | **missing** |
| Activating a draft | no API, no CLI; only hand-written SQL | **missing** |

**Two defects block a rename even with a screen:**
1. **One source name per column.**
   - Loadable metrics are required (`mapping.py:83-86`).
   - A version that maps the **new** name therefore fails every **older** file when the sweep reloads it.
   - A version that maps the **old** name fails every new file.
2. **The seeder reverts UI edits.** It drafts whenever the YAML differs from the database (`seed_mappings.py:145-154`).

## 2. Design

### 2.1 The database is the source of truth
- **The seeder only creates:** after the first seed of a portal × report × sheet, the database owns the mapping. `seed_mappings` creates mappings for keys that have none and **never drafts over an existing one**.
- **YAML becomes an export:** a new `make export-mappings` writes every active version back to `backend/ingest/mappings/**/*.yaml`, so a change made in the UI still reaches git for review. The YAML stops being the place to edit.

### 2.2 Renames are aliases
- **New column:** `ingest.column_mappings.source_aliases text[] NOT NULL DEFAULT '{}'` (new migration; [20](20-schema.md)).
- **Presence:** a column is present when its `source_column` **or any alias** appears in the header. This applies to `header_coverage` / `require_coverage` (`mapping.py:263-292`) and to the cell lookup in `map_table` (`backend/ingest/canonical.py`).
- **Example:** "Zepto renamed `Spend` to `Spends`" becomes *add `Spends` as an alias of `Spend`*. Old and new files load under one version, and history never breaks.
- **Duplicates:** two names of one column in the same file count as `duplicated`, and the load is held.
- **Why not one version per file date:** aliases are simpler to explain and survive back-and-forth renames.

### 2.3 What admins may choose (targets stay code-defined)
- **A picker, not free text:**
  - metrics from `BASE_METRICS` (`backend/ingest/metrics.py:14`), each a column of `wh.fact_ad`
  - dimensions from `_HOMES` (`canonical.py:98`)
  - roles and transforms from `metrics.py`
  - plain-language labels from `wh.metric_definitions`
- **Free keys only where they're safe:** `reported`, `ext` and `validator` targets (stored in jsonb).
- **A new canonical metric stays a developer change:** a fact column, a migration and [02](02-metric-dictionary.md). This is the guardrail that keeps cross-platform numbers comparable.

### 2.4 The flow
1. **A header hold names the problem.** Needs attention and the import drawer list the unmapped and missing columns from the `header` check, with a **suggested match** (closest missing column by name: "`Spends` looks like `Spend`"). The hint becomes **Map the new column**, not Re-pull.
2. **Draft (admin).** Start from the active version and edit: add an alias, change target / role / transform, mark a column *ignore*, or add a new column. The draft is saved as `status = 'draft'`.
3. **Preview (admin).**
   - An in-memory dry run of the draft on the held file(s): read the file → `map_table` → `file_checks`.
   - It shows checks, row counts and totals before vs after. Nothing is written.
   - The Blinkit research ran the same way ([blinkit-ads-unified-format.md](../research/blinkit-ads-unified-format.md)).
4. **Activate (super admin).** In one transaction:
   - re-run the mapping validation (`mapping.py:215-246`) and the seeder rules: no metric from an `unknown` column; the declared grain present
   - retire the active version and activate the draft (the partial unique index allows one active)
   - set `activated_by` / `activated_at`
   - write an audit row
5. **Reload (automatic).** The sweep re-queues the report's files under the new mapping set. Held loads re-run, and changed days are recorded as restatements with cause `remap`.
6. **Roll back (super admin).** Re-activate a retired version through the same path.

### 2.5 Roles
| Action | Admin | Super admin |
|---|---|---|
| View mappings, versions, header problems | ✓ | ✓ |
| Create or edit a draft; preview it | ✓ | ✓ |
| Activate a draft; roll back | — (sees "Waiting for a super admin") | ✓ (`RequireSuperAdmin`, `backend/app/core/rbac.py:92`) |

Every endpoint gets a test in `backend/tests/rbac/`. Every activation and roll-back writes `audit.record` (`backend/app/modules/audit/service.py:50`).

### 2.6 API sketch (`/warehouse/mappings`)
| Method · path | Purpose |
|---|---|
| `GET /warehouse/mappings` | per platform → report → sheet: active version, pending draft, last header problem |
| `GET /warehouse/mappings/{portal}/{report}/{sheet}` | versions with columns; draft vs active diff |
| `POST …/drafts` | create a draft from the active version plus edits |
| `PATCH …/drafts/{id}` | edit a draft |
| `POST …/drafts/{id}/preview` | dry run on the held file(s) or a chosen stored file; no writes |
| `POST …/drafts/{id}/activate` | super admin; validate, retire and activate, audit |
| `POST …/versions/{id}/rollback` | super admin; re-activate a retired version |

### 2.7 The screen
[UI_PLAN](../UI_PLAN.md) §3.18 **Mappings** (`/data/mappings`).

### 2.8 Later, the same pattern
`wh.brand_aliases`, `wh.dim_ad_product` (house groups) and `wh.dim_city.aliases` are promised as admin data with an audit trail ([03](03-dimensions.md)), but nothing writes them today. They get the same draft / preview / activate treatment, on the same screen family.

## 3. Build order (when approved)
1. **Migration and core logic:**
   - `source_aliases`, plus alias-aware coverage and lookups
   - the seeder becomes create-only; add `make export-mappings`
   - unit tests: a renamed column loads both old and new files; a duplicate alias is held
2. **Show the problem:** render the header-check names in Needs attention and the import drawer, and replace the Re-pull hint.
3. **API:** read, draft, preview, activate and roll-back endpoints, with audit and RBAC tests.
4. **Screen:** UI_PLAN §3.18 and `frontend/src/features/data/MappingsPage.tsx`; then `make types`, lint, tests.

## 4. Verification (when built)
- **Unit:**
  - a rename via an alias loads both files
  - activation refuses an `unknown` metric
  - activation retires the previous version atomically
  - roll-back works
- **Integration:**
  - rename a header in an in-memory **copy** of a stored file (never the original; CLAUDE.md rule 6) → preview → activate an alias on a real held load
  - the sweep reloads, the load publishes, and the restatement cause is `remap`
- **UI:** header problem → suggested match → preview → activate (as super admin) → load published, end to end in the browser.
