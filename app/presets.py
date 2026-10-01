"""Channel presets and the Cloudinary transformations behind them (FR-07 to FR-10)."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from .listing import FALLBACK_BACKGROUND


@dataclass(frozen=True)
class Preset:
    id: str
    label: str
    width: int
    height: int
    style: str  # "cutout" = background removed on a solid colour, "scene" = generative fill
    background: str = "brand"  # "brand" or a fixed hex colour
    quality: str = "auto"
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


PRESETS: tuple[Preset, ...] = (
    Preset("instagram_post", "Instagram Post", 1080, 1080, "cutout", note="Square feed post on your brand colour"),
    Preset("instagram_story", "Instagram Story", 1080, 1920, "cutout", note="Full-screen vertical story"),
    Preset("marketplace", "Marketplace", 2000, 2000, "cutout", background="#FFFFFF",
           note="Pure white background for Amazon, Flipkart and Meesho"),
    Preset("whatsapp", "WhatsApp Catalog", 600, 600, "cutout", quality="auto:eco",
           note="Small and fast for chat sharing"),
    Preset("web_banner", "Website Banner", 1600, 600, "scene",
           note="Original scene extended with generative fill"),
)

PRESETS_BY_ID = {p.id: p for p in PRESETS}
_HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6})$")


def resolve_background(preset: Preset, brand_color: str | None, ai_suggestion: str | None) -> str:
    """Return the Cloudinary background value, e.g. 'rgb:FFFFFF'."""
    if preset.background != "brand":
        chosen = preset.background
    elif brand_color and brand_color.lower() != "auto" and _HEX_RE.match(brand_color.strip()):
        chosen = brand_color
    elif ai_suggestion and _HEX_RE.match(ai_suggestion.strip()):
        chosen = ai_suggestion
    else:
        chosen = FALLBACK_BACKGROUND
    return "rgb:" + _HEX_RE.match(chosen.strip()).group(1).upper()


def build_transformation(preset: Preset, background: str) -> list[dict]:
    if preset.style == "scene":
        steps = [{"width": preset.width, "height": preset.height, "crop": "pad", "background": "gen_fill"}]
    else:
        steps = [
            {"effect": "background_removal"},
            {"width": int(preset.width * 0.86), "height": int(preset.height * 0.86), "crop": "fit"},
            {"width": preset.width, "height": preset.height, "crop": "pad", "background": background},
        ]
    steps.append({"fetch_format": "auto", "quality": preset.quality})
    return steps


def selected_presets(ids: list[str] | None) -> list[Preset]:
    if not ids:
        return list(PRESETS)
    chosen = [PRESETS_BY_ID[i] for i in ids if i in PRESETS_BY_ID]
    return chosen or list(PRESETS)
