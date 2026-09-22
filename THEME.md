# UniQCAI — Theme

Version 0.1 · 21 Sep 2026

> **STATUS: PROVISIONAL BRAND COLOURS.** The Digital Upshot logo has not been received yet.
> Everything in this file is final **except the `--brand-*` ramp and the logo section**.
> Those get replaced from the logo, and nothing else changes, because every component reads from tokens.

---

## 1. Personality

An operations console used daily by an agency team, and occasionally by clients.
**Calm, dense, trustworthy.** Colour is used for *status* and *brand accents*, not decoration. Neutral surfaces dominate, the brand colour marks primary actions and navigation, and red/amber/green are reserved for state.

## 2. Brand colour (to be derived from the logo)

Derivation method once the logo arrives:
1. Sample the logo's primary colour. It becomes `--brand-600` (buttons, active nav).
2. Generate a 50–950 ramp in OKLCH (same hue, stepped lightness), checking that `--brand-600` on white reaches ≥ 4.5:1 contrast. If the logo colour is too light (e.g. a yellow or orange), use it for accents and pick a darker step for buttons.
3. If the logo has a secondary colour, it becomes `--accent-*`, used sparingly (charts, highlights).

Provisional ramp (a neutral deep blue, safe to build against):

```css
--brand-50:  #eef3ff;
--brand-100: #dbe5ff;
--brand-200: #b9ccff;
--brand-300: #8eaaff;
--brand-400: #5f80f7;
--brand-500: #3d5ce8;
--brand-600: #2a45cc;   /* primary actions */
--brand-700: #2237a3;
--brand-800: #1f3183;
--brand-900: #1d2c69;
--brand-950: #131b40;
```

## 3. Neutrals (final)

A slightly cool slate so data tables read cleanly.

```css
--gray-0:   #ffffff;
--gray-25:  #fafbfc;
--gray-50:  #f4f6f8;
--gray-100: #eceff3;
--gray-200: #dde2e8;
--gray-300: #c4ccd5;
--gray-400: #97a2af;
--gray-500: #6b7684;
--gray-600: #4f5967;
--gray-700: #3a424e;
--gray-800: #262c35;
--gray-900: #171b21;
--gray-950: #0d1014;
```

## 4. Semantic tokens (final)

Components only ever use these, never raw ramps.

```css
:root {
  /* surfaces */
  --bg-app:        var(--gray-25);
  --bg-surface:    var(--gray-0);
  --bg-subtle:     var(--gray-50);
  --bg-sidebar:    var(--gray-950);
  --border:        var(--gray-200);
  --border-strong: var(--gray-300);

  /* text */
  --text:          var(--gray-900);
  --text-muted:    var(--gray-600);   /* gray-500 failed AA on --bg-app and --bg-subtle */
  --text-inverse:  var(--gray-0);
  --text-link:     var(--brand-600);

  /* brand */
  --primary:        var(--brand-600);
  --primary-hover:  var(--brand-700);
  --primary-soft:   var(--brand-50);
  --focus-ring:     var(--brand-400);

  /* feedback */
  --success: #15803d;  --success-soft: #dcfce7;
  --warning: #b45309;  --warning-soft: #fef3c7;
  --danger:  #b91c1c;  --danger-soft:  #fee2e2;
  --info:    #0369a1;  --info-soft:    #e0f2fe;
}

[data-theme="dark"] {
  --bg-app:        var(--gray-950);
  --bg-surface:    var(--gray-900);
  --bg-subtle:     var(--gray-800);
  --bg-sidebar:    #080a0d;
  --border:        var(--gray-800);
  --border-strong: var(--gray-700);
  --text:          var(--gray-50);
  --text-muted:    var(--gray-400);
  --text-link:     var(--brand-300);
  --primary:       var(--brand-500);
  --primary-hover: var(--brand-400);
  --primary-soft:  color-mix(in oklab, var(--brand-500) 18%, transparent);

  /* Feedback foregrounds are lightened for dark surfaces. The light-mode
     values on these soft backgrounds land at about 2.3:1 — well under AA. */
  --success: #4ade80;  --success-soft: #052e16;
  --warning: #fbbf24;  --warning-soft: #451a03;
  --danger:  #f87171;  --danger-soft:  #450a0a;
  --info:    #38bdf8;  --info-soft:    #082f49;
}
```

## 5. Status colours (final)

Used by `StatusBadge` and `HealthDot`. Every status also has an icon, so colour is never the only signal.

| Status | Light — text / bg | Dark — text / bg | Icon |
|---|---|---|---|
| queued | `--gray-600` / `--gray-100` | `--gray-300` / `--gray-800` | clock |
| running | `--info` / `--info-soft` | same tokens | spinner |
| awaiting_otp | `#7c3aed` / `#ede9fe` | `#a78bfa` / `#2e1065` | mail |
| succeeded | `--success` / `--success-soft` | same tokens | check |
| partial | `--warning` / `--warning-soft` | same tokens | half-circle |
| failed | `--danger` / `--danger-soft` | same tokens | x |
| cancelled | `--gray-600` / `--gray-50` | `--gray-400` / `--gray-800` | slash |
| **Health:** healthy / needs attention / untested / not connected | success / warning / gray-400 outline / gray-300 dash | | dot |

The four semantic rows read "same tokens" because `--success`, `--warning`, `--danger` and `--info` are themselves redefined for dark mode in §4. Only the three that are not — queued, awaiting_otp and cancelled — need a value here.

