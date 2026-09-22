# -*- coding: utf-8 -*-
"""The four screens used by the short client page (`overview.html`).

Same drawings as the walkthrough's previews, with two differences that are the
whole point of this file:

  * no corner status badge — the short page says nothing about what is built;
  * stacked light over dark, so one image shows both themes with neither
    copy shrunk below readable size.
"""
import os

import screens
from common import OUT

THEMES = os.path.join(OUT, "themes")
os.makedirs(THEMES, exist_ok=True)

screens.BADGE = False
screens.MODE = "stack"
screens.OUTDIR = THEMES

FOUR = (screens.wizard_4, screens.live_run, screens.library, screens.spoc)

if __name__ == "__main__":
    for fn in FOUR:
        fn()
