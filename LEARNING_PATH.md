# Learning path — how to understand UniQCAI and change it safely

Written for someone who can read and write code but has not used Docker, PostgreSQL, Make, or a
background-worker setup before. Everything here is about *this* repo: no general tutorials, only the
parts of each tool this project actually uses.

Work top to bottom. Each section says **what it is**, **why this project needs it**, **the 20% you
must know**, and **something to try in this repo**.

---

## 0. The one-paragraph mental model

UniQCAI logs into quick-commerce seller portals (Zepto, Blinkit, Instamart, Flipkart) *with a real
browser*, downloads report files, and stores them for brand users to fetch. Because a browser login
can take minutes and needs an OTP from an email inbox, that work cannot happen inside a web request.
So the system is split into **six processes**, each in its own container:

```
        browser (you)
             │  http://localhost:5174   (FRONTEND_PORT in infra/.env)
             ▼
     ┌───────────────┐   proxies /api    ┌──────────────┐
     │   frontend    │ ────────────────► │     api      │  FastAPI, answers in milliseconds
     │ React + Vite  │ ◄──────────────── │  (uvicorn)   │
     └───────────────┘   JSON + SSE      └──────┬───────┘
                                                │ writes rows        ┌────────────┐
                                                ├───────────────────►│  postgres  │ the facts
                                                │                    └────────────┘
                                                │ pushes a job       ┌────────────┐
                                                ├───────────────────►│   redis    │ the queue + live events
                                                │                    └─────┬──────┘
                                                │                          │ pops the job
                                         ┌──────┴───────┐            ┌─────▼──────┐
                                         │  scheduler   │            │   worker   │ Playwright drives
                                         │ every 60s,   │            │ Xvfb +     │ a real Chromium,
                                         │ "is anything │            │ Chromium   │ downloads files to
                                         │  due?"       │            └─────┬──────┘ /data/storage
                                         └──────────────┘                  │
                                                                           └─► report files on disk
```

Two sentences worth memorising:

1. **The API never does slow work.** It writes a `runs` row, drops a message on Redis, and returns.
   The worker picks it up. The browser watches progress over SSE (a one-way live stream).
2. **Postgres holds truth, Redis holds work-in-flight.** Wipe Redis and you lose queued jobs; wipe
   Postgres and you lose the product.

Start reading the code at [backend/app/main.py](backend/app/main.py) → [backend/app/api.py](backend/app/api.py)
→ [backend/workers/tasks.py](backend/workers/tasks.py) → [backend/rpa/executor.py](backend/rpa/executor.py).

---

## 1. Make — the command menu (30 minutes)

**What it is.** `make` reads a file called `Makefile` and runs the shell commands listed under a
name. That name is called a *target*. `make dev` means "run the recipe named `dev`".

**Why here.** Every real command in this project is long
(`docker compose -f infra/docker-compose.dev.yml --env-file infra/.env up --build -d`). The
[Makefile](Makefile) gives each one a short name so nobody has to remember flags — and so everyone
runs them identically.

**The 20%:**

- `make help` prints every target with its description. Run this first, always.
- A target's body must be indented with a **TAB**, never spaces. This is the #1 reason a Makefile
  edit breaks.
- `make revision m="add users"` — the `m=...` is a *variable*, read inside the recipe as `$(m)`.
- `.PHONY` at the top just tells make these targets are commands, not filenames.
- Lines starting with `@` don't echo themselves before running.

**Targets you will use daily** (all defined in [Makefile](Makefile)):

| Command | What it does |
|---|---|
| `make dev` | Build images and start all six containers |
| `make up` / `make down` | Start / stop without rebuilding (data kept) |
| `make logs` | Follow the logs of every service — your main debugging tool |
| `make ps` | Which containers are running and healthy |
| `make migrate` | Apply database migrations |
| `make test` | Backend pytest + frontend vitest |
| `make lint` / `make fmt` | ruff + tsc + eslint / autofix |
| `make types` | Regenerate the frontend's API types from the live API |
| `make clean` | Stop everything **and delete the database volume** — destroys local data |

