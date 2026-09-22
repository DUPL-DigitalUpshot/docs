# Platform port references

One file per platform: what the prototype in `legacy/` actually does, and which
of its behaviours are load-bearing. `legacy/README.md` maps *which* old file
becomes which new one; these say *what the code has to do*.

| Platform | Portals | State |
|---|---|---|
| [zepto.md](zepto.md) | `zepto.ads` (browser), `zepto.vendor` (JSON API, shares the ads session) | Ads implemented; Sales next |
| [blinkit.md](blinkit.md) | `blinkit.brandcentral` (magic link), `blinkit.partnersbiz` (OTP) | stubs |
| [instamart.md](instamart.md) | `instamart.brandportal` (one login serves Ads + Sales) | stub; **engine code was never imported** |
| [fkminutes.md](fkminutes.md) | `fkminutes.ads`, `flipkart.sellerhub` | stubs |
| [bigbasket.md](bigbasket.md) | — | on hold, no prototype |

## What these are for

Each one ends in a **gotchas** table. Those are not style notes: nearly every
row is a failure that produced a *believable wrong file* or a *silent* timeout
in the prototype, which is the failure mode this product exists to prevent
(CLAUDE.md rules 6 and 9).

Themes that recur across platforms, and therefore belong in shared code rather
than in each adapter:

- **Per-report date-range caps are real**, not advisory — Zepto
  `OOS_VISIBILITY` (7 days), Blinkit `po` (30), Instamart Granular and Search
  Query (31), FK Minutes (31). `ReportType.max_range_days` exists but is not
  enforced.
- **Read back what you set.** Zepto verifies the applied range, FK Minutes
  re-reads the week preset, Instamart re-reads the date trigger. Each was added
  after a run produced a plausible file about the wrong period.
- **Never match a downloaded file by position.** Zepto sniffs its header;
  Instamart writes the report name; Zepto vendor gets an exact `reportId`.
- **One login can carry several businesses** — Zepto brand UUID, PartnersBiz
  `PB_ENTITY`, FK Minutes `baccount`/`aaccount`, Instamart, Flipkart Seller
  Hub. Verify, never guess (rule 9).
- **Two-phase exports differ wildly in timing**: Zepto ads ~90 s, Instamart
  5–10 min with 7-day retention. A single poll budget will not fit both.
