"""Gemma 4 multimodal analysis through the Gemini API (FR-04)."""

from __future__ import annotations

from .config import Settings
from .listing import ProductListing, parse_listing

PROMPT = """You are SnapShelf, an e-commerce listing assistant for small sellers.
Look carefully at the product in this photo and write a listing for it.

Reply with ONE JSON object only, no other text, using exactly these keys:
{
  "product_name": "short generic name of the product",
  "category": "store category, e.g. Kitchen, Fashion, Electronics, Beauty, Home Decor",
  "title": "marketplace title, max 80 characters, include material or colour if visible",
  "description": "2 to 3 persuasive sentences based only on what is visible",
  "features": ["feature 1", "feature 2", "feature 3"],
  "tags": ["5 to 8 lowercase search tags"],
  "alt_text": "one accessible sentence describing the product for screen readers",
  "social_caption": "one short Instagram caption with up to 3 hashtags",
  "background_hex": "#RRGGBB background colour that complements the product"
}
Do not invent brand names, prices or specifications that are not visible."""


class GemmaError(RuntimeError):
    """Raised when Gemma cannot produce a usable listing."""


def analyze_product(image_bytes: bytes, mime_type: str, settings: Settings) -> ProductListing:
    from google import genai
    from google.genai import types

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=settings.gemma_model,
            contents=[types.Part.from_bytes(data=image_bytes, mime_type=mime_type), PROMPT],
            config=types.GenerateContentConfig(temperature=0.4, max_output_tokens=1024),
        )
    except Exception as exc:  # network, auth, quota, unknown model
        detail = settings.redact(str(exc))[:300]
        raise GemmaError(f"Gemma request failed ({settings.gemma_model}): {detail}") from exc

    try:
        return parse_listing(response.text or "")
    except ValueError as exc:
        raise GemmaError(str(exc)) from exc
