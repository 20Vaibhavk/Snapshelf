"""Demo mode: the full flow without API keys (FR-14)."""

from __future__ import annotations

import uuid

from .config import PROJECT_ROOT
from .listing import ProductListing
from .presets import Preset, build_transformation, resolve_background

UPLOAD_DIR = PROJECT_ROOT / "uploads"

DEMO_LISTING = ProductListing(
    product_name="Ceramic Coffee Mug",
    category="Kitchen",
    title="Handcrafted Ceramic Coffee Mug, 350 ml, Matte Finish",
    description=("A sturdy everyday mug with a smooth matte glaze and a comfortable handle. "
                 "Ideal for coffee, tea or hot chocolate, and a thoughtful gift for any kitchen."),
    features=["Matte glazed ceramic", "Comfortable C-shaped handle", "Microwave and dishwasher safe"],
    tags=["coffee mug", "ceramic mug", "kitchen", "gift", "tea cup", "handmade"],
    alt_text="A matte ceramic coffee mug with a curved handle on a plain background.",
    social_caption="Morning rituals, upgraded. #coffeetime #handmade #kitchendecor",
    background_hex="#F3E9DC",
)


def save_upload(image_bytes: bytes, extension: str) -> dict:
    UPLOAD_DIR.mkdir(exist_ok=True)
    name = f"{uuid.uuid4().hex}.{extension}"
    (UPLOAD_DIR / name).write_bytes(image_bytes)
    return {"public_id": f"demo/{name}", "url": f"/uploads/{name}", "bytes": len(image_bytes),
            "format": extension}


def build_variants(upload: dict, presets: list[Preset], brand_color: str | None,
                   ai_background: str | None) -> list[dict]:
    """Same metadata as live mode. The image is the local original, styled by the browser."""
    variants = []
    for preset in presets:
        background = resolve_background(preset, brand_color, ai_background)
        variants.append({
            **preset.to_dict(),
            "background_used": background,
            "transformation": build_transformation(preset, background),
            "url": upload["url"],
            "download_url": upload["url"],
        })
    return variants
