"""
src/geo/ner_extractor.py
────────────────────────
Uses spaCy (en_core_web_sm) to extract Geographical Entities (GPE/LOC) from text.

Usage:
  from src.geo.ner_extractor import extract_locations
  locations = extract_locations("Major flood hits Assam and Guwahati.")
"""

import logging

import spacy

logger = logging.getLogger(__name__)

# Singleton spaCy model
_nlp = None

def get_nlp():
    """Lazy load the spaCy model."""
    global _nlp
    if _nlp is None:
        logger.info("[NER] Loading spaCy en_core_web_sm model...")
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.error("[NER] spaCy model not found. Did you run: python -m spacy download en_core_web_sm?")
            # Very basic fallback model if download failed
            from spacy.lang.en import English
            _nlp = English()
            _nlp.add_pipe("ner") # Will be mostly empty but won't crash
    return _nlp

def extract_locations(text: str) -> list[str]:
    """
    Extract geographical entities from the text.
    Returns a deduplicated list of location strings.
    """
    if not text.strip():
        return []
        
    nlp = get_nlp()
    # Enforce a max length string to avoid spacy buffer overflows
    doc = nlp(text[:10000]) 
    
    locations = []
    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC"]:  # Removed FAC to avoid building names
            # Clean up trailing punctuation
            clean_loc = ent.text.strip(" .,;:'\"()[]{}")
            if len(clean_loc) > 2:  # Ignore garbage 1-2 char outputs
                locations.append(clean_loc)
                
    # Deduplicate while preserving order
    return list(dict.fromkeys(locations))
