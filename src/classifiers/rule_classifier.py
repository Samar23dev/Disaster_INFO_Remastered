"""
src/classifiers/rule_classifier.py
──────────────────────────────────
Extremely fast keyword-based classifier.
If this returns a high-confidence match, we skip the heavy ML/LLM steps.

Returns a tuple: (disaster_type, confidence)
If confidence is 0.0, the pipeline should fall back to ML.
"""

import re

# Map of explicit keywords -> canonical disaster_type
# Order matters: more specific phrases should be checked first,
# but since these are distinct buckets, we use regex for all.

_RULE_MAP = {
    "flood":      [r"\bflash flood\b", r"\bfloods?\b", r"\bwaterlogging\b", r"\bcloudburst\b", r"\bdeluge\b", r"\binundat"],
    "earthquake": [r"\bearthquake\b", r"\bquake\b", r"\btremor\b", r"\bseismic\b", r"\brichter\b"],
    "cyclone":    [r"\bcyclone\b", r"\bhurricane\b", r"\btyphoon\b", r"\bstorm surge\b"],
    "landslide":  [r"\blandslide\b", r"\bmudslide\b", r"\bavalanche\b", r"\bdebris flow\b"],
    "heatwave":   [r"\bheatwave\b", r"\bheat wave\b", r"\bscorching\b", r"\bcold wave\b", r"\bblizzard\b"], # Mapping extreme temp to heatwave/temp generic
    "fire":       [r"\bforest fire\b", r"\bwildfire\b", r"\bbushfire\b", r"\bbuilding fire\b"],
    "tsunami":    [r"\btsunami\b", r"\btidal wave\b"],
    "storm":      [r"\bstorm\b", r"\bgale\b", r"\btornado\b", r"\bsquall\b"]
}

# Compile patterns once
_COMPILED_RULES = {
    dtype: re.compile(r"|".join(patterns), re.IGNORECASE)
    for dtype, patterns in _RULE_MAP.items()
}

def rule_classify(title: str, description: str = "") -> tuple[str | None, float]:
    """
    Check if the text definitively matches a disaster type based on hardcoded rules.
    
    Returns:
        (disaster_type, 0.75) if matched
        (None, 0.0) if no definitive match
    """
    combined = f"{title} {description}"

    for dtype, pattern in _COMPILED_RULES.items():
        if pattern.search(combined):
            return dtype, 0.75
            
    return None, 0.0
