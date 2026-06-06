# GSD plan for skp-li-saves

## Goal

Build a programmatic pipeline for compiling LinkedIn Saved Posts into a usable library.

## Scope

- browser-based capture of saved posts from a logged-in LinkedIn session
- normalization and deduplication
- theme assignment and short summaries
- HTML and XLSX exports
- docs and tests that can live in a public repo

## Non-goals for the first slice

- bypassing LinkedIn access controls
- storing secrets in GitHub
- fully automated cloud refresh from public CI
- perfect taxonomy coverage on day one

## Recommended slice order

1. repo bootstrap and docs
2. capture prototype
3. parser/normalizer
4. theme classifier
5. HTML export
6. XLSX export
7. tests and fixtures
8. CI and release hygiene

## Acceptance criteria

- public GitHub repo exists
- repo contains the architecture and plan docs
- work is organized for a Claude implementation lane and Codex QA lane
- the repo is ready for code implementation without further setup

## QA approach

- review each slice before merging
- verify exports against fixtures
- keep raw/private data out of public files
- check that scripts and docs do not assume a LinkedIn API exists
