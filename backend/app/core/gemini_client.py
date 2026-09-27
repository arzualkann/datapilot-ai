"""Gemini client factory used by SQL generation."""

from functools import lru_cache

from google import genai

from app.core.config import get_settings


GEMINI_MODEL = "gemini-3.5-flash-lite"


@lru_cache
def get_gemini_client() -> genai.Client:
    api_key = get_settings().gemini_api_key
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    return genai.Client(api_key=api_key)
