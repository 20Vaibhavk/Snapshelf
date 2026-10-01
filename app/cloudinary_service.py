"""Cloudinary upload, AI transformations and optimized delivery (FR-06 to FR-12)."""

from __future__ import annotations

import io

import httpx

from .config import Settings
from .presets import Preset, build_transformation, resolve_background

FOLDER = "snapshelf"


class CloudinaryError(RuntimeError):
    """Raised when Cloudinary cannot store the image."""


def configure(settings: Settings) -> None:
    import cloudinary

    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )


def upload_image(image_bytes: bytes, filename: str, settings: Settings) -> dict:
    import cloudinary.uploader

    configure(settings)
    try:
        result = cloudinary.uploader.upload(
            io.BytesIO(image_bytes),
            folder=FOLDER,
            resource_type="image",
            use_filename=True,
            unique_filename=True,
            filename_override=filename,
            tags=["snapshelf"],
        )
    except Exception as exc:
        detail = settings.redact(str(exc))[:300]
        raise CloudinaryError(f"Cloudinary upload failed: {detail}") from exc
    return {
        "public_id": result["public_id"],
        "url": result["secure_url"],
        "bytes": result.get("bytes"),
        "width": result.get("width"),
        "height": result.get("height"),
        "format": result.get("format"),
    }


def _url(public_id: str, transformation: list[dict]) -> str:
    from cloudinary import CloudinaryImage

    return CloudinaryImage(public_id).build_url(transformation=transformation, secure=True)


def build_variants(public_id: str, presets: list[Preset], brand_color: str | None,
                   ai_background: str | None) -> list[dict]:
    variants = []
    for preset in presets:
        background = resolve_background(preset, brand_color, ai_background)
        steps = build_transformation(preset, background)
        download_steps = steps + [{"flags": f"attachment:snapshelf_{preset.id}"}]
        variants.append({
            **preset.to_dict(),
            "background_used": background,
            "url": _url(public_id, steps),
            "download_url": _url(public_id, download_steps),
        })
    return variants


def optimized_original_url(public_id: str) -> str:
    return _url(public_id, [{"fetch_format": "auto", "quality": "auto"}])


def measure_optimization(original_bytes: int | None, optimized_url: str, timeout: float = 20.0) -> dict:
    """Compare the uploaded size with what Cloudinary actually delivers (f_auto, q_auto)."""
    result = {"original_bytes": original_bytes, "optimized_bytes": None, "saved_percent": None,
              "optimized_url": optimized_url}
    try:
        response = httpx.get(optimized_url, timeout=timeout, follow_redirects=True,
                             headers={"Accept": "image/avif,image/webp,image/*"})
        response.raise_for_status()
        result["optimized_bytes"] = len(response.content)
        result["delivered_format"] = response.headers.get("content-type")
    except httpx.HTTPError:
        return result
    if original_bytes:
        result["saved_percent"] = round(100 * (1 - result["optimized_bytes"] / original_bytes), 1)
    return result
