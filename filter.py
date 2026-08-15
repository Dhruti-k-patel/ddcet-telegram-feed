"""Relevance filtering + summarising of notices."""

import re

from config import (
    ANTHROPIC_API_KEY,
    ENGINEERING_ONLY,
    ENGINEERING_TERMS,
    EXCLUDE_KEYWORDS,
    INCLUDE_KEYWORDS,
    PHARMACY_TERMS,
    STRONG_KEYWORDS,
)


def is_relevant(title, strict=False):
    """
    True if the notice looks DDCET / diploma-to-degree relevant.

    strict=True (used for noisy sources like GTU) requires a STRONG DDCET term;
    generic words like "result" or "admission" are not enough.
    """
    text = title.lower()

    # Engineering-only: drop pharmacy-specific notices (unless they also name
    # engineering). Runs before everything, so it overrides strong keywords.
    if ENGINEERING_ONLY:
        has_pharm = any(k in text for k in PHARMACY_TERMS)
        has_eng = any(k in text for k in ENGINEERING_TERMS)
        if has_pharm and not has_eng:
            return False

    has_strong = any(k in text for k in STRONG_KEYWORDS)
    if strict:
        return has_strong
    if has_strong:
        return True

    has_include = any(k in text for k in INCLUDE_KEYWORDS)
    if not has_include:
        return False

    # Included but also matches an exclude term (and no strong term) -> drop.
    has_exclude = any(k in text for k in EXCLUDE_KEYWORDS)
    return not has_exclude


# ---------------------------------------------------------------------------
# Summarising
# ---------------------------------------------------------------------------
_DATE_RE = re.compile(
    r"\b(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}"
    r"|\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"
    r"|last date[^.]*|deadline[^.]*)\b",
    re.IGNORECASE,
)


def _rule_based_summary(title):
    """Free summary: the notice text plus any dates/deadlines it mentions."""
    dates = _DATE_RE.findall(title)
    dates = [d.strip() for d in dates if d and d.strip()]
    if dates:
        uniq = list(dict.fromkeys(dates))
        return "📅 Key dates: " + "; ".join(uniq[:3])
    return ""


def _claude_summary(title):
    """Optional AI summary via Anthropic API (used only if a key is set)."""
    try:
        import anthropic
    except ImportError:
        return ""
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=120,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Summarise this DDCET / diploma-to-degree engineering "
                        "admission notice for students in ONE short plain-English "
                        "line. Keep any dates/deadlines. No preamble.\n\n"
                        f"Notice: {title}"
                    ),
                }
            ],
        )
        return msg.content[0].text.strip()
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] Claude summary failed: {exc}")
        return ""


def summarise(title):
    """Return a short extra line to add under the notice, or ''."""
    if ANTHROPIC_API_KEY:
        s = _claude_summary(title)
        if s:
            return s
    return _rule_based_summary(title)
