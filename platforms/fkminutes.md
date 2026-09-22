# Flipkart Minutes — port reference

Two portals in one legacy folder, and they are **different sites, not sections
of one**:

| | `fkminutes.ads` | `flipkart.sellerhub` |
|---|---|---|
| Host | `advertising.flipkart.com` | `seller.flipkart.com` |
| Carries | Minutes ads | marketplace ads (PLA/PCA), and the Sales surface |
| Login | email + password + OTP, **no account picker** | username → password → **seller-account picker** → OTP |
| New home | `rpa/adapters/fkminutes/ads.py` | `rpa/adapters/fkminutes/sales.py` |

Sources: `legacy/fkminutes/docs/minutes-flow.md` (captured live 25 & 31 Aug
2026, "observed, not inferred"), `login-flow.md`, `ads-report-flow.md`,
`minutes_session.py`, `minutes_report_engine.py`, `minutes_account.py`.

## Minutes sign-in

```
advertising.flipkart.com/login?returl=/
  input[type=text][placeholder="Enter email"]
  input[type=password][placeholder="Enter password"]
  button[type=submit] "Login"
  → six input.otp-input boxes
  → dashboard
```

The inputs carry **no `id` or `name`** — locate by type and placeholder.

- **The URL tells the truth about login state.** Logged out is always
  `/login?returl=…`. The Seller Hub next door cannot do this and needs DOM
  markers.
- **No Verify button.** The six boxes auto-advance and submit themselves once
  the last digit lands.
- **Resend is on a countdown** ("Resend OTP in 19 seconds") and only arms when
  it expires — a retry must *wait*, not click.
- **reCAPTCHA Enterprise** loads on the page, so headed Chromium on a
  persistent profile is as deliberate here as on Zepto.

### The OTP goes to the login address, but is read somewhere else

The masked hint says `aw**********************om` — the login address itself.
But that is a personal account that **cannot issue an app password**, so its
mail is forwarded to a relay and the code is picked up there
(`MINUTES_OTP_MAILBOX`).

This is the origin of the **relay mailbox** concept and of recipient matching
in `SYSTEM_DESIGN.md` §6. Instamart can watch the login address directly; this
portal cannot. Point the account at the *relay* inbox, not the login address —
matching still lines up because it uses the login id.

> Recipient matching is **new code with no prior art**: no legacy reader looks
> at `To`, `Delivered-To` or any `X-Forwarded-*` header — they read only
> `Date`, `From` and `Subject`.

## Ad accounts — `baccount` / `aaccount`

Despite there being no picker at login, there *is* an account dimension. The
landing route carries both ids:

```
/ad-account/campaigns?baccount=ZWP03W9X5C26&aaccount=AOM4OYMP7PB7
```

The header hides a **Switch to account** menu listing (as captured) **14 ad
accounts under 6 businesses**. Each row is an `<a>` whose href already carries
both ids, so `minutes_account.discover()` *reads* them rather than clicking
through. Rows without an href are business headings, not accounts.

**Switching is a plain navigation**, so a run never touches the menu — it goes
straight to the report form for the pair it wants.

**Four of the account names differ only in punctuation, and one is called "Do
not Use this account".** `minutes_account.py` therefore treats an ambiguous
substring as an **error rather than a pick** — which is exactly CLAUDE.md rule
9, and is where that rule came from. `baccount`/`aaccount` is what
`connections.portal_brand_selector` has to hold here.

## Reports

Not a separate area — a filter on the ads console's report form at
`/ad-account/reports/others?baccount=…&aaccount=…`. Four controls: **Ad
Product** (only `PLA` is selectable), **Select Report For**
(Flipkart | Grocery | Minutes), **Report Type**, **Date**, then Download
streams a CSV.

**`Select Report For` must be set _before_ the report type** — changing it
rewrites the type list, so setting the type first leaves whatever the new list
defaulted to.

| Scope | Report types |
|---|---|
| Minutes & Grocery (same seven) | Consolidated FSN, Consolidated Daily, FSN Attribution, Business Zone Level, Search Term, Placement Performance, Keyword |
| Flipkart | swaps in Seller Level and Attributed FSN |

`MAX_DAYS = 31`.

The CSVs carry `Start Time` / `End Time` preamble rows, and `read_file_range()`
verifies them — a built-in check that the file covers what was asked for. Worth
keeping: it is the same instinct as Zepto's header sniffing.

### Traps

- **A product tour blocks every click on a fresh profile.** It sits behind a
  `MouseEventsBlockingOverlay` that can **outlive its own Dismiss button**, so
  the overlay is removed explicitly after dismissing — otherwise the tabs read
  as dead rather than covered.
- **The nav rail is collapsed**; "Reports" exists but is not visible until
  hovered. Navigating by URL avoids it entirely.
- **The portal's week is not Python's.** Its "Last Week" preset is
  Sunday–Saturday; `resolve_range()` builds Monday–Sunday. So
  `set_date_range()` **reads the control back** after clicking a preset and
  falls through to the custom calendar when they disagree — *otherwise every
  preset run downloads a believable file about the wrong seven days.* That is
  the single most valuable line in this folder.
- **The calendar renders two non-adjacent months** (August beside October, the
  right panel entirely disabled) and marks unselectable days with a `disabled`
  class. `CALENDAR_JS` splits panels by grouping columns seven at a time.

## Seller Hub (Sales) — still an open question

`flipkart.sellerhub` is the source for Flipkart Minutes · Sales. Port the login
(username → password → **seller-account picker** → OTP) and the download/verify
loop.

**Which Seller Hub reports count as Sales is unresolved (PRD §12 Q7).** The
pipeline pulls the eight *ads* reports from Ads › Reports › Other Reports,
while the sales surface is the **Report Centre** at
`#dashboard/metrics/report-centre` (Fulfilment, Invoices, Listings, Payment,
Tax) — mapped in `docs/ads-report-flow.md` and **automated by nothing**. That
gap has to be closed before Sales can be built.

## Gotchas

| Trap | Consequence |
|---|---|
| Reading the OTP at the login address | it can't issue an app password; use the relay |
| Clicking Resend immediately | the button is on a countdown and not yet armed |
| Waiting for a Verify button | there isn't one; the form self-submits |
| Setting Report Type before Select Report For | the list is rewritten and the type silently reverts |
| Trusting the "Last Week" preset | Sun–Sat vs Mon–Sun: a believable file about the wrong week |
| Dismissing the tour without removing the overlay | every click is swallowed; tabs look dead |
| Matching an account name by substring | four differ only in punctuation, one says "Do not Use" |
| Assuming one account per login | 14 ad accounts under 6 businesses, on one login |
