# skp-li-saves

A local-first, programmatic LinkedIn Saved Posts compiler.

This repo captures the plan and bootstrap for turning a user's LinkedIn saved posts into a searchable, sortable library with:

- one-file HTML browsing experience
- XLSX export with filters and theme counts
- incremental refreshes from a logged-in browser session

## Why this exists

LinkedIn exposes saved posts in the browser, but not as a usable library. The goal here is to:

1. extract saved-post content from a logged-in browser session
2. normalize and dedupe the data
3. assign stable themes and summaries
4. export the result into HTML, spreadsheet, and machine-readable formats

## Working approach

The recommended implementation follows a GSD workflow with two lanes:

- **Claude lane**: research, browser behavior analysis, extraction strategy, taxonomy design, docs
- **Codex lane**: implementation, tests, exports, QA, and security checks

This mirrors the `agents-army-claude-codex-gsd` workflow.

## Initial architecture

See [`docs/architecture.md`](docs/architecture.md).

## Initial implementation plan

See [`docs/gsd-plan.md`](docs/gsd-plan.md).

## Notes

- No LinkedIn API is assumed.
- The pipeline should remain local-first and user-session-driven.
- Public repo contents should avoid secrets, cookies, or private export data.
- Pass `--enrich` to apply deterministic theme classification and lightweight summary generation before JSONL, HTML, or XLSX export.
- See [`docs/capture.md`](docs/capture.md) for the browser-console capture helper.
