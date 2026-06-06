"""HTML export for normalized saved posts."""

from __future__ import annotations

import html
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .export_common import record_to_export_dict


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: light dark;
      --bg: #0f172a;
      --panel: #111827;
      --panel-2: #1f2937;
      --text: #e5e7eb;
      --muted: #9ca3af;
      --accent: #60a5fa;
      --accent-2: #22c55e;
      --border: rgba(148, 163, 184, 0.24);
    }}
    html, body {{ margin: 0; padding: 0; background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    body {{ padding: 24px; }}
    .app {{ max-width: 1200px; margin: 0 auto; }}
    header {{ display: grid; gap: 12px; margin-bottom: 20px; }}
    h1 {{ margin: 0; font-size: clamp(1.6rem, 3vw, 2.4rem); }}
    .meta {{ color: var(--muted); }}
    .toolbar {{ display: grid; gap: 12px; grid-template-columns: 1fr; }}
    .row {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
    input[type="search"], select {{ background: var(--panel); color: var(--text); border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; font: inherit; }}
    input[type="search"] {{ min-width: min(100%, 520px); flex: 1 1 320px; }}
    .chip {{ border: 1px solid var(--border); border-radius: 999px; padding: 8px 12px; background: var(--panel); color: var(--text); cursor: pointer; }}
    .chip[aria-pressed="true"] {{ background: var(--accent); color: #08111f; border-color: var(--accent); }}
    .chip:hover {{ border-color: var(--accent); }}
    .results {{ display: grid; gap: 16px; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }}
    .card {{ border: 1px solid var(--border); border-radius: 16px; background: linear-gradient(180deg, rgba(255,255,255,0.03), transparent), var(--panel); padding: 16px; display: grid; gap: 12px; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15); }}
    .card h2 {{ margin: 0; font-size: 1.05rem; line-height: 1.3; }}
    .card .subtle {{ color: var(--muted); font-size: 0.95rem; }}
    .themes {{ display: flex; gap: 6px; flex-wrap: wrap; }}
    .theme {{ border-radius: 999px; background: var(--panel-2); padding: 4px 10px; font-size: 0.85rem; color: var(--text); }}
    .summary {{ font-weight: 600; }}
    .excerpt {{ white-space: pre-wrap; color: #cbd5e1; line-height: 1.5; margin: 0; }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .footer {{ margin-top: 18px; color: var(--muted); }}
    .empty {{ padding: 32px; border: 1px dashed var(--border); border-radius: 16px; color: var(--muted); text-align: center; }}
  </style>
</head>
<body>
  <div class="app">
    <header>
      <div>
        <h1>{title}</h1>
        <div class="meta" id="result-meta">Loading…</div>
      </div>
      <div class="toolbar">
        <div class="row">
          <input id="search" type="search" placeholder="Search author, role, summary, or text" autocomplete="off">
          <select id="sort">
            <option value="recency">Sort: recency</option>
            <option value="author">Sort: author</option>
            <option value="theme">Sort: theme</option>
          </select>
        </div>
        <div class="row" id="theme-filters" aria-label="Theme filters"></div>
      </div>
    </header>
    <main>
      <section id="cards" class="results" aria-live="polite"></section>
      <div id="empty" class="empty" hidden>No saved posts match the current filters.</div>
    </main>
    <div class="footer">State is stored locally in your browser via localStorage.</div>
  </div>

  <script id="saved-posts-data" type="application/json">{json_data}</script>
  <script>
    const STORAGE_KEYS = {{
      search: 'skpLiSaves.search',
      theme: 'skpLiSaves.theme',
      sort: 'skpLiSaves.sort',
    }};

    const rawData = document.getElementById('saved-posts-data').textContent;
    const records = JSON.parse(rawData);
    const cards = document.getElementById('cards');
    const empty = document.getElementById('empty');
    const resultMeta = document.getElementById('result-meta');
    const searchInput = document.getElementById('search');
    const sortSelect = document.getElementById('sort');
    const themeFilters = document.getElementById('theme-filters');

    const uniqueThemes = Array.from(new Set(records.flatMap((record) => [record.theme_primary, record.theme_secondary].filter(Boolean)))).sort((a, b) => a.localeCompare(b));

    function readStorage(key, fallback) {{
      try {{
        return localStorage.getItem(key) ?? fallback;
      }} catch (error) {{
        return fallback;
      }}
    }}

    function writeStorage(key, value) {{
      try {{
        localStorage.setItem(key, value);
      }} catch (error) {{
        // Ignore storage failures.
      }}
    }}

    function formatDate(value) {{
      if (!value) return '';
      const parsed = new Date(value);
      if (Number.isNaN(parsed.getTime())) return value;
      return parsed.toLocaleString(undefined, {{ dateStyle: 'medium', timeStyle: 'short' }});
    }}

    function excerptFor(record) {{
      const text = (record.text_clean || record.text_raw || '').trim();
      if (!text) return '';
      return text.length > 280 ? `${{text.slice(0, 280).trimEnd()}}…` : text;
    }}

    function searchableText(record) {{
      return [record.author_name, record.author_role, record.summary, record.text_clean, record.text_raw].filter(Boolean).join(' ').toLowerCase();
    }}

    function themeFor(record) {{
      return record.theme_primary || record.theme_secondary || '';
    }}

    function timestamp(value) {{
      const parsed = Date.parse(value || '');
      return Number.isNaN(parsed) ? 0 : parsed;
    }}

    function sortRecords(items, sortMode) {{
      const cloned = [...items];
      if (sortMode === 'author') {{
        cloned.sort((a, b) => (a.author_name || '').localeCompare(b.author_name || '') || (timestamp(b.published_at) - timestamp(a.published_at)));
        return cloned;
      }}
      if (sortMode === 'theme') {{
        cloned.sort((a, b) => (themeFor(a) || '').localeCompare(themeFor(b) || '') || (a.author_name || '').localeCompare(b.author_name || ''));
        return cloned;
      }}
      cloned.sort((a, b) => timestamp(b.published_at) - timestamp(a.published_at) || (a.author_name || '').localeCompare(b.author_name || ''));
      return cloned;
    }}

    function renderThemeButtons(selectedTheme) {{
      themeFilters.innerHTML = '';
      const allButton = document.createElement('button');
      allButton.type = 'button';
      allButton.className = 'chip';
      allButton.textContent = 'All themes';
      allButton.setAttribute('aria-pressed', selectedTheme ? 'false' : 'true');
      allButton.addEventListener('click', () => {{
        writeStorage(STORAGE_KEYS.theme, '');
        render();
      }});
      themeFilters.appendChild(allButton);

      for (const theme of uniqueThemes) {{
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'chip';
        button.textContent = theme;
        button.setAttribute('aria-pressed', selectedTheme === theme ? 'true' : 'false');
        button.addEventListener('click', () => {{
          writeStorage(STORAGE_KEYS.theme, selectedTheme === theme ? '' : theme);
          render();
        }});
        themeFilters.appendChild(button);
      }}
    }}

    function renderCard(record) {{
      const article = document.createElement('article');
      article.className = 'card';

      const title = document.createElement('h2');
      title.textContent = record.author_name || 'Unknown author';
      article.appendChild(title);

      const sub = document.createElement('div');
      sub.className = 'subtle';
      sub.textContent = [record.author_role, formatDate(record.published_at)].filter(Boolean).join(' • ');
      article.appendChild(sub);

      const themes = [record.theme_primary, record.theme_secondary].filter(Boolean);
      if (themes.length) {{
        const themeWrap = document.createElement('div');
        themeWrap.className = 'themes';
        for (const theme of themes) {{
          const span = document.createElement('span');
          span.className = 'theme';
          span.textContent = theme;
          themeWrap.appendChild(span);
        }}
        article.appendChild(themeWrap);
      }}

      if (record.summary) {{
        const summary = document.createElement('div');
        summary.className = 'summary';
        summary.textContent = record.summary;
        article.appendChild(summary);
      }}

      const excerpt = document.createElement('p');
      excerpt.className = 'excerpt';
      excerpt.textContent = excerptFor(record);
      article.appendChild(excerpt);

      if (record.post_url) {{
        const link = document.createElement('a');
        link.href = record.post_url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.textContent = 'Open on LinkedIn';
        article.appendChild(link);
      }}

      return article;
    }}

    function render() {{
      const search = searchInput.value.trim().toLowerCase();
      const selectedTheme = readStorage(STORAGE_KEYS.theme, '');
      const sortMode = sortSelect.value;
      writeStorage(STORAGE_KEYS.search, searchInput.value);
      writeStorage(STORAGE_KEYS.sort, sortMode);

      renderThemeButtons(selectedTheme);

      let filtered = records.filter((record) => {{
        const matchesSearch = !search || searchableText(record).includes(search);
        const matchesTheme = !selectedTheme || [record.theme_primary, record.theme_secondary].filter(Boolean).includes(selectedTheme);
        return matchesSearch && matchesTheme;
      }});

      filtered = sortRecords(filtered, sortMode);
      cards.innerHTML = '';

      for (const record of filtered) {{
        cards.appendChild(renderCard(record));
      }}

      empty.hidden = filtered.length !== 0;
      resultMeta.textContent = `${{filtered.length}} of ${{records.length}} posts shown${{selectedTheme ? ` · theme: ${{selectedTheme}}` : ''}}`;
    }}

    searchInput.value = readStorage(STORAGE_KEYS.search, '');
    sortSelect.value = readStorage(STORAGE_KEYS.sort, 'recency');
    searchInput.addEventListener('input', render);
    sortSelect.addEventListener('change', render);
    render();
  </script>
</body>
</html>
"""


def render_html(records: Iterable[dict[str, Any]], *, title: str = "LinkedIn Saved Posts") -> str:
    """Render a single-file HTML library for saved posts."""

    normalized = [record_to_export_dict(record) for record in records]
    json_data = json.dumps(normalized, ensure_ascii=False)
    json_data = json_data.replace("</", "<\\/")
    return HTML_TEMPLATE.format(title=html.escape(title), json_data=json_data)


def export_html(records: Iterable[dict[str, Any]], output_path: Path, *, title: str = "LinkedIn Saved Posts") -> Path:
    """Write a single-file HTML library to *output_path*."""

    output_path.write_text(render_html(records, title=title), encoding="utf-8")
    return output_path
