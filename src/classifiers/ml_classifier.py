"""
src/classifiers/ml_classifier.py
────────────────────────────────
Zero-shot ML classifier using HuggingFace 'distilbart-mnli-12-3'.

Loads the model efficiently and classifies text against the known disaster labels.
"""

import logging
from typing import Any

from transformers import pipeline

logger = logging.getLogger(__name__)

# Core disaster labels supported by the system
CANDIDATE_LABELS = [
    "flood", "earthquake", "cyclone", "landslide", 
    "heatwave", "fire", "tsunami", "storm"
]

# Singleton instance to avoid reloading the model on every call
_classifier: Any = None

def get_ml_classifier():
    """Lazy load the HuggingFace zero-shot pipeline."""
    global _classifier
    if _classifier is None:
        logger.info("[ML Classifier] Loading distilbart-mnli-12-3 ...")
        # Initialize pipeline. Downloads model on first run.
        _classifier = pipeline(
            "zero-shot-classification",
            model="valhalla/distilbart-mnli-12-3"
        )
        logger.info("[ML Classifier] Model loaded successfully.")
    return _classifier


def ml_classify(title: str, description: str = "") -> tuple[str, float]:
    """
    Run zero-shot classification on the text.
    
    Returns:
        (best_label, confidence_score)
    """
    classifier = get_ml_classifier()
    text = f"{title}. {description}"
    
    try:
        # We don't use multi_label=True. We want the best single category.
        result = classifier(text, CANDIDATE_LABELS)
        best_label = result['labels'][0]
        confidence = result['scores'][0]
        return best_label, float(confidence)
    except Exception as e:
        logger.error(f"[ML Classifier] Error during inference: {e}")
        return "unknown", 0.0
