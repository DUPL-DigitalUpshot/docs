# Toggle admin and the Visibility switchboard

How to run the one role that decides what everyone else is shown. The *why*
lives in PRD §4a and FR-2a, the screen in UI_PLAN §2a–2b, and the decisions in
DECISIONS.md (2026-09-23, 2026-09-26, 2026-09-28). This page is the *how*.

## What it is

| | |
|---|---|
| Role | `toggle_admin` ("Toggle admin"), the fourth role, outside super_admin › admin › member |
| Who | The product owner at Digital Upshot. One person, maybe two |
| Can do | Everything an Admin can, plus **Visibility** (`/visibility`) under a *Product* group in the sidebar |
| Sees | Always the full sidebar. Rules never apply to this role, so it can't hide its own switch |
| Invisible to | Everyone else. It is left out of user lists, can't be invited or promoted to or from, and its endpoints answer 404 to everyone else, before routing |
| Created by | `infra/.env` only. No screen can create one |

## Setting it up

In `infra/.env` (never committed):

```
UNIQCAI_TOGGLE_ADMIN_EMAIL=owner.person@example.com
UNIQCAI_TOGGLE_ADMIN_PASSWORD=<a first password>
UNIQCAI_TOGGLE_ADMIN_NAME=Toggle admin
```

When the API starts, `seed_toggle_admin()` (`backend/app/core/seed.py`) creates
the account if the email doesn't exist yet. An empty password is refused. The
first sign-in forces a password change, so the value in `.env` works once.

The seed **skips an email that already exists**, so editing `.env` later changes
nothing. Use the repair instead.

## Repair or recover: `make toggle-admin`

```
make toggle-admin
```

This runs `backend/app/cli/toggle_admin.py`, and running it twice is safe:

- **No account for the email:** it creates one as Toggle admin.
- **The account exists:** it resets the password to the `.env` value, restores the role to `toggle_admin` and reactivates the account.
- **Either way,** it sets `must_change_password`, so you choose a new password at the next sign-in.

Use it when the owner can't sign in, was deactivated, or lost the role. This is
the only way back to the switchboard: no other role can see or grant it. If
repeated failed sign-ins have locked the owner out, run `make unlock-login` first.

## Using the switchboard

Sign in as the Toggle admin → **Product › Visibility**.

1. Pick an audience tab: **Admin · Manager · Executive**.
2. Set each row to **Visible**, **Locked** or **Hidden**. The rows are the sidebar
   sections plus a Platform → Category → Report tree.
3. Optionally add a note to a *Locked* row. It becomes that item's tooltip
   ("Coming soon" if left empty).
4. **Save**. The button stays disabled until something changes. Your own shell
   refreshes at once; other people see the change on their next page load.

Every save is written to the audit log as `visibility.updated`.

### Who counts as which audience

| Person | Audience |
|---|---|
| Super admin, Admin | **Admin** |
| Member whose highest brand grant is Manager | **Manager** |
| Member whose highest brand grant is Executive | **Executive** |
| Member with no grants | none: their sidebar is already empty |
| Toggle admin | never filtered |

So **a Super admin follows the Admin tab.** If something is locked for Admin,
the owner account (`super_admin`) sees it locked too. On 2026-09-28 Runs,
Schedules, Report library, Users & access, Settings and Audit log were locked
for Admin, which is why the client demo video shows them as "Coming soon".

### What each state does

| State | In the sidebar and catalogue | Typing the URL |
|---|---|---|
| Visible | shown as normal | works |
| Locked | greyed, lock icon, tooltip; not a link | bounces to Overview |
| Hidden | not there (an emptied group leaves no stray divider) | bounces to Overview |

The same three states apply to platforms, categories and report types
wherever the catalogue appears: the connect wizard's tiles, the Run now report
tree and the Report library filters.

The **Brands** row also covers every brand page and the brand switcher.
*Hidden* removes the switcher and the *This brand* group; *Locked* leaves a
greyed placeholder in the switcher's place.

### Unified data and Data status (added 2026-10-03)

| Row | What it covers | Who has it to begin with |
|---|---|---|
| **Unified data** (key `warehouse`) | The `/data` screens (Needs attention, Reports, Imports); the Needs attention and Imports views on each brand's **Data** tab and *Set up unified data for <Brand>*; for admins, the *Feeds unified data* badge on Schedules and the warning before pausing or deleting the last schedule behind a feeding report | Admin |
| **Data status** (key `data_status`) | Not a sidebar entry. The Report library's status badges (*Checked*, *Being checked*, *Held back, being re-pulled*, *Provisional*) and its *Data status* filter; each brand's **Data** tab (Status view); for brand users, the *Feeds unified data* badge on Schedules. Words and dates only, never a number | Admin, Manager, Executive |

- For **Data status**, *Locked* behaves like *Hidden*: a badge or a tab has no greyed form, so both remove it, and typing `/brands/<id>/data` bounces to Overview. The note is unused.
- Hiding **Unified data** for Admin keeps the brand Data tab's Status view (it follows *Data status*) but drops the admin views, the Schedules badge and the warning. The brand's admin views need both rows visible.
- Brand users never reach `/data`, whatever the row says; *All brands* from a Data tab takes them to the brand list.
- As with every row, this is presentation only: `GET /brands/{id}/data-status` and the files' `data_status` still answer, under RBAC.

## The two limits, on purpose

- **Rules only take away.** Marking *Users & access* visible for Executive
  doesn't give it to them, because that audience never had it.
- **It is presentation, not security.** The API answers exactly as before. A
  hidden section is still reachable through the API by anyone whose role
  allows it. Access is enforced by RBAC (`scope_to_user_brands`), never here.

## For developers

| Piece | Where |
|---|---|
| Role, audiences, states | `backend/app/core/types.py`: `TOGGLE_ADMIN`, `Audience`, `VisibilityState`, `audience_for()` |
| Rules table | `ui_visibility`, migration 0008. Model in `backend/app/modules/visibility/models.py` |
| API (toggle admin only, else 404) | `GET /api/v1/visibility/catalogue`, `GET /api/v1/visibility/rules`, `PUT /api/v1/visibility/rules` (replaces the whole matrix) |
| Rules sent to each user | `rules_for_user()` in `visibility/service.py`, delivered with `/auth/me` |
| Section keys | `SECTIONS` plus `FEATURE_SECTIONS` (sections with no page, e.g. `data_status`) in `frontend/src/app/sections.ts`, mirrored in `visibility/service.py`. Keep the two in step. Components check a feature section with `useShowsSection()` (`frontend/src/lib/visibility.ts`) |
| Route guard | `RequireSection` in `frontend/src/features/auth/guards.tsx` |
| Screen | `frontend/src/features/visibility/` |
| Tests | `backend/tests/rbac/test_visibility_rbac.py`, `backend/tests/unit/test_visibility_rules.py`, `frontend/src/app/nav.test.ts` |

When you add a sidebar section, add its key to both `SECTIONS` lists, or the
switchboard can't control it.
