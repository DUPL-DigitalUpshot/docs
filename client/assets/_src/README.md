# How these SVGs are made

From this directory:

```
python3 diagrams.py    # ../*.svg          — the six explanatory diagrams
python3 screens.py     # ../screens/*.svg  — the fourteen interface previews
python3 client.py      # ../themes/*.svg   — four previews for the short page
```

- `common.py` holds the palette (copied from `docs/THEME.md`, both themes), the
  app-window chrome, the two renderers and the small drawing helpers.
- `screens.py` draws the previews. It is importable: the fourteen calls sit
  behind `if __name__ == "__main__"`, and `client.py` reuses four of them.

Four things to know before editing:

1. **Colour goes in `style="fill:…"`, never a `fill=` attribute.** The class
   rules in the shared `<style>` block have higher specificity than a
   presentation attribute and would silently win.
2. **Each SVG carries its own light and dark palette**, so a file embedded with
   `<img>` still answers the reader's OS preference. That is why the tokens are
   declared inside every file rather than inherited from the page.
3. **The two documents want different previews.** `FLOW.md` / `flow.html` show
   each screen once, with a `Built` or `Designed — not yet built` corner badge.
   `OVERVIEW.md` / `overview.html` show four screens with **no badge at all**,
   stacked light over dark. `client.py` sets `screens.BADGE`, `screens.MODE`
   and `screens.OUTDIR` to get the second form out of the same drawing code —
   so a change to a screen reaches both documents.
4. **The brand names are invented.** Northwind Foods, Saffron Kitchen and
   Bluepeak Drinks are placeholders. No real client brand, login or inbox from
   `samples/` appears in any of these files, and none should be added.

On why the themed previews are stacked rather than side by side: two half-width
copies scale the 12.5px interface text under 7px, and splitting one image down
the middle leaves the dark half nearly empty, because these screens carry their
content on the left. Stacking keeps both copies full size.
