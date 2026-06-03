"""
Fuzzy text → MCQ option matching (synonyms, partial phrases).
"""
from __future__ import annotations
import re
from typing import Optional

# Canonical value → accepted user phrases
VALUE_SYNONYMS: dict[str, list[str]] = {
    "morning": ["morning", "mornings", "morning time", "morning hours", "early morning", "am", "before noon"],
    "afternoon": ["afternoon", "afternoons", "afternoon time", "midday", "noon", "post lunch"],
    "evening": ["evening", "evenings", "evening time", "late", "after work"],
    "night": ["night", "night time", "late night"],
    "any": ["any", "anytime", "any time", "flexible", "whenever"],
    "immediate": ["immediate", "immediately", "asap", "urgent", "now", "right away"],
    "immediate_urgent": ["immediate", "urgent", "asap", "right away", "emergency"],
    "within_1m": ["within 1 month", "1 month", "one month", "30 days", "few weeks"],
    "1m": ["1 month", "one month", "30 days", "within a month"],
    "1_3m": ["1-3 months", "1 to 3 months", "2 months", "couple months"],
    "3_6m": ["3-6 months", "3 to 6 months", "few months", "half year"],
    "flexible": ["flexible", "no rush", "open", "not sure"],
    "high": ["very urgent", "urgent", "high", "asap", "critical"],
    "medium": ["moderate", "medium", "somewhat urgent"],
    "low": ["not urgent", "low", "no rush", "relaxed"],
    "apartment": ["apartment", "flat", "apt"],
    "villa": ["villa", "bungalow"],
    "independent_house": ["independent", "independent house", "house", "bungalow"],
    "below_5L": ["below 5", "under 5", "less than 5 lakh", "5l below"],
    "5_15L": ["5-15", "5 to 15", "5 lakh", "10 lakh", "below 15"],
    "interior": ["interior", "inside", "internal", "indoor"],
    "exterior": ["exterior", "outside", "external", "outdoor"],
    "new": ["new", "fresh", "from scratch"],
    "renovation": ["renovation", "renovate", "remodel", "makeover"],
    "yes": ["yes", "yep", "yeah", "correct", "ok", "okay", "sure"],
    "none": ["none", "no", "nothing", "n/a", "na", "not applicable"],
}


def _normalize(text: str) -> str:
    t = (text or "").strip().lower()
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _tokens(text: str) -> set[str]:
    return set(_normalize(text).split())


def match_mcq_option(user_text: str, options: list[dict]) -> Optional[dict]:
    """Match user message to an option by number, label, value, or synonyms."""
    raw = (user_text or "").strip()
    if not raw:
        return None
    lower = raw.lower()

    if lower.isdigit():
        idx = int(lower) - 1
        if 0 <= idx < len(options):
            return options[idx]

    for opt in options:
        label = str(opt.get("label", "")).lower()
        value = str(opt.get("value", "")).lower()
        if lower == label or lower == value:
            return opt
        if label and label in lower:
            return opt
        if value and value.replace("_", " ") in lower:
            return opt

    norm = _normalize(raw)
    user_toks = _tokens(raw)

    best: Optional[dict] = None
    best_score = 0

    for opt in options:
        value = str(opt.get("value", "")).lower()
        label = str(opt.get("label", "")).lower()
        candidates = {_normalize(label), _normalize(value.replace("_", " "))}
        for syn in VALUE_SYNONYMS.get(value, []):
            candidates.add(_normalize(syn))
        for phrase in candidates:
            if not phrase:
                continue
            if phrase == norm or phrase in norm or norm in phrase:
                return opt
            overlap = len(user_toks & _tokens(phrase))
            if overlap > best_score:
                best_score = overlap
                best = opt

    if best_score >= 1:
        return best
    return None
