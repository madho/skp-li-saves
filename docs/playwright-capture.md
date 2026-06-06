# Playwright capture runbook

Use this when you want a repeatable browser automation path for LinkedIn saved posts.

## Recommended setup

1. Install the package and browser binary:

```bash
pip install -e .
playwright install chromium
```

2. Decide on a persistent profile directory. A dedicated directory is simplest:

```bash
mkdir -p ~/.cache/skp-li-saves/playwright-profile
```

3. Run the capture command:

```bash
skp-li-saves-capture \
  --url https://www.linkedin.com/my-items/saved-posts/ \
  --profile-dir ~/.cache/skp-li-saves/playwright-profile \
  --output linkedin_saved_posts.json
```

## Reusing a logged-in browser session

- The profile directory is persistent, so you only need to log in once.
- If you want to point Playwright at a real Chrome profile directory, close Chrome first so the profile lock is released.
- You can switch to a different browser channel with `--browser-channel chrome` or `--browser-channel msedge` if that matches your local setup better; leaving it empty uses bundled Chromium.

## What the command does

- opens the saved-posts page in a logged-in browser session
- scrolls the feed repeatedly
- clicks any visible **Show more results** gate
- captures `data-chameleon-result-urn` and visible card text
- writes JSON that the existing normalization CLI already understands

## Fallback if Playwright is blocked

If the environment cannot install Playwright or launch a browser, use the browser-console helper in [`capture.md`](capture.md) instead. The HTML parser in `skp_li_saves.capture_playwright` also lets you parse a saved HTML snapshot offline with:

```bash
skp-li-saves-capture --html saved_snapshot.html --output linkedin_saved_posts.json
```
