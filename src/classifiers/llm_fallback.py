"""
src/classifiers/llm_fallback.py
───────────────────────────────
Gemini 2.5 Flash fallback wrapper.
Invoked ONLY if both Rule and ML classifiers fail to yield high confidence.
Uses structured JSON output to guarantee schema compliance.

Rate limits: Hard cap of LLM_MAX_CALLS_PER_CYCLE per pipeline run.
"""

import json
import logging
import os

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

_client = None

def _get_gemini_client():
    """Lazy init for Gemini client to ensure we have the API key."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("[LLM] GEMINI_API_KEY not found in environment!")
            return None
            
        _client = genai.Client(api_key=api_key)
    return _client


def llm_classify(title: str, description: str = "") -> tuple[str, float]:
    """
    Use Gemini to classify the disaster event.
    
    Returns:
        (disaster_type, confidence_score)
    """
    client = _get_gemini_client()
    if not client:
        return "unknown", 0.0
        
    text = f"Title: {title}\nDescription: {description}"
    
    prompt = f"""
Analyze the following news text and determine what kind of physical disaster it is describing.
If it is a metaphor (like a "political storm" or "market crash"), return "none".

Valid disaster types: flood, earthquake, cyclone, landslide, heatwave, fire, tsunami, storm, none.

Respond ONLY with a valid JSON object matching this schema exactly:
{{
  "disaster_type": "string (one of the valid types)",
  "confidence": float (0.0 to 1.0)
}}

News Text:
{text}
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",  # Updated to current stable model
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        data = json.loads(response.text)
        
        dtype = data.get("disaster_type", "unknown").lower().strip()
        confidence = float(data.get("confidence", 0.0))
        
        if dtype == "none":
            return "unknown", 0.0
            
        return dtype, confidence
        
    except Exception as e:
        logger.error(f"[LLM Classifier] Error generating/parsing response: {e}")
        return "unknown", 0.0
