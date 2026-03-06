"""
Shared LLM model instance for all agents.

Supports two providers — set the matching API key in .env:
  • OpenAI  → OPENAI_API_KEY   (default model: gpt-4o-mini)
  • Gemini  → GOOGLE_API_KEY   (default model: gemini-2.5-flash-lite)

The MODEL env-var overrides the model name regardless of provider.
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

_openai_key = os.getenv("OPENAI_API_KEY")
_google_key = os.getenv("GOOGLE_API_KEY")

if _openai_key:
    # ── OpenAI ──────────────────────────────────────────────
    from langchain_openai import ChatOpenAI

    _model_name = os.getenv("MODEL", "gpt-4o-mini")
    logger.info("Using OpenAI model: %s", _model_name)

    llm = ChatOpenAI(
        model=_model_name,
        api_key=_openai_key,
        max_retries=0,
        timeout=60,
    )

elif _google_key:
    # ── Google Gemini ───────────────────────────────────────
    from langchain_google_genai import ChatGoogleGenerativeAI

    _model_name = os.getenv("MODEL", "gemini-2.5-flash-lite")
    # Strip provider prefix if present (e.g. "google-genai:gemini-2.0-flash")
    if ":" in _model_name:
        _model_name = _model_name.split(":", 1)[1]

    logger.info("Using Gemini model: %s", _model_name)

    # max_retries=0  → disables the internal tenacity retry loop in google-genai SDK
    #                  so 429 errors surface immediately instead of hanging for minutes.
    # timeout=60     → hard cap on any single API call (seconds).
    llm = ChatGoogleGenerativeAI(
        model=_model_name,
        google_api_key=_google_key,
        max_retries=0,
        timeout=60,
    )

else:
    raise RuntimeError(
        "No LLM API key found. Set OPENAI_API_KEY or GOOGLE_API_KEY in .env"
    )