**Every pair above reaches WCAG AA (≥ 4.5:1) in both themes.** The greys used to fail: `--gray-500` on `--gray-100` is 4.00:1, and cancelled's `--gray-400` on `--gray-100` is 2.25:1. Cancelled stays the quieter of the two — a fainter chip in light, dimmer text in dark — but by a margin that no longer costs legibility.

`frontend/src/theme/contrast.test.ts` recomputes every pair from `tokens.css` and fails the build if a change drops one below 4.5:1, so this table cannot drift out of date silently.

## 6. Platform chips (final, approximate platform colours)

Used only in `PlatformChip` (a small colour dot + text label), so a portal is recognisable at a glance. Colours approximate each platform's public brand; no platform logos are reproduced.

| Platform | Dot colour |
|---|---|
| Zepto | `#5b21b6` |
| Blinkit | `#f5c518` (with dark text), secondary `#0c831f` |
| Swiggy Instamart | `#fc8019` |
| Flipkart Minutes | `#2874f0` |
| BigBasket | `#84c225` |

The category is shown as a text suffix: `Blinkit · Ads`, `Blinkit · Sales`. Portal names (Seller, Brand Central) are not used in the UI chrome.

## 7. Typography

```css
--font-sans: "Inter", ui-sans-serif, system-ui, "Segoe UI", sans-serif;
--font-mono: "JetBrains Mono", ui-monospace, "SFMono-Regular", monospace;
```
Load via Google Fonts or self-host. Enable `font-variant-numeric: tabular-nums` on all tables and metrics, so numbers line up.

| Token | Size / line-height | Weight | Use |
|---|---|---|---|
| `display` | 28 / 36 | 600 | Overview KPI numbers |
| `h1` | 22 / 30 | 600 | Page titles |
| `h2` | 17 / 26 | 600 | Section titles, card titles |
| `body` | 14 / 22 | 400 | Default |
| `body-strong` | 14 / 22 | 500 | Table emphasis, labels |
| `small` | 12.5 / 18 | 400 | Meta, timestamps, helper text |
| `mono` | 12.5 / 18 | 400 | Run logs, error codes, IDs |

## 8. Spacing, radius, elevation

```css
/* 4px base */
--space-1: 4px;  --space-2: 8px;  --space-3: 12px; --space-4: 16px;
--space-5: 20px; --space-6: 24px; --space-8: 32px; --space-10: 40px;

--radius-sm: 6px;   /* inputs, badges */
--radius-md: 8px;   /* buttons, cards */
--radius-lg: 12px;  /* drawers, modals */
--radius-full: 999px;

--shadow-sm: 0 1px 2px rgb(16 24 40 / 0.06);
--shadow-md: 0 4px 12px rgb(16 24 40 / 0.08);
--shadow-lg: 0 12px 32px rgb(16 24 40 / 0.14);  /* drawers, modals only */
```
Layout: sidebar 240px (collapsible to 64px), content max-width 1440px, page padding 24px. Table row height 44px (comfortable) / 36px (compact toggle).

## 9. Component guidance

- **Buttons:** Primary is `--primary` fill with white text, one per view. Secondary is surface with border. Ghost is used in tables. Destructive is `--danger` and always confirmed.
- **Sidebar:** dark (`--bg-sidebar`), active item uses a `--primary` left bar and a lighter background. The logo sits at the top.
- **Cards:** `--bg-surface`, 1px `--border`, `--radius-md`, `--shadow-sm`.
- **Tables:** sticky header on `--bg-subtle`, zebra off, row hover `--bg-subtle`, numbers right-aligned.
- **StepTimeline:** 20px icons in status colours, a connecting 1px line, elapsed time right-aligned in `mono`. The running step pulses gently (respect `prefers-reduced-motion`).
- **Focus:** 2px `--focus-ring` outline with 2px offset on every interactive element.
- **Motion:** 150ms ease-out for hovers, 200ms for drawers. Nothing decorative.

## 10. Tailwind mapping

```js
// tailwind.config.js (excerpt)
theme: {
  extend: {
    colors: {
      brand: { 50:'var(--brand-50)', 100:'var(--brand-100)', /* … */ 950:'var(--brand-950)' },
      primary: 'var(--primary)', 'primary-hover': 'var(--primary-hover)',
      surface: 'var(--bg-surface)', subtle: 'var(--bg-subtle)', app: 'var(--bg-app)',
      border: 'var(--border)', muted: 'var(--text-muted)',
      success: 'var(--success)', warning: 'var(--warning)',
      danger: 'var(--danger)', info: 'var(--info)',
    },
    fontFamily: { sans: ['var(--font-sans)'], mono: ['var(--font-mono)'] },
    borderRadius: { sm: 'var(--radius-sm)', md: 'var(--radius-md)', lg: 'var(--radius-lg)' },
  },
},
darkMode: ['class', '[data-theme="dark"]'],
```

## 11. Logo usage (to be completed with the logo)

- Sidebar: logo on dark background, so a light/white variant is needed. Confirm whether Digital Upshot has one.
- Login page: full logo centred above the form. Product name "UniQCAI", with "by Digital Upshot" beneath.
- Favicon: logo mark only.
- Brand (client) logos, e.g. Del Monte, appear only as small avatars on brand cards and the SPOC home, never in the app chrome.
