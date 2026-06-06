"""Deterministic enrichment helpers for normalized saved posts."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .clean import normalize_whitespace, strip_linkedin_ui_junk
from .schema import SavedPostRecord

SUMMARY_MAX_LENGTH = 180
SUMMARY_SOFT_LIMIT = 240
DEFAULT_THEME = "General / Other"

THEME_TAXONOMY: tuple[str, ...] = (
    "AI & Automation",
    "Data & Analytics",
    "Engineering & DevOps",
    "Product & Strategy",
    "Leadership & Management",
    "Career & Hiring",
    "Startups & Entrepreneurship",
    "Marketing & Growth",
    "Sales & Revenue",
    "Design & UX",
    "Finance & Investing",
    "Research & Science",
    "Writing & Communication",
    "Productivity & Operations",
    DEFAULT_THEME,
)


@dataclass(frozen=True, slots=True)
class _ThemeRule:
    theme: str
    terms: tuple[str, ...]
    role_terms: tuple[str, ...] = ()


_THEME_RULES: tuple[_ThemeRule, ...] = (
    _ThemeRule(
        "AI & Automation",
        terms=(
            "ai",
            "artificial intelligence",
            "machine learning",
            "ml",
            "llm",
            "large language model",
            "genai",
            "generative ai",
            "automation",
            "agent",
            "agentic",
            "prompt",
            "inference",
            "fine-tune",
            "foundation model",
        ),
        role_terms=("ai", "ml", "machine learning", "prompt engineer", "research scientist"),
    ),
    _ThemeRule(
        "Data & Analytics",
        terms=(
            "data",
            "analytics",
            "analysis",
            "analyst",
            "data science",
            "data scientist",
            "data engineering",
            "business intelligence",
            "dashboard",
            "metrics",
            "sql",
            "python",
            "experiment",
            "a/b test",
        ),
        role_terms=("data scientist", "analyst", "analytics", "bi", "data engineer"),
    ),
    _ThemeRule(
        "Engineering & DevOps",
        terms=(
            "engineer",
            "engineering",
            "software",
            "developer",
            "devops",
            "platform",
            "backend",
            "frontend",
            "infrastructure",
            "systems",
            "distributed systems",
            "api",
            "architecture",
            "kubernetes",
            "cloud",
        ),
        role_terms=("engineer", "developer", "cto", "tech lead", "staff engineer"),
    ),
    _ThemeRule(
        "Product & Strategy",
        terms=(
            "product",
            "strategy",
            "roadmap",
            "go-to-market",
            "gtm",
            "pm",
            "prioritization",
            "discovery",
            "pricing",
            "positioning",
            "metrics",
            "user story",
        ),
        role_terms=("product manager", "pm", "product", "strategy", "chief product officer"),
    ),
    _ThemeRule(
        "Leadership & Management",
        terms=(
            "leadership",
            "leader",
            "management",
            "manager",
            "executive",
            "ceo",
            "cfo",
            "vp",
            "director",
            "org",
            "culture",
            "coaching",
            "feedback",
        ),
        role_terms=("manager", "director", "vice president", "vp", "ceo", "founder", "lead"),
    ),
    _ThemeRule(
        "Career & Hiring",
        terms=(
            "career",
            "hiring",
            "recruiting",
            "recruiter",
            "talent",
            "interview",
            "interviewing",
            "resume",
            "cv",
            "job",
            "promotion",
            "salary",
            "compensation",
        ),
        role_terms=("recruiter", "talent", "hiring manager", "people ops", "hr"),
    ),
    _ThemeRule(
        "Startups & Entrepreneurship",
        terms=(
            "startup",
            "startups",
            "founder",
            "cofounder",
            "entrepreneur",
            "entrepreneurship",
            "venture",
            "bootstrapped",
            "bootstrap",
            "seed round",
            "series a",
            "series b",
            "product-market fit",
        ),
        role_terms=("founder", "cofounder", "entrepreneur", "startup", "venture"),
    ),
    _ThemeRule(
        "Marketing & Growth",
        terms=(
            "marketing",
            "growth",
            "brand",
            "branding",
            "demand gen",
            "demand generation",
            "content marketing",
            "community",
            "campaign",
            "social media",
            "seo",
            "distribution",
        ),
        role_terms=("marketer", "marketing", "growth", "brand", "demand gen"),
    ),
    _ThemeRule(
        "Sales & Revenue",
        terms=(
            "sales",
            "revenue",
            "pipeline",
            "account executive",
            "ae",
            "closing",
            "quota",
            "prospecting",
            "customer success",
            "crm",
            "deal",
        ),
        role_terms=("sales", "account executive", "customer success", "revops"),
    ),
    _ThemeRule(
        "Design & UX",
        terms=(
            "design",
            "designer",
            "ux",
            "ui",
            "product design",
            "research",
            "interaction design",
            "prototyping",
            "usability",
            "visual design",
            "accessibility",
        ),
        role_terms=("designer", "ux", "ui", "product design", "researcher"),
    ),
    _ThemeRule(
        "Finance & Investing",
        terms=(
            "finance",
            "financial",
            "investing",
            "investor",
            "venture capital",
            "vc",
            "valuation",
            "equity",
            "portfolio",
            "budget",
            "accounting",
            "cash flow",
        ),
        role_terms=("investor", "vc", "finance", "cfo", "analyst"),
    ),
    _ThemeRule(
        "Research & Science",
        terms=(
            "research",
            "scientist",
            "science",
            "academic",
            "paper",
            "study",
            "experiment",
            "evidence",
            "peer review",
            "methodology",
            "hypothesis",
        ),
        role_terms=("researcher", "scientist", "professor", "phd"),
    ),
    _ThemeRule(
        "Writing & Communication",
        terms=(
            "writing",
            "writer",
            "newsletter",
            "copywriting",
            "communication",
            "storytelling",
            "editing",
            "editor",
            "narrative",
            "publish",
            "blog",
        ),
        role_terms=("writer", "editor", "communications", "communication", "content"),
    ),
    _ThemeRule(
        "Productivity & Operations",
        terms=(
            "productivity",
            "operations",
            "ops",
            "workflow",
            "process",
            "systems",
            "checklist",
            "time management",
            "notes",
            "habits",
            "framework",
            "automation",
        ),
        role_terms=("ops", "operations", "chief of staff", "program manager"),
    ),
    _ThemeRule(DEFAULT_THEME, terms=()),
)


_SENTENCE_BOUNDARY_RE = re.compile(r"^(.+?[.!?])(?:\s|$)")
_CLAUSE_BOUNDARY_RE = re.compile(r"^(.+?)(?:\s?[—–-]\s+|:\s+|;\s+|\|\s+)")


def _as_mapping(record: Mapping[str, Any] | SavedPostRecord) -> Mapping[str, Any]:
    if isinstance(record, SavedPostRecord):
        return record.to_dict()
    return record


def _clean_field(value: Any) -> str:
    if value is None:
        return ""
    return normalize_whitespace(strip_linkedin_ui_junk(str(value)))


def _compile_term(term: str) -> re.Pattern[str]:
    escaped = re.escape(term)
    if re.fullmatch(r"[A-Za-z0-9]+", term):
        return re.compile(rf"\b{escaped}\b", re.IGNORECASE)
    return re.compile(escaped, re.IGNORECASE)


def _score_text(text: str, term: str) -> int:
    if not text:
        return 0
    pattern = _compile_term(term)
    return len(pattern.findall(text))


def _score_record_texts(data: Mapping[str, Any]) -> dict[str, float]:
    scores = {theme: 0.0 for theme in THEME_TAXONOMY}
    field_weights = (("text_clean", 1.25), ("text_raw", 1.0), ("summary", 1.1), ("author_role", 1.6))

    for field, weight in field_weights:
        text = _clean_field(data.get(field, ""))
        if not text:
            continue
        for rule in _THEME_RULES:
            if rule.theme == DEFAULT_THEME:
                continue
            for term in rule.terms:
                scores[rule.theme] += _score_text(text, term) * weight
            if field == "author_role":
                for term in rule.role_terms:
                    scores[rule.theme] += _score_text(text, term) * (weight + 0.5)

    return scores


def classify_theme(record: Mapping[str, Any] | SavedPostRecord) -> str:
    """Assign exactly one deterministic primary theme to a saved post."""

    data = _as_mapping(record)
    scores = _score_record_texts(data)
    best_theme = DEFAULT_THEME
    best_score = 0.0

    for theme in THEME_TAXONOMY:
        score = scores.get(theme, 0.0)
        if score > best_score:
            best_theme = theme
            best_score = score

    return best_theme


def _summary_from_text(text: str) -> str:
    cleaned = _clean_field(text)
    if not cleaned:
        return ""

    for regex in (_SENTENCE_BOUNDARY_RE, _CLAUSE_BOUNDARY_RE):
        match = regex.search(cleaned)
        if match:
            candidate = normalize_whitespace(match.group(1))
            if candidate:
                if len(candidate) <= SUMMARY_SOFT_LIMIT:
                    return candidate
                cleaned = candidate
                break

    if len(cleaned) <= SUMMARY_MAX_LENGTH:
        return cleaned

    snippet = cleaned[:SUMMARY_MAX_LENGTH].rstrip()
    cut = snippet.rfind(" ")
    if cut >= 80:
        snippet = snippet[:cut].rstrip()
    return snippet + ("…" if len(snippet) < len(cleaned) else "")


def summarize_record(record: Mapping[str, Any] | SavedPostRecord) -> str:
    """Build a short summary from the record text when summary is missing."""

    data = _as_mapping(record)
    existing = _clean_field(data.get("summary", ""))
    if existing:
        return existing

    for field in ("text_clean", "text_raw"):
        summary = _summary_from_text(str(data.get(field, "")))
        if summary:
            return summary
    return ""


def enrich_record(record: Mapping[str, Any] | SavedPostRecord) -> dict[str, Any]:
    """Return a normalized mapping with a deterministic theme and short summary."""

    data = dict(_as_mapping(record))
    if not _clean_field(data.get("summary", "")):
        data["summary"] = summarize_record(data)
    else:
        data["summary"] = _clean_field(data.get("summary", ""))
    data["theme_primary"] = classify_theme(data)
    return data
