"""SnapShelf API: upload one product photo, get a listing and channel-ready images."""

from __future__ import annotations

import asyncio
import io
import logging
import re
import time
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

from . import __version__, cloudinary_service, demo, gemma_client
from .cloudinary_service import CloudinaryError
from .config import PROJECT_ROOT, Settings, get_settings
from .gemma_client import GemmaError
from .presets import PRESETS, selected_presets

log = logging.getLogger("snapshelf")

ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
PIL_TO_MIME = {"JPEG": ("image/jpeg", "jpg"), "PNG": ("image/png", "png"), "WEBP": ("image/webp", "webp")}
STATIC_DIR = PROJECT_ROOT / "static"

app = FastAPI(title="SnapShelf", version=__version__,
              description="AI product photo studio built with Gemma 4 and Cloudinary")
demo.UPLOAD_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=demo.UPLOAD_DIR), name="uploads")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health(settings: Settings = Depends(get_settings)) -> dict:
    return {
        "status": "ok",
        "version": __version__,
        "mode": settings.mode,
        "gemma_model": settings.gemma_model,
        "missing_keys": settings.missing_keys() if settings.mode == "demo" else [],
        "max_upload_mb": settings.max_upload_mb,
    }


@app.get("/api/presets")
def presets() -> list[dict]:
    return [p.to_dict() for p in PRESETS]


async def _read_and_validate(file: UploadFile, settings: Settings) -> tuple[bytes, str, str]:
    """Return (bytes, mime type, extension) or raise the right HTTP error (FR-01 to FR-03)."""
    if (file.content_type or "").lower() not in ALLOWED_TYPES:
        raise HTTPException(415, "Unsupported file type. Please upload a JPEG, PNG or WEBP image.")
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(413, f"Image is larger than {settings.max_upload_mb} MB.")
    if not data:
        raise HTTPException(400, "The uploaded file is empty.")
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.verify()
            detected = image.format
    except Exception:
        raise HTTPException(400, "The file could not be read as an image.") from None
    if detected not in PIL_TO_MIME:
        raise HTTPException(415, "Unsupported image format. Please upload a JPEG, PNG or WEBP image.")
    mime, extension = PIL_TO_MIME[detected]
    return data, mime, extension


def _safe_stem(filename: str | None) -> str:
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", Path(filename or "product").stem).strip("_")
    return stem[:60] or "product"


@app.post("/api/process")
async def process(
    file: UploadFile = File(...),
    brand_color: str = Form("auto"),
    presets: str = Form(""),
    settings: Settings = Depends(get_settings),
) -> dict:
    data, mime, extension = await _read_and_validate(file, settings)
    chosen = selected_presets([p.strip() for p in presets.split(",") if p.strip()])
    started = time.perf_counter()
    warnings: list[str] = []

    if settings.mode == "demo":
        upload = demo.save_upload(data, extension)
        listing = demo.DEMO_LISTING
        variants = demo.build_variants(upload, chosen, brand_color, listing.background_hex)
        optimization = {"original_bytes": len(data), "optimized_bytes": None, "saved_percent": None}
        warnings.append("Demo mode: sample listing and local preview. Add your API keys to .env "
                        "for real Gemma 4 analysis and Cloudinary AI transformations.")
    else:
        # NFR-03: Gemma analysis and Cloudinary upload run in parallel.
        gemma_result, upload_result = await asyncio.gather(
            asyncio.to_thread(gemma_client.analyze_product, data, mime, settings),
            asyncio.to_thread(cloudinary_service.upload_image, data, _safe_stem(file.filename), settings),
            return_exceptions=True,
        )
        if isinstance(upload_result, BaseException):
            message = str(upload_result) if isinstance(upload_result, CloudinaryError) else "Cloudinary upload failed."
            log.warning("Cloudinary failure: %s", message)
            raise HTTPException(502, message)
        upload = upload_result

        if isinstance(gemma_result, BaseException):
            listing = None
            message = str(gemma_result) if isinstance(gemma_result, GemmaError) else "Gemma analysis failed."
            log.warning("Gemma failure: %s", message)
            warnings.append(f"AI listing unavailable: {message} Images were still generated.")
        else:
            listing = gemma_result

        variants = cloudinary_service.build_variants(
            upload["public_id"], chosen, brand_color, listing.background_hex if listing else None)
        optimization = await asyncio.to_thread(
            cloudinary_service.measure_optimization, upload.get("bytes"),
            cloudinary_service.optimized_original_url(upload["public_id"]))

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    log.info("Processed %s in %d ms (mode=%s, variants=%d)", extension, elapsed_ms, settings.mode, len(variants))
    return {
        "mode": settings.mode,
        "gemma_model": settings.gemma_model,
        "original": upload,
        "listing": listing.model_dump() if listing else None,
        "variants": variants,
        "optimization": optimization,
        "warnings": warnings,
        "elapsed_ms": elapsed_ms,
    }
