"""
src/geo/loc_normalizer.py
─────────────────────────
Standardises historical or common misspellings of major Indian cities/states
to their canonical Nominatim-friendly names.

Usage:
  from src.geo.loc_normalizer import normalize_location
  loc = normalize_location("Bombay")  # returns "Mumbai"
"""

ALIAS_DICT: dict[str, str] = {
    "bombay":      "Mumbai",
    "madras":      "Chennai",
    "calcutta":    "Kolkata",
    "bangalore":   "Bengaluru",
    "poona":       "Pune",
    "gurgaon":     "Gurugram",
    "baroda":      "Vadodara",
    "benares":     "Varanasi",
    "kashi":       "Varanasi",
    "pondicherry": "Puducherry",
    "trivandrum":  "Thiruvananthapuram",
    "orissa":      "Odisha",
    "uttaranchal": "Uttarakhand",
    "gauhati":     "Guwahati",
}

def normalize_location(location_name: str) -> str:
    """
    Replace known old names and aliases with modern canonical forms.
    Returns the mapped name, or the original (title-cased) if no mapping exists.
    """
    sanitized = location_name.lower().strip()
    return ALIAS_DICT.get(sanitized, location_name.strip())
