# Instamart — port reference

> ⚠ **The engine code was never imported.** `legacy/instamart/download_reports.py`
> and `download_sales.py` are shims into an absent `src/upshot/…` tree (PRD §12
> Q13). So unlike every other platform, `legacy/instamart/docs/` — not the
> Python — is the source of truth. It is unusually good: captured against the
> live portal on 2026-08-21, and explicit that everything in it is *observed,
> not inferred*.

Portal key `instamart.brandportal` on `partner.instamart.in`. **One portal, one
login, one session serves both Ads and Sales.**

## Sign-in

`partner.instamart.in/login` → email → **OTP by mail** → dashboard. **There is
no portal password.** The OTP inbox is the same address as the login.

One login may carry several businesses, so this is a CLAUDE.md rule 9 portal:
verify the selected business against `connections.portal_brand_selector` and
raise `WRONG_ACCOUNT` on a mismatch.

**The side nav has no `<a href>`** — it is div/button based with router pushes.
**Navigate by URL, never by clicking nav text.**

## Ads — a report-centre queue, with a long wait

Route: `/instamart/reports`. Same two-phase shape as Zepto, but far slower:

1. Fill the filters, click **Generate Report**
2. The portal builds it — **5 to 10 minutes**
3. It appears in **Available Reports** with a Download button

**Retention is 7 days**, not 90 seconds. That changes the design: a collect pass
has a week-long window, so a run that times out waiting has not necessarily lost
the report. Worth modelling as a resumable collect rather than a tight poll.

### Report types — each with its own maximum span

| Type | Max span |
|---|---|
| Summary Report | **1 year** |
| Date × Campaign | 3 months |
| City × Campaign | 3 months |
| Placement × Campaign | 3 months |
| Product × Campaign | 3 months |
| Granular Report | **31 days** |
| Search Query × Campaign | **31 days** |

The cap is part of the option label. This is the third platform with real
per-report range caps (Zepto `OOS_VISIBILITY`, Blinkit `po`), so
`max_range_days` must be *enforced*, not merely stored.

Default selection is `Summary Report (Max 1 Year)`.

### The report name is the collection key

`#campaign-name-input` is auto-filled and **editable**, generated as:

```
IM_<TYPE>_<hhmm><AM|PM>_<ddmmyyyy>     e.g. IM_GRANULAR_0215PM_21082026
```

Since it can be written, it is the reliable handle for matching a finished row
back to the request that made it — better than timestamps, and the reason this
portal does not need Zepto's row-ownership heuristics.

### Five traps that each cost a run

All five failed *silently*: the field stayed empty, the portal said "End date is
required" in red, and nothing generated.

1. **Selecting a type can hit the table instead of the dropdown.** The Available
   Reports table has its own Report Type column, so a whole-page text search for
   "Granular Report" matches a **table cell** first, and clicking it does
   nothing. The symptom only appears on the *second* report of a run, because
   the first works by default. Exclude `table` and `[data-testid^="row-"]`
   descendants.
2. **The date-picker test id is not unique.** Once open,
   `data-testid="date-picker-start-date"` resolves to **three** elements and
   `get_by_test_id` goes strict-mode ambiguous. Address the trigger by `#id`
   (`#date-picker-start-date button`) and the calendar body by the nested
   `[class*="_dateRoot_"]`.
3. **The end picker's popup carries the *start* picker's test id** — apparently
   a copy-paste bug in the portal. A selector scoped to `date-picker-end-date`
   finds the end calendar **never**. Locate the open calendar by
   `[class*="_dateRoot_"]` alone; only one is ever open.
4. **An open picker blocks the next click.** It leaves a modal overlay that
   swallows pointer events, so clicking the end trigger while the start calendar
   is up does nothing at all. Dismiss each picker (**Done**, else Escape) before
   touching the next control.
5. **The two pickers constrain each other.** The start calendar disables days
   after the current end, and vice versa. Moving a range forward must set the
   **end** first; moving it backward must set the **start** first.

### Today is never selectable

Today and every later day render disabled — ads data is complete only through
**yesterday**. This invalidates Zepto-style presets wholesale: there, `last7`,
`last30`, `thismonth`, `thisquarter` and `thisyear` all *ended today*. Here
every preset must end on the last complete day, so "last 7 days" means seven
**complete** days — which is what anyone pulling ads data actually wants.

Other calendar facts: day cells are `<button role="gridcell">` whose text is the
bare day number, so **scope the lookup to the calendar body** or `"1"` matches
`"10"`, `"21"` and the rows-per-page control. Clicking a day commits
immediately; **Done only closes**. And because a wrong date is worse than no
report, re-read the trigger afterwards and fail if it does not show what was
asked for.

### Other filters

- **Ad types** — multi-select, default "All Ad Types". Five, three nested: Item
  Ads (5 sub-options), Banner Ads (7), Auto Suggest Ads, Guaranteed Top Slots,
  Collection Ads (2). Sub-option names were never probed.
- **Campaigns** — default "All Campaigns", backed by a type-to-search box. Not
  enumerable in bulk; leave at the default.
- **Generate Report** — plain `<button>`, exact text match.
- "MORE FILTERS" expands nothing; it labels the row.

## Sales

`download_sales.py` with `sales_options.json`, which records the brands and
cities discovered on the portal (a real capture: BACARDI, Dilmah Tea, Del
Monte; ~20 cities). Same login and session as Ads — no second sign-in.

The engine behind it was never imported, so this side needs re-probing against
the live portal before it can be ported. Treat `sales_options.json` as evidence
of the filter shape, not as a contract.

## Gotchas

| Trap | Consequence |
|---|---|
| Clicking nav text | nothing happens — no `<a href>`, router pushes only |
| `get_by_test_id` on a date picker | strict-mode ambiguity across three elements |
| Scoping to `date-picker-end-date` | never matches — the portal reuses the start id |
| Not dismissing a picker | the next click is swallowed by the overlay |
| Setting start before end when moving forward | the target day is disabled |
| Zepto-style presets ending today | today is never selectable |
| Whole-page text search for a report type | clicks a table cell, type never changes |
| A tight collect poll | reports take 5–10 min; retention is 7 days |
