# LinkedIn Saved Posts capture options

This repo now supports two capture paths:

1. a **browser-console helper** for ad hoc extraction from a logged-in tab
2. a **Playwright-based capture command** that uses a persistent browser profile and writes JSON to disk

## 1) Browser-console helper

This is the lightweight, browser-local option.

### How it works

1. Open LinkedIn while logged in.
2. Navigate to the saved-posts page.
3. Paste the contents of [`scripts/linkedin_saved_posts_capture.js`](../scripts/linkedin_saved_posts_capture.js) into the DevTools console, or save it as a bookmarklet-style helper if you prefer.
4. Run:

```javascript
__runLinkedInSavedPostsCapture()
```

The helper will:

- scroll the page in real browser increments
- click any visible **Show more results** gates
- collect post URNs from `data-chameleon-result-urn`
- download a JSON file named `linkedin_saved_posts.json`

## 2) Playwright persistent-profile capture

This is the more automated path.

### Install prerequisites

```bash
pip install -e .
playwright install chromium
```

If you want to reuse a real Chrome login, point `--profile-dir` at a dedicated persistent profile directory and launch with `--browser-channel chrome`.

### Run it

```bash
skp-li-saves-capture \
  --url https://www.linkedin.com/my-items/saved-posts/ \
  --profile-dir ~/.cache/skp-li-saves/playwright-profile \
  --output linkedin_saved_posts.json
```

Useful flags:

- `--headless` runs the browser hidden
- `--max-scrolls` caps how long the scraper keeps scrolling
- `--settle-ms` and `--click-wait-ms` control timing for slow LinkedIn renders
- `--html path/to/snapshot.html` parses a saved HTML snapshot instead of opening a browser

### Output shape

The capture command writes an array of raw records shaped like this:

```json
[
  {
    "urn": "urn:li:activity:1234567890",
    "text": "full card text from LinkedIn"
  }
]
```

That JSON file can be fed directly into the repo's normalization CLI:

```bash
skp-li-saves linkedin_saved_posts.json --format html --enrich
skp-li-saves linkedin_saved_posts.json --format xlsx --enrich
```

## Notes

- The helper and the Playwright command are intentionally browser-local. They do not require LinkedIn API access.
- They use the visible page DOM, so if LinkedIn changes the markup, the capture logic may need a refresh.
- The repository's normalization, enrichment, HTML export, and XLSX export layers are designed to consume the JSON output from either capture path.
