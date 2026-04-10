"""
src/alerts/risk_scorer.py
─────────────────────────
Calculates a numeric risk score (0-100) for a given processed event.

Risk is a composite metric derived from:
  - Severity Level (HIGH=50, MEDIUM=25, LOW=10)
  - Source Count (higher source count = higher validity/impact) +2 per source
  - Confidence (ML/LLM confidence multiplier)
  
Usage:
  score = calculate_risk_score("HIGH", 0.85, 3)
"""

import logging

logger = logging.getLogger(__name__)

def calculate_risk_score(severity: str, confidence: float, source_count: int) -> int:
    """
    Calculate a disaster event's quantitative risk score.
    
    Args:
        severity: "HIGH", "MEDIUM", or "LOW"
        confidence: Float between 0.0 and 1.0
        source_count: Number of independent news sources confirming the event
        
    Returns:
        Integer score between 0 and 100.
    """
    # 1. Base score derived purely from lexical severity
    severity_upper = severity.upper()
    if severity_upper == "HIGH":
        base = 50.0
    elif severity_upper == "MEDIUM":
        base = 25.0
    else:
        base = 10.0
        
    # 2. Add corroboration weighting (max +30 points for 15+ sources)
    corroboration_bonus = min(30.0, (source_count - 1) * 2.0)
    
    # 3. Compile Raw Metric
    raw_score = base + corroboration_bonus
    
    # 4. Modulate strictly by Machine Learning Confidence
    # e.g. A HIGH severity claim with only 50% ML confidence gets heavily nerfed
    adjusted_score = raw_score * max(0.2, confidence) # Base floor of 0.2 multiplier
    
    # 5. Provide an exponential scalar for extreme events
    if severity_upper == "HIGH" and source_count >= 5 and confidence >= 0.8:
        adjusted_score *= 1.2
        
    final_score = int(round(adjusted_score))
    
    # Boundary constraints
    return max(0, min(100, final_score))