**Try it:** run `make help`, then `make ps`. Then open [Makefile](Makefile) and find the exact
`docker compose` line that `make logs` expands to.

---

## 2. Docker and Docker Compose — the six boxes (1–2 days)

This is the biggest new concept. Take it slowly; everything else depends on it.

### 2.1 The three nouns

- **Image** — a frozen, read-only filesystem: an OS plus Python plus this project's dependencies.
  Built once from a `Dockerfile`. Think "installer".
- **Container** — a running process started from an image, isolated from your machine. Think
  "running program". Containers are disposable: delete one, start another from the same image.
- **Volume** — a named disk area that *survives* containers being deleted. Anything not in a volume
  disappears when a container is recreated.

This repo has four volumes, declared at the bottom of
[infra/docker-compose.dev.yml](infra/docker-compose.dev.yml): `pgdata` (the database files),
`redisdata`, `storage` (downloaded report files), `profiles` (browser profiles holding portal
cookies — these are secrets).

### 2.2 The Dockerfiles

- [infra/Dockerfile.api](infra/Dockerfile.api) — Python 3.12, installs `backend/pyproject.toml`
  dependencies with `uv`, copies `backend/`. Used by both **api** and **scheduler**.
- [infra/Dockerfile.worker](infra/Dockerfile.worker) — the same plus Chromium, Playwright and
  **Xvfb** (a fake screen, so a *visible* browser can run on a server with no monitor). The portals
  block invisible/headless browsers, which is why this exists (`CLAUDE.md` rule 10).
- [infra/Dockerfile.frontend](infra/Dockerfile.frontend) — Node 22, `npm install`, runs the Vite dev
  server.

The one Dockerfile idea worth understanding: **layer caching**. Notice
[Dockerfile.api](infra/Dockerfile.api) copies `pyproject.toml` and installs dependencies *before*
copying the source. Docker caches each step; because dependencies are their own step, editing a
Python file does not reinstall every package. If you ever reorder those lines, builds get slow.

### 2.3 Compose — the file that wires the six together

[infra/docker-compose.dev.yml](infra/docker-compose.dev.yml) is the single most important
infrastructure file. Read it end to end once — its comments explain nearly every choice. What to
look for:

- **`services:`** — the six containers: `postgres`, `redis`, `api`, `worker`, `scheduler`,
  `frontend`.
- **`x-backend-env: &backend-env`** — a reusable block of environment variables. `&backend-env`
  defines it, `*backend-env` (in api, worker, scheduler) pastes it in. That is YAML anchors, not
  Docker.
- **Networking by name.** Inside Docker, `postgres`, `redis` and `api` are *hostnames*. That is why
  the database URL says `@postgres:5432` and the frontend proxies to `http://api:8000`. Your
  machine cannot use those names — from your terminal it is `localhost`.
- **`ports: "8000:8000"`** — left is the port on **your machine**, right is the port **inside** the
  container. Only mapped ports are reachable from outside.
- **`volumes: ../backend:/srv/backend`** — a *bind mount*: your source folder appears live inside
  the container. This is why editing a `.py` file reloads the API instantly without a rebuild.
- **`depends_on` + `healthcheck`** — the api waits until postgres reports healthy, so it does not
  start against a database that is still booting.
- **`${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in infra/.env}`** — read from `infra/.env`; the
  `:?` form makes compose refuse to start if it is missing.

### 2.4 Environment files

`infra/.env` (gitignored, never commit) holds 29 settings; `infra/.env.example` is the committed
template. `make dev` runs `env-check` first, which refuses to start if `UNIQCAI_MASTER_KEY` or
`POSTGRES_PASSWORD` is missing and warns when `.env.example` has gained a setting yours lacks.

**The master key matters:** it encrypts every stored portal password. Lose it and every saved
credential is unreadable. Never print it, never commit it.

### 2.5 The rebuild rule — memorise this

