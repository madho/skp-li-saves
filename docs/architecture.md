# Architecture for skp-li-saves

## Goal

Convert a user's LinkedIn Saved Posts page into a searchable, sortable library.

## Core constraints

- No LinkedIn API is assumed.
- Extraction must happen from the user's logged-in browser session.
- Outputs should be local-first and reproducible.
- The repo itself should remain safe for public GitHub hosting.

## Recommended pipeline

### 1. Capture

Use a browser automation session to:

- open LinkedIn saved posts
- scroll until the page stops loading new items
- click any "show more results" gates
- capture post DOM nodes and/or page network payloads

Preferred capture order:

1. network/XHR responses
2. DOM extraction fallback
3. page-state/script fallback

### 2. Normalize

Convert captured payloads into a canonical record shape.

Suggested fields:

- `post_id`
- `post_url`
- `author_name`
- `author_role`
- `published_at`
- `text_raw`
- `text_clean`
- `summary`
- `theme_primary`
- `theme_secondary`
- `source_type`
- `source_run_id`

### 3. Clean and dedupe

Perform:

- whitespace normalization
- UI-junk stripping
- URL canonicalization
- record deduplication by stable ID
- provenance retention for debugging

### 4. Theme assignment

Use a hybrid approach:

- deterministic rules for obvious categories
- taxonomy-based classification for consistency
- LLM fallback for low-confidence posts

Keep the taxonomy fixed so results remain stable across refreshes.

### 5. Export

Build three outputs:

- **HTML**: single-file, searchable, filterable, theme chips, localStorage state
- **XLSX**: one row per post, frozen header, autofilter, theme summary tab
- **JSONL/JSON**: machine-readable archive and reprocessing input

### 6. Storage

Use a small local database or file store as the source of truth.

Good options:

- SQLite with FTS
- DuckDB
- JSONL plus derived exports

## Repo layout suggestion

```text
skp-li-saves/
├── README.md
├── docs/
│   ├── architecture.md
│   └── gsd-plan.md
├── src/
│   ├── capture/
│   ├── normalize/
│   ├── themes/
│   ├── export/
│   └── cli/
├── tests/
├── data/
└── .github/
```

## Risks

- LinkedIn DOM changes
- infinite scroll / lazy loading quirks
- session expiry during extraction
- inconsistent theme labels
- accidental inclusion of private data in the public repo

## Mitigation

- fixture-based regression tests
- stable canonical schema
- local-first storage
- separate raw private data from public docs and code
- frequent QA passes before merging slices
