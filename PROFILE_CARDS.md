# Animated profile cards

The profile README is built from SVG images in `cards/`. The renderer is
`scripts/render_cards.py`; edit profile text, colours, links and featured
repositories in `cards_config.json`.

## Preview before publishing

Run this from the repository root:

```bash
STATIC=1 python scripts/render_cards.py
```

`STATIC=1` writes the final frame without CSS animation, which is useful for
screenshots. Run without `STATIC=1` to create the animated SVG cards.

## Daily contribution refresh

The workflow uses the repository's `GITHUB_TOKEN` to query the public
contribution calendar through GitHub GraphQL. The initial run has already
completed successfully, fetched 365 daily records and rendered all nine cards.
No additional token or secret is required for the current setup.

The workflow runs daily at 00:17 UTC (05:47 IST). You can also run it manually
from **Actions → Refresh animated profile cards → Run workflow**.

## Fonts and portrait

The current profile design keeps the Arial-style typography used by the
original SVG assets. The workflow installs Liberation Sans, an
Arial-metric-compatible open font, subsets it with `pyftsubset`, and embeds
the WOFF subset as a base64 data URI inside each SVG. To use a different
licensed font, place its TTF at `assets/fonts/profile.ttf`.

To add a portrait, set `portrait_url` in `cards_config.json` to a publicly
accessible image URL. Leave it empty to keep the abstract brand mark.