| You changed | What to run |
|---|---|
| A `.py` or `.tsx` source file | Nothing. Bind mount + reload picks it up |
| `backend/pyproject.toml` or `frontend/package.json` | `make dev` (rebuilds the image) |
| A `Dockerfile` | `make dev` |
| `infra/.env` | `make up` — **not** `make restart`; restart reuses the old environment |
| `docker-compose.dev.yml` | `make up` |
| A model (`models.py`) | `make revision m="..."` then `make migrate` |

**Try it:** `make ps`, then `docker compose -f infra/docker-compose.dev.yml --env-file infra/.env
exec api bash` (or just `make shell-api`) and run `ls /srv/backend` — you are standing inside the
container looking at your own source folder.

---

## 3. PostgreSQL — where the facts live (1 day)

**What it is.** A relational database: tables with typed columns, rows, and foreign keys linking
them. Postgres 16 runs in its own container from the official image; nothing is installed on your
machine.

**The 20% of SQL** you need to read this codebase: `SELECT ... FROM ... WHERE ... JOIN ... ON ...`,
`INSERT`, `UPDATE`, and what a **primary key** (a row's unique id), a **foreign key** (a column
pointing at another table's id) and an **index** (a lookup shortcut) are. You will rarely write raw
SQL here — SQLAlchemy writes it — but you must be able to read it in logs.

**The tables.** [backend/app/models.py](backend/app/models.py) imports every model in one place and
is the fastest table-of-contents: brands, users, invites, grants, platforms/portals/report types
(the catalogue), platform accounts and connections (logins), mailboxes and OTP rules, runs, run
tasks, run events, report files, schedules, audit log, UI visibility. Each lives in
`backend/app/modules/<x>/models.py`. Pair this with `docs/SYSTEM_DESIGN.md` §data model.

### 3.1 SQLAlchemy — Python objects instead of SQL

An **ORM** maps a class to a table and an instance to a row. Read
[backend/app/core/db.py](backend/app/core/db.py) — its docstring explains the one genuinely subtle
thing in this codebase (the engine is cached *per event loop*, because the worker starts a new loop
per job).

Concepts to learn, in order: `Base` (the declarative base every model inherits), `Mapped[...]` /
`mapped_column(...)` column declarations, `relationship(...)`, **session** (a unit of work — you add
objects and `commit()`), and `select(Model).where(...)` query building. This project is **async**
SQLAlchemy 2.x, so queries are `await session.execute(select(...))`. Ignore older tutorials using
`session.query(...)`; that style is not used here.

### 3.2 Alembic — versioned schema changes

The database schema is not edited by hand. Every change is a numbered Python file in
[backend/alembic/versions/](backend/alembic/versions/) with `upgrade()` and `downgrade()`. Files
`0001` … `0008` form a chain; Postgres records which ones have run.

The workflow:

```bash
# 1. edit the model in backend/app/modules/<x>/models.py
make revision m="add split_by_day to schedules"   # alembic reads your models, writes a migration
# 2. READ the generated file. Autogenerate gets renames and enums wrong.
make migrate                                       # applies it
```

**Hard rule (CLAUDE.md #5): never edit a migration that has already run.** Write a new one. If your
local database gets into a bad state, `make clean` deletes the volume and you start from an empty
database plus `make migrate` — fine locally, never in production.

**Try it:** open [backend/alembic/versions/0006_schedules.py](backend/alembic/versions/0006_schedules.py)
and match every `op.create_table` column to the fields in
[backend/app/modules/schedules/models.py](backend/app/modules/schedules/models.py).

---

## 4. Redis, Dramatiq and the scheduler — how work gets done later (half a day)

**Redis** is an in-memory key-value store. This project uses it for three unrelated jobs:

1. **A job queue** — the API pushes "run 42, go", the worker pops it.
2. **A pub/sub channel** — the worker publishes live step events; the API's SSE endpoint subscribes
   and streams them to the browser. See [backend/app/core/events.py](backend/app/core/events.py).
3. **Login rate-limit counters** — `make unlock-login` deletes those keys when you lock yourself out.

**Dramatiq** is the library that turns a Python function into a queued job. Read
[backend/workers/tasks.py](backend/workers/tasks.py): a function decorated with `@dramatiq.actor`
becomes an *actor*. Calling `test_login.send(run_id)` from the API enqueues a message and returns
immediately; the worker container runs the body. Note the comment about importing
`workers/broker.py` first — that is what points Dramatiq at the right Redis.

**The scheduler** ([backend/workers/scheduler.py](backend/workers/scheduler.py)) is a plain loop
that wakes every 60 seconds, asks "which schedules are due in Asia/Kolkata?" using `croniter`, and
enqueues runs. It touches a heartbeat file each tick, which is what its healthcheck in the compose
file checks.

**The executor** ([backend/rpa/executor.py](backend/rpa/executor.py)) is where a run actually
happens: one lock per account, log in once, then each report. Read its module docstring — four
bullets, each a hard-won rule.

---

## 5. The backend — FastAPI, Pydantic, and this repo's module shape (2 days)

**FastAPI** turns a Python function into an HTTP endpoint and derives the OpenAPI schema from your
type hints. **Pydantic v2** validates the request body and shapes the response.

Every domain is one folder under `backend/app/modules/<x>/` with the same four files:

| File | Role |
|---|---|
| `router.py` | HTTP endpoints — paths, status codes, permissions. Thin |
| `service.py` | The actual logic. Testable without HTTP |
| `models.py` | SQLAlchemy tables |
| `schemas.py` | Pydantic request/response shapes |

Routers are collected in [backend/app/api.py](backend/app/api.py) under `/api/v1` and mounted by
[backend/app/main.py](backend/app/main.py), which also configures CORS, CSRF, error handlers,
logging and startup seeding.

Concepts to learn: **dependency injection** (`Depends(get_session)` hands the endpoint a database
session; `ActiveUser` hands it the signed-in user), **path/query/body parameters**, **response
models**, and `async`/`await` (why `await` appears before every database call).

Two project-specific rules that will fail review if you miss them:

- **RBAC** — every brand-scoped query goes through `scope_to_user_brands(query, user, min_level)`
  in [backend/app/core/rbac.py](backend/app/core/rbac.py), and every new endpoint gets a test in
  [backend/tests/rbac/](backend/tests/rbac/).
- **Secrets** — passwords, OTPs and session state are Fernet-encrypted at rest
  ([backend/app/core/crypto.py](backend/app/core/crypto.py)), never logged, never returned by the
  API, never rendered.

**The free documentation:** with the stack up, http://localhost:8000/api/docs is an interactive list
of every endpoint, generated from the code. Click "Try it out" and call one.

---

## 6. The frontend — React, Vite, TypeScript, TanStack Query (2–3 days)

- **Vite** is the dev server and bundler. [frontend/vite.config.ts](frontend/vite.config.ts) proxies
  `/api` to the api container so the browser only ever talks to one origin, and disables buffering
  so SSE streams arrive live.
- **React** — components are functions returning JSX; `useState` for local state, `useEffect` for
  side effects, props flow down.
- **TypeScript (strict)** — types are checked at build time. `make lint` runs `tsc`.
- **TanStack Query** — handles all *server* state: fetching, caching, loading/error flags,
  refetching after a mutation. You almost never need `useEffect` to fetch.
- **Tailwind + shadcn/ui** — styling via utility classes; UI primitives live in
  [frontend/src/components/ui/](frontend/src/components/ui/). **No hard-coded colours** — tokens
  only, from `docs/THEME.md` via `frontend/src/theme/tokens.css` (CLAUDE.md rule 8).

Layout: [frontend/src/app/](frontend/src/app/) (router, providers, AppShell),
[frontend/src/components/](frontend/src/components/) (shared: `common/`, `filters/`, `data/`),
[frontend/src/features/<area>/](frontend/src/features/) (one folder per screen — page component,
sub-components, and its own `api.ts`), [frontend/src/lib/](frontend/src/lib/) (the fetch wrapper,
generated types, SSE helper, formatters).

**The types rule (CLAUDE.md):** `frontend/src/lib/api-types.ts` is **generated** by `make types`
from the running API's OpenAPI schema. Never hand-edit it. Change a Pydantic schema → `make types` →
TypeScript immediately shows every frontend line that no longer matches. That loop is the main
safety net between the two halves of the app.

Read [frontend/src/lib/api.ts](frontend/src/lib/api.ts) first — auth is an HTTP-only cookie plus a
CSRF header, and its comments explain why the token is read per request.

---

## 7. Playwright and the RPA layer (learn when you touch an adapter)

**Playwright** drives a real Chromium: `page.goto(...)`, `page.click(...)`, waiting for selectors,
capturing downloads. Here it runs **headed** inside Xvfb because the portals challenge headless
browsers.

Shared machinery lives in `backend/rpa/`: `browser.py` (launching, profiles), `otp.py` + `imap.py` +
`mail.py` (reading the one-time code out of a mailbox), `storage.py` (saving files immutably),
`executor.py` (the run loop), `registry.py` (which adapter serves which portal). Portal-specific
selectors live **only** in `backend/rpa/adapters/<platform>/<category>.py` — nothing outside that
folder may know a URL or a CSS selector (CLAUDE.md rule 3).

To watch a run happen: set `UNIQCAI_BROWSER_VIEW=on` in `infra/.env`, `make up`, then `make watch`
for a VNC link.

---

## 8. Trace one real request end to end

Do this once with the files open; it is worth more than any tutorial. "Start a run" travels:

1. [frontend/src/features/runs/RunNowDrawer.tsx](frontend/src/features/runs/RunNowDrawer.tsx) — user
   picks brand, reports, dates.
2. [frontend/src/features/runs/api.ts](frontend/src/features/runs/api.ts) → `startRun(body)` →
   `post('/runs', body)`.
3. [frontend/src/lib/api.ts](frontend/src/lib/api.ts) — adds the CSRF header, sends cookies.
4. Vite proxy → `http://api:8000/api/v1/runs`.
5. [backend/app/modules/runs/router.py](backend/app/modules/runs/router.py) — validates against
   `StartRunRequest`, checks RBAC.
6. [backend/app/modules/runs/service.py](backend/app/modules/runs/service.py) — writes `runs` and
   `run_tasks` rows to Postgres, enqueues the Dramatiq actor. Responds. **Milliseconds.**
7. Redis holds the message; [backend/workers/tasks.py](backend/workers/tasks.py) `run_download`
   picks it up in the worker container.
8. [backend/rpa/executor.py](backend/rpa/executor.py) — locks the account, logs in once via the
   adapter, fetches OTP from the mailbox if needed, downloads each report, saves bytes +
   checksum through `rpa/storage.py`, writes `report_files` rows, publishes a step event to Redis
   after each step.
9. Meanwhile the browser holds an SSE connection to `/runs/{id}/events`
   ([router.py](backend/app/modules/runs/router.py) replays stored events, then follows Redis), and
   [frontend/src/features/runs/LiveRunPage.tsx](frontend/src/features/runs/LiveRunPage.tsx) renders
   them into `StepTimeline`.

---

## 9. Recipes for the changes you will actually make

**Add a field to an existing API response**
1. Add the column in `backend/app/modules/<x>/models.py`.
2. `make revision m="add <field> to <table>"`, read the generated migration, `make migrate`.
3. Add it to `schemas.py`; populate it in `service.py`.
4. `make types` — regenerates the frontend types.
5. Use it in the feature component. `make lint && make test`.

**Add a new endpoint**
1. Function in `service.py` (logic), route in `router.py` (thin), schemas in `schemas.py`.
2. Brand-scoped query? Use `scope_to_user_brands`. **Write the test in `backend/tests/rbac/`.**
3. `make types`, then a call in `frontend/src/features/<area>/api.ts`.

**Change a screen**
1. Find it under `frontend/src/features/<area>/`.
2. Reuse `DataTable`, `FilterBar`, `StatusBadge`, `EmptyState` from `components/`.
3. Cover all four states: loading, empty, error, no-permission.
4. Filters go in the URL via `useUrlFilters` so views are shareable.

**Add a platform adapter** — use the repo's own `/new-adapter` skill, and port from `legacy/` rather
than rewriting (CLAUDE.md rule 4).

Before any of these, read `docs/PRD.md` for the requirement, `docs/SYSTEM_DESIGN.md` for the
contract, `docs/UI_PLAN.md` for the screen, and `docs/PROGRESS.md` for where the build has got to.

---

## 10. When something breaks

| Symptom | First move |
|---|---|
| Anything at all | `make logs` — then `make ps` to see which container is unhealthy |
| `permission denied ... docker.sock` | `newgrp docker`, or log out and back in (see README) |
| API says `DATABASE_UNAVAILABLE` | The volume's password ≠ `infra/.env`. `make db-password`, or `make clean` to start fresh |
| Changed `infra/.env`, nothing changed | You ran `make restart`. Use `make up` — restart reuses the old environment |
| Locked out of login | `make unlock-login` |
| Frontend types don't match the API | `make types` (stack must be running) |
| Migration won't apply | Read the Alembic error; never edit an applied migration — add a new one |
| A run sits at "queued" | The worker is down or Redis is unreachable: `make logs` and look at `worker` |
| Everything is inexplicable | `make clean && make dev && make migrate` — local data is disposable |

Logs for one service: `docker compose -f infra/docker-compose.dev.yml --env-file infra/.env logs -f worker`.

---

## 11. A realistic two-week schedule

| Days | Focus | Done when you can |
|---|---|---|
| 1 | Make + this document + `make dev`, `make migrate`, click through the app | Start and stop the stack, read `make help` |
| 2–3 | Docker: images, containers, volumes, ports, bind mounts, Compose | Explain every service block in `docker-compose.dev.yml` |
| 4–5 | SQL basics, then SQLAlchemy models, then Alembic | Add a column end to end and migrate it |
| 6 | Redis + Dramatiq + scheduler; read `executor.py` | Say exactly what happens between "Run now" and a saved file |
| 7–8 | FastAPI + Pydantic; poke `/api/docs`; read one module's four files | Add an endpoint with an RBAC test |
| 9–11 | React + TypeScript + TanStack Query + Tailwind; read one feature folder | Change a screen and see it hot-reload |
| 12 | The end-to-end trace in §8, with every file open | Draw the diagram from memory |
| 13–14 | Playwright and one adapter (only if adapter work is coming) | Follow a login with `make watch` |

**Official docs, in the order you need them:** Docker "Get started" → Docker Compose file reference
→ PostgreSQL tutorial (Ch. 2 only) → SQLAlchemy 2.0 ORM Quick Start → Alembic tutorial → FastAPI
tutorial (first 10 pages) → Dramatiq motivation + actors → React "Learn React" (Describing/Adding
Interactivity) → TanStack Query "Quick Start" → Playwright "Writing tests". Skip anything about
Kubernetes, Docker Swarm, Django, Flask, Redux or `session.query()` — none is used here.

---

## 12. Glossary

**Image / container / volume** — installer / running program / disk that survives.
**Bind mount** — your source folder mounted live into a container; why edits hot-reload.
**Service** — one named container in the compose file.
**Healthcheck** — a command Docker runs repeatedly to decide if a container is healthy.
**Migration** — a versioned, replayable schema change (Alembic).
**ORM** — maps classes to tables (SQLAlchemy).
**Session** — a unit of database work, committed or rolled back.
**Actor / broker / queue** — a function runnable in the background / Redis / where messages wait.
**SSE** — Server-Sent Events: a one-way live stream from server to browser.
**OpenAPI schema** — machine-readable description of the API; the source of `api-types.ts`.
**RBAC** — role-based access control; here, which brands a user may see.
**Fernet** — the symmetric encryption used for stored secrets, keyed by `UNIQCAI_MASTER_KEY`.
**Adapter** — the per-portal Playwright code; the only place selectors and URLs may live.
**Xvfb** — a fake display so a visible browser can run without a monitor.
**Headed / headless** — browser with / without a visible window; this project runs headed on purpose.
