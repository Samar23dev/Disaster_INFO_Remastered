"""
src/classifiers/severity_detector.py
─────────────────────────────────────
Analyzes raw text to determine disaster severity based on lexical cues.

Levels:
  - HIGH: Mentions casualties, destruction, major disruption, rescue ops
  - MEDIUM: Warnings, alerts, forecasts, risk
  - LOW: General advisory, update, monitoring (fallback default)

Usage:
  from src.classifiers.severity_detector import detect_severity
  sev = detect_severity(title, description)
"""

import re

# Pre-compiled regex patterns for speed
HIGH_PATTERN = re.compile(
    r"\b(killed|dead|deaths?|destroyed|evacuations?|rescue|"
    r"collapse|casualties|fatalities|massive|severe damage|catastrophe|"
    r"emergency|tragedy|devastation)\b",
    re.IGNORECASE
)

MEDIUM_PATTERN = re.compile(
    r"\b(warning|alert|watch|expected|possible|risk|forecast|"
    r"approaching|moderate|threat)\b",
    re.IGNORECASE
)

def detect_severity(title: str, description: str = "") -> str:
    """
    Determine the severity of a disaster event from its text.
    
    Args:
        title: Article title
        description: Article body/summary
        
    Returns:
        "HIGH", "MEDIUM", or "LOW"
    """
    combined = f"{title} {description}"

    if HIGH_PATTERN.search(combined):
        return "HIGH"
    
    if MEDIUM_PATTERN.search(combined):
        return "MEDIUM"
        
    return "LOW"
