# Zepto — port reference

How the Zepto prototypes actually work, and what that means for
`backend/rpa/adapters/zepto/`. `legacy/README.md` says *which* old file becomes
which new one; this says *what the code has to do* and which behaviours are
load-bearing.

Sources: `legacy/zepto/zepto_session.py`, `report_engine.py`,
`vendor_report_engine.py`, `otp_provider.py`, `config.example.py`, and
`legacy/zepto/docs/vendor-reports.md` (probed against the live portal,
2026-09-02).

## One login, two portals

| | `zepto.ads` | `zepto.vendor` |
|---|---|---|
| Host | `brands.zepto.co.in` | `fcc.zepto.co.in` (UI at `brands.zepto.co.in/vendor/reports`) |
| Driven by | Browser (DOM) | **JSON API** |
| Reports | 6 × Sponsored Products + 6 × Sponsored Brands (+ 6 Sponsored Display, inactive) | 13 vendor reports |
| Brand identity | `?selectedBrand=<uuid>` in the URL | the **JWT**; `selectedBrand` is stripped |
| Login | email + password + OTP | none of its own |

The `<projectId>_AUTH_TOKEN` cookie is scoped to `.zepto.co.in`, so **one
sign-in covers both**. `ZeptoSalesAdapter` declares
`shares_session_with = "zepto.ads"` for exactly this reason: no second browser,
no second OTP.

> The executor does not honour that yet — it resolves one adapter per run
> (`executor.py:323-324`) while `RunTask.portal_key` is per report. Mixing Ads
> and Sales reports in one run currently drives half the tasks through the wrong
> adapter. Dormant only because the vendor adapter is a stub.

## Sign-in (`zepto_session.py`)

Runs **headed under Xvfb**: Zepto sits behind AWS WAF and challenges headless.

1. `wait_login_or_dashboard` — decides on `"/login" in url or "/auth" in url`,
   polling every 500 ms up to `PAGE_LOAD_TIMEOUT` (60 s). It is the only
   judge of "signed in"; a page that is neither is treated as signed out.
2. `fill_credentials` — `#email`, `#password`, then an **exact-match** "Log In".
   Exactness matters: a loose match hits "Continue with Google".
3. `wait_after_submit` — waits for any of five OTP-input candidates.
4. `enter_otp` — clears with Ctrl+A, Delete, then **eight Backspaces**, and
   types the code **character by character with `delay=120`**. The eight
   backspaces are for split one-digit boxes, where a single clear leaves
   earlier boxes filled.
5. Verify, or assume auto-submit if no verify button appears within 5 s.
6. **Resend-and-retry**, up to `OTP_MAX_ATTEMPTS = 3.** The account is shared
   with humans, so a colleague can consume the code we matched. On rejection it
   requests a fresh OTP and excludes the used email before waiting again.

**Session:** a persistent Chromium profile **and** a saved cookie jar. Both,
not either — Zepto's auth token is a *session* cookie that Chromium drops on
exit even with a persistent profile, so the profile alone loses the session
every run.

**A broken session is wiped, not repaired** (`wipe_profile`). The account is
shared and gets invalidated server-side; that is normal, not exceptional.

**OTP rule:** sender `mailer@zeptonow.com`, code regex
`otp code is\s*(\d{4,8})` (`config.example.py`). Legacy also had a loose
`\b(\d{4,8})\b` fallback; it is deliberately **not** ported — it would match
years and order numbers.

## Ads — a two-phase export

Clicking export queues a job server-side; the file appears later in a report
centre. So `download()` requests, then polls, then matches rows back to
requests.

**Three things drive the whole design:**

1. **"No data found" is also what loading looks like.** A card mid-fetch says
   it, and Zepto only fetches a card's table once it scrolls into view. Every
   no-data verdict must therefore *persist* before it is believed —
   `confirmed_no_data` holds it for 15 s, re-scrolling each pass, and one frame
   with data cancels it immediately.
2. **The account is shared with humans.** A colleague's rows appear in the same
   report centre, so rows must be matched to *our* requests, not taken in order.
3. **Export needs `selectedBrand` in the URL**, or the API answers "required
   parameter brand_id is missing".

**Report anchors** (`REPORTS` in `report_engine.py`) — each is either a card
subtitle or a tab:

| Key | How to find it |
|---|---|
| `campaign` | subtitle "Campaign Performance" |
| `product` | tab "Product Performance" |
| `category` | tab "Category Performance" |
| `keyword` | tab "Keyword Performance" |
| `city` | subtitle "City Level Performance" |
| `page` | subtitle "Page Level Performance" |

**Order of operations per report:** scroll into view → 1.5 s → `wait_card_loaded`
(25 s) → `confirmed_no_data` (15 s) → `card_stable_with_data` (10 s, 2.5 s
poll) → set the date range → export → poll the report centre.

**The date picker** is `dd/mm/yyyy` (note: the *vendor* modal is `mm/dd/yyyy`).
Legacy retries the whole picker interaction **once** on failure — "popovers can
be flaky" — pressing Escape first to close a half-open one. Then it *verifies*
the applied range and refuses to proceed on a mismatch.

**Identifying the downloaded file:** by its **own header row**
(`sniff_report_type`), never by row order — a missing or extra row would shift
every mapping. A file whose type cannot be read is `UNMATCHED_`, **not**
assumed to be the one we asked for.

**Row matching** uses a baseline taken *before* requesting, and `Requested At`
has only **minute** resolution, so the comparison is `<=` and legacy takes
**one baseline per batch of six**, not one per report. A per-report baseline
re-taken inside the same minute cannot see its own row.

## Sales — a JSON API

Base `https://fcc.zepto.co.in/api/v1/reports`. Three calls:

| Call | Purpose |
|---|---|
| `GET /api/v1/reports?offset=0&limit=15` | the queue, newest first |
| `POST /api/v1/reports/request` | queue one, returns `reportId` |
| `GET /api/v1/reports/{id}/download` | returns a presigned S3 URL |

**Cookies alone are not enough.** Every call needs these headers, all derivable
from the session:

```
authorization:   <value of the "<projectId>_AUTH_TOKEN" cookie>   # raw JWT, no "Bearer"
x-aws-waf-token: <value of the "aws-waf-token" cookie>
x-proxy-target:  brand-analytics
waf-enabled:     false
accept:          application/json
```

Playwright's `context.request` carries the browser context's cookies, so these
can go through the same authenticated session — no second HTTP client, no
copied token.

**Dates are IST midnight expressed in UTC.** `2026-08-31` becomes
`2026-08-30T18:30:00.000Z` (00:00 +05:30), and `endDate` is the *start* of the
end day. Getting this wrong silently shifts the whole report by a day — the
worst kind of bug, because the file looks perfectly valid.

**Status vocabulary differs from Ads**: `IN_PROGRESS` → `COMPLETED`, or
`FAILED`. The ads report centre says *Success*; this one says **COMPLETED**.

**The `reportId` is an exact handle** — no timestamp guessing, none of the
row-ownership heuristics the ads centre needs.

**The presigned URL is valid 24 h and needs no auth headers.**

**Read the file extension from the S3 path, never assume.** Most are CSV but
**MSL returns a real xlsx workbook**; naming an xlsx `.csv` and parsing it as
text is how the first version broke.

### Report types — dropdown label → API enum

Read from the MUI select's hidden input, so authoritative rather than guessed.

| Label | Enum | Dated? |
|---|---|---|
| Sales_F | `SALES` | **yes** |
| Non FBZ Sales Ledger | `NON_FBZ_SALES_LEDGER` | **yes** |
| Fill Rate | `FILL_RATE` | snapshot |
| DEQ Inventory | `DEQ_INVENTORY` | snapshot |
| OOS Visibility | `OOS_VISIBILITY` | snapshot |
| OTIF | `OTIF` | snapshot |
| Vendor Inventory_F | `INVENTORY` | snapshot |
| Catalogue | `CATALOGUE` | snapshot |
| ODR | `ODR` | snapshot |
| ODR_Discrepancy at IB | `ODR_INBOUND` | snapshot |
| RTV | `RTV` | snapshot |
| GRN | `GRN` | snapshot |
| MSL | `MSL` | snapshot |

`SALES_OVERVIEW` appears in old queue rows but is **retired** — no longer
offered.

**"Snapshot" does not mean the range is unvalidated.** `OOS_VISIBILITY` rejects
anything wider than a week:

```
HTTP 400 {"error":{"message":"date range should be max selectable upto 7 days"}}
```

Legacy does **not** hardcode a per-type limit table, which would rot. It reads
the number out of Zepto's own rejection, retries inside the cap, and records
what it actually used — so the file is named for the range it really covers,
not the one that was asked for. Worth keeping.

### SALES file schema

13 columns, one row per SKU × city × day: `Date, SKU Number, SKU Name, EAN, SKU
Category, SKU Sub Category, Brand Name, Manufacturer Name, Manufacturer ID,
City, Sales (Qty) - Units, MRP, Gross Merchandise Value`. `Date` is `dd-mm-yyyy`.

## Rule 9 — verifying the brand, on both sides

A wrong pick yields a complete, believable file for the wrong business that
nothing downstream can detect. Both portals must verify, by different means:

- **Ads** — capture the brand UUID from `?selectedBrand=` and compare it with
  `connections.portal_brand_selector`. Raise `WrongAccount` on a mismatch;
  `AccountChoiceRequired` when the connection says nothing. Never guess.
- **Sales** — there is no selector; the brand comes from the token. Verify
  against `tags.brandIds` / `tags.manufacturerId` from
  `GET /vendor/api/v1/auth/get-user-by-token`. The mechanism differs; the rule
  does not.

## Do not port

- **`stamp_dates` (`report_engine.py`) and `stamp_dates_csv`
  (`vendor_report_engine.py`).** They inject the date range into the downloaded
  file because ads exports carry no date column. CLAUDE.md rule 6 forbids it —
  files are stored byte-for-byte, and the period lives in
  `report_files.period_start/end` and the generated download filename. Note the
  vendor SALES file already has a per-row `Date`, so legacy skipped stamping it
  anyway.
- **`dump_debug` on the login page.** It screenshots a filled-in password field
  (rule 1). Failure screenshots are taken only after navigating away from a
  login form.
- **The loose OTP fallback regex** (see Sign-in).
- **`PRESET_FOR_SPEC` / `resolve_range`.** The executor hands the adapter two
  explicit dates; presets are a UI concern now. Dropping the preset escape
  hatch also makes `verify_applied` strict, which is an improvement.
- **`webapp.py` / `templates/`** — replaced by the React UI.

## Gotchas, in one place

| Trap | Consequence |
|---|---|
| Vendor dates not converted to IST-midnight-in-UTC | report silently shifted by one day |
| Assuming vendor files are CSV | MSL is xlsx; parsing it as text breaks |
| Trusting the first "No data found" | a report with data is recorded as empty |
| Per-report report-centre baseline | a second report in the same minute never finds its row |
| Accepting a file whose header will not parse | a believable file filed as the wrong report |
| Matching report-centre rows by order | a colleague's row is taken as ours |
| Loose "Log In" match | clicks "Continue with Google" |
| Single OTP clear | split one-digit boxes keep earlier digits |
| Persistent profile without the cookie jar | session lost every run |
| Headless | AWS WAF challenge |
