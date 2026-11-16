"""Minimal Gemini (Google AI Studio) client shared by the text and video recaps.

Calls the REST API directly (no extra dependency). Retries briefly and falls
back to a lighter model when Google reports overload (503) or rate limits (429).
"""

import json
import logging
import time
import urllib.error
import urllib.request

from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

# Tried in order when the configured model is overloaded, rate-limited or too slow
_BACKUP_MODELS = ["gemini-flash-lite-latest", "gemini-flash-latest"]
_RETRYABLE = {429, 500, 503}
_TIMEOUT_SECONDS = 45


class GeminiHTTPError(RuntimeError):
    def __init__(self, code: int, body: str) -> None:
        super().__init__(f"Gemini HTTP {code}: {body[:300]}")
        self.code = code


def is_configured() -> bool:
    return bool(settings.gemini_api_key)


def generate_json(prompt: str, system: str | None = None, max_tokens: int = 8192) -> str:
    """Return the model's raw JSON text for `prompt`."""
    models = [settings.gemini_model] + [m for m in _BACKUP_MODELS if m != settings.gemini_model]
    last_exc: Exception | None = None
    for model in models:
        for attempt in range(2):
            try:
                return _request(model, prompt, system, max_tokens)
            except GeminiHTTPError as exc:
                last_exc = exc
                if exc.code not in _RETRYABLE:
                    raise
                logger.warning("Gemini %s busy (HTTP %s), attempt %d", model, exc.code, attempt + 1)
                time.sleep(2 * (attempt + 1))
            except (TimeoutError, urllib.error.URLError) as exc:
                # Too slow / network hiccup: don't wait again on the same model, try the next one
                last_exc = exc
                logger.warning("Gemini %s timed out or unreachable (%s), trying next model", model, exc)
                break
    raise last_exc  # type: ignore[misc]


def _request(model: str, prompt: str, system: str | None, max_tokens: int) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body: dict = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": max_tokens},
    }
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": settings.gemini_api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as res:
            data = json.load(res)
    except urllib.error.HTTPError as exc:
        # Google's error body never includes the key, safe to log
        raise GeminiHTTPError(exc.code, exc.read().decode()) from exc
    parts = data["candidates"][0]["content"]["parts"]
    logger.info("Gemini answered with model %s", model)
    return "".join(p.get("text", "") for p in parts)
