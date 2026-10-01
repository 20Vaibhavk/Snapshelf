"""Parsing and normalisation of the listing that Gemma returns (FR-04, FR-05)."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

FALLBACK_BACKGROUND = "#F5F5F5"
MAX_TITLE = 80
MIN_TAGS, MAX_TAGS = 3, 10
FEATURE_COUNT = 3

_HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6})$")
_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


class ListingParseError(ValueError):
    """Raised when the model output contains no usable JSON listing."""


class ProductListing(BaseModel):
    # Run validators on defaults too, so a sparse model reply still meets FR-05.
    model_config = ConfigDict(validate_default=True)

    product_name: str = Field(default="Product")
    category: str = Field(default="General")
    title: str = Field(default="Product")
    description: str = Field(default="")
    features: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    alt_text: str = Field(default="Product photo")
    social_caption: str = Field(default="")
    background_hex: str = Field(default=FALLBACK_BACKGROUND)

    @field_validator("product_name", "category", "description", "alt_text", "social_caption", mode="before")
    @classmethod
    def _strip(cls, value):
        return " ".join(str(value or "").split())

    @field_validator("title", mode="before")
    @classmethod
    def _title(cls, value):
        title = " ".join(str(value or "").split()) or "Product"
        if len(title) > MAX_TITLE:
            title = title[: MAX_TITLE - 1].rstrip() + "…"
        return title

    @field_validator("features", mode="before")
    @classmethod
    def _features(cls, value):
        items = [" ".join(str(v).split()) for v in (value or []) if str(v).strip()]
        defaults = ["Quality build", "Everyday use", "Great value"]
        items = items[:FEATURE_COUNT]
        while len(items) < FEATURE_COUNT:
            items.append(defaults[len(items)])
        return items

    @field_validator("tags", mode="before")
    @classmethod
    def _tags(cls, value):
        if isinstance(value, str):
            value = value.split(",")
        seen: list[str] = []
        for raw in value or []:
            tag = re.sub(r"[^a-z0-9 \-]", "", str(raw).lower().lstrip("#")).strip()
            tag = " ".join(tag.split())
            if tag and tag not in seen:
                seen.append(tag)
        for filler in ("product", "shop", "new"):
            if len(seen) >= MIN_TAGS:
                break
            if filler not in seen:
                seen.append(filler)
        return seen[:MAX_TAGS]

    @field_validator("background_hex", mode="before")
    @classmethod
    def _hex(cls, value):
        match = _HEX_RE.match(str(value or "").strip())
        return f"#{match.group(1).upper()}" if match else FALLBACK_BACKGROUND


def _extract_json(text: str) -> dict:
    if not text or not text.strip():
        raise ListingParseError("Empty response from model")
    candidates = [m.group(1) for m in _FENCE_RE.finditer(text)]
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start : end + 1])
    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
    raise ListingParseError("Model response did not contain a JSON object")


def parse_listing(text: str) -> ProductListing:
    return ProductListing(**_extract_json(text))
