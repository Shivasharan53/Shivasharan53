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

After merging the pull request, open **Settings → Secrets and variables →
Actions** and add a repository secret named `PROFILE_TOKEN`. Use a GitHub
personal access token with the `read:user` scope so the workflow can query
your contribution calendar through GraphQL. The workflow also needs the
repository's normal `GITHUB_TOKEN` write permission to commit refreshed cards.

Then open **Actions → Refresh animated profile cards → Run workflow** once.
After that, it runs daily at 00:17 UTC (05:47 IST) and commits the updated
`data/contributions.json` and SVG cards.

## Fonts and portrait

The current profile design uses the Arial-style typography already present
in the original SVG assets. The workflow installs Liberation Sans (an
Arial-metric-compatible open font), subsets it with `pyftsubset`, and embeds
the WOFF subset as a base64 data URI inside each SVG. To use a different
licensed font, place its TTF at `assets/fonts/profile.ttf`.

To add a portrait, set `portrait_url` in `cards_config.json` to a publicly
accessible image URL. Leave it empty to keep the abstract brand mark.