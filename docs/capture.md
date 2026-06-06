# LinkedIn Saved Posts capture helper

This repo now includes a browser-console helper for extracting saved posts from the LinkedIn saved-posts page.

## How it works

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

## Output shape

The downloaded file is an array of objects:

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

- The helper is intentionally browser-local. It does not require LinkedIn API access.
- It uses the visible page DOM, so if LinkedIn changes the markup, the helper may need a refresh.
- The repository's normalization, enrichment, HTML export, and XLSX export layers are designed to consume this JSON output.
