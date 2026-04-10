"""
src/processors/keyword_filter.py
─────────────────────────────────
Fast keyword-based pre-filter. Runs before any DB insert to discard
articles that are clearly not disaster-related.

Usage:
    from src.processors.keyword_filter import is_disaster_related

    if is_disaster_related(title, description):
        # proceed to normalise + insert
"""

import re

# ── Master keyword set ────────────────────────────────────────────────────────
# Covers all disaster types tracked by GeoPulse.
# Keep lowercase — text is lowercased before matching.

DISASTER_KEYWORDS: set[str] = {
    # Flood / water
    "flood", "flooding", "floods", "inundation", "waterlogging", "cloudburst",
    "flash flood", "river overflow", "dam break", "dam burst", "deluge",
    "submerged", "swollen river",

    # Earthquake / tremor
    "earthquake", "quake", "tremor", "seismic", "aftershock", "richter",
    "magnitude", "epicentre", "epicenter",

    # Cyclone / storm / wind
    "cyclone", "hurricane", "typhoon", "storm", "superstorm", "tornado",
    "gale", "windstorm", "squall", "low pressure", "depression", "landfall",
    "storm surge",

    # Landslide / mudslide
    "landslide", "mud slide", "mudslide", "rockfall", "rock slide",
    "slope failure", "debris flow", "avalanche",

    # Heatwave / cold
    "heatwave", "heat wave", "extreme heat", "scorching", "severe cold",
    "cold wave", "frost", "snowstorm", "blizzard",

    # Fire
    "wildfire", "forest fire", "bushfire", "fire breaks out", "fire breaks",
    "building collapse", "structure fire", "fire accident",

    # Tsunami
    "tsunami", "tidal wave", "sea wave", "seawave",

    # Industrial / man-made
    "explosion", "blast", "gas leak", "chemical spill", "oil spill",
    "factory fire", "boiler explosion", "mine collapse", "building collapses",

    # Drought / shortage
    "drought", "severe drought", "water crisis", "crop failure",

    # General disaster language
    "disaster", "calamity", "catastrophe", "emergency", "evacuation",
    "evacuate", "rescue", "stranded", "casualties", "deaths", "killed",
    "missing", "injured", "relief camp", "ndrf", "sdrf", "ndma",
    "red alert", "orange alert", "yellow alert", "state of emergency",
    "disruption", "alert issued", "warning issued",
}

# ── Negative keywords (Metaphor / False Positive catchers) ────────────────────
# If any of these are present, we drop the article even if it has disaster words.
# This prunes out financial "crashes", political "storms", or box-office "disasters".

NEGATIVE_KEYWORDS: set[str] = {
    # Financial / Markets
    "share market", "stock market", "box office", "sensex", "nifty",
    "wall street", "trading", "investor", "dividend", "yield",
    
    # Politics / Metaphors
    "political storm", "storm in a teacup", "fashion disaster", 
    "election", "poll violence", "campaign", "cricket", "bollywood",
    "movie", "film", "review"
}

_NEGATIVE_PATTERN: re.Pattern = re.compile(
    r"|".join(re.escape(kw) for kw in NEGATIVE_KEYWORDS)
)

# Pre-compiled regex for multi-word disaster phrases (faster than splitting)
_PHRASE_PATTERN: re.Pattern = re.compile(
    r"|".join(re.escape(kw) for kw in DISASTER_KEYWORDS if " " in kw)
)

# Single-word keywords as a frozen set for O(1) lookup
_WORD_KEYWORDS: frozenset[str] = frozenset(kw for kw in DISASTER_KEYWORDS if " " not in kw)


def is_disaster_related(title: str, description: str = "") -> bool:
    """
    Return True if the combined title + description text contains at least
    one disaster-related keyword or phrase.

    Checks:
    1. Phrase keywords (multi-word) via regex — e.g. "flash flood"
    2. Single-word keywords via set intersection on tokenised words

    Args:
        title:       Article/event headline
        description: Body text / summary (optional)

    Returns:
        bool — True means "worth inserting into raw_events"
    """
    combined = f"{title} {description}".lower()

    # ── Step 0: Negative Keyword Exclusion ────────────────────────────────────
    if _NEGATIVE_PATTERN.search(combined):
        return False

    # ── Step 1: phrase match ──────────────────────────────────────────────────
    if _PHRASE_PATTERN.search(combined):
        return True

    # ── Step 2: word-level match ──────────────────────────────────────────────
    # Strip punctuation and split into words
    words = set(re.sub(r"[^\w\s]", " ", combined).split())
    if words & _WORD_KEYWORDS:
        return True

    return False


def get_matched_keywords(title: str, description: str = "") -> list[str]:
    """
    Return all matched disaster keywords (useful for debugging / logging).

    Args:
        title:       Article/event headline
        description: Body text / summary

    Returns:
        List of matched keyword strings (may be empty)
    """
    combined = f"{title} {description}".lower()
    matched: list[str] = []

    # Phrase matches
    for m in _PHRASE_PATTERN.finditer(combined):
        matched.append(m.group())

    # Word matches
    words = set(re.sub(r"[^\w\s]", " ", combined).split())
    single_matches = words & _WORD_KEYWORDS
    matched.extend(sorted(single_matches))

    return list(dict.fromkeys(matched))  # deduplicate, preserve insertion order
