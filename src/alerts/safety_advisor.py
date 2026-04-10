"""
src/alerts/safety_advisor.py
────────────────────────────
Utilises Gemini 1.5 Flash to automatically generate specific community safety 
recommendations for high-risk disasters.

Implements an aggressive runtime cache to prevent redundant API calls 
during large-scale regional emergencies.
"""

import logging
import time

from google import genai
from google.genai import types

from src.classifiers.llm_fallback import _get_gemini_client

logger = logging.getLogger(__name__)

# Basic dictionary cache to prevent redundant Gemini API calls.
# Key: (disaster_type, severity) -> Value: (safety_text, timestamp)
_TIPS_CACHE: dict[tuple[str, str], tuple[str, float]] = {}
CACHE_TTL = 3600  # 1 hour

# Fallback generic templates if LLM is offline or rate limited.
_FALLBACK_ADVICE = {
    "flood": "Move to higher ground immediately. Do not walk or drive through flood waters.",
    "earthquake": "Drop, Cover, and Hold On. Stay away from windows and exterior walls.",
    "cyclone": "Stay indoors away from windows. Evacuate immediately if instructed by local authorities.",
    "fire": "Evacuate the area immediately. If caught in smoke, stay low to the ground.",
    "heatwave": "Stay hydrated, remain indoors during peak heat hours, and check on vulnerable neighbors."
}

def get_safety_advice(disaster_type: str, severity: str) -> str:
    """
    Fetch structural safety recommendations for a disaster.
    Hits a local memory cache first.
    """
    cache_key = (disaster_type.lower(), severity.upper())
    
    # 1. Check local cache
    if cache_key in _TIPS_CACHE:
        advice, timestamp = _TIPS_CACHE[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            return advice
            
    # 2. Invoke Gemini LLM 
    client = _get_gemini_client()
    if client:
        prompt = f"""
Provide exactly 2 concise, highly actionable safety tips for civilians facing a {severity} severity {disaster_type}.
Do not use introductory text, formatting, or bullet points. Just two clear sentences.
"""
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",  # Updated to current stable model
                contents=prompt
            )
            advice = response.text.strip().replace("\n", " ")
            
            if advice:
                _TIPS_CACHE[cache_key] = (advice, time.time())
                return advice
                
        except Exception as e:
            logger.error(f"[Safety Advisor] Failed generating tips from Gemini: {e}")
            
    # 3. Drop down to strict static fallback mapping if LLM fails
    fallback = _FALLBACK_ADVICE.get(disaster_type.lower(), "Follow all instructions from local emergency authorities immediately.")
    _TIPS_CACHE[cache_key] = (fallback, time.time())
    
    return fallback
