# BigBasket — port reference

**On hold.** No portal key assigned yet; `rpa/adapters/bigbasket/` comes later.
There is no working prototype — only a login skeleton and a saved page.

Sources: `legacy/bigbasket/adapters/bigbasket/bootstrap_login.py`,
`run_headless.py`, `BigBasket Ops.html`, `multi-platform-plan.md`.

## What exists

Two files, and `bootstrap_login.py` still carries
`LOGIN_URL = "https://<bigbasket>.osmos.ai/login"` with a `TODO: fill in from
the live portal`. So the host itself is unconfirmed. It is an **Osmos-hosted
SPA**, and sign-in is **Google**, not a portal-native form.

## Why it matters anyway: the bootstrap pattern

BigBasket is the only prototype that solves *interactive* sign-in, and it is the
pattern for **any Google login**:

1. A human signs in **once**, by hand, watching a real browser.
2. The session is saved — a persistent profile **and** `storage_state`.
3. Every run afterwards reuses it headlessly, with no human.

Two details are deliberate:

- **`channel="chrome"`** — real Chrome, not bundled Chromium, because *"Google
  is far friendlier to it"*. Nothing else in the workspace does this.
- Viewport 1440×900, `--disable-blink-features=AutomationControlled`.

## It is also where our live viewer came from

The docstring is the origin of `UNIQCAI_BROWSER_VIEW`:

```
Xvfb :99 -screen 0 1440x900x24 &
x11vnc -display :99 -localhost -rfbport 5900 -nopw -forever &
DISPLAY=:99 python adapters/bigbasket/bootstrap_login.py
```

viewed over `ssh -L 5900:localhost:5900`. That recipe is now ported into the
worker image and `make watch` — see `docs/DECISIONS.md`, 2026-09-22.

## What a port would need first

- The real portal host and login route.
- Whether Google sign-in can be re-driven unattended at all, or whether a human
  bootstrap is permanently required — which would make BigBasket the first
  platform needing an explicit "re-authenticate by hand" operator flow, and a
  UI for it.
- The report catalogue: nothing is captured. `BigBasket Ops.html` is one saved
  page, not a schema.

Until those are answered there is nothing to port. Treat this file as a
placeholder that records *why* the bootstrap pattern is worth keeping.
