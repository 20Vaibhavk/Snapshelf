"""Application settings, read only from environment variables or a local .env file (NFR-01)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DEFAULT_GEMMA_MODEL = "gemma-4-27b-it"

# Values that mean "not filled in yet" (NFR-02).
_PLACEHOLDER_MARKERS = ("your_", "your-", "<", "changeme", "placeholder")


def _clean(value: str | None) -> str:
    value = (value or "").strip().strip('"').strip("'")
    if not value or any(marker in value.lower() for marker in _PLACEHOLDER_MARKERS):
        return ""
    return value


@dataclass(frozen=True)
class Settings:
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    gemini_api_key: str
    gemma_model: str
    max_upload_mb: int
    force_demo: bool

    @property
    def cloudinary_ready(self) -> bool:
        return all((self.cloudinary_cloud_name, self.cloudinary_api_key, self.cloudinary_api_secret))

    @property
    def gemini_ready(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def mode(self) -> str:
        if self.force_demo or not (self.cloudinary_ready and self.gemini_ready):
            return "demo"
        return "live"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    def missing_keys(self) -> list[str]:
        missing = []
        if not self.cloudinary_cloud_name:
            missing.append("CLOUDINARY_CLOUD_NAME")
        if not self.cloudinary_api_key:
            missing.append("CLOUDINARY_API_KEY")
        if not self.cloudinary_api_secret:
            missing.append("CLOUDINARY_API_SECRET")
        if not self.gemini_api_key:
            missing.append("GEMINI_API_KEY")
        return missing

    def redact(self, text: str) -> str:
        """Remove any configured credential from a message before it is logged or returned."""
        for secret in (self.cloudinary_api_key, self.cloudinary_api_secret, self.gemini_api_key):
            if secret:
                text = text.replace(secret, "[REDACTED]")
        return text

    def __repr__(self) -> str:  # never leak secrets into logs
        return f"Settings(mode={self.mode!r}, gemma_model={self.gemma_model!r}, missing={self.missing_keys()!r})"


def get_settings() -> Settings:
    try:
        max_mb = int(os.getenv("MAX_UPLOAD_MB", "10"))
    except ValueError:
        max_mb = 10
    return Settings(
        cloudinary_cloud_name=_clean(os.getenv("CLOUDINARY_CLOUD_NAME")),
        cloudinary_api_key=_clean(os.getenv("CLOUDINARY_API_KEY")),
        cloudinary_api_secret=_clean(os.getenv("CLOUDINARY_API_SECRET")),
        gemini_api_key=_clean(os.getenv("GEMINI_API_KEY")),
        gemma_model=_clean(os.getenv("GEMMA_MODEL")) or DEFAULT_GEMMA_MODEL,
        max_upload_mb=max(1, max_mb),
        force_demo=os.getenv("DEMO_MODE", "false").strip().lower() in {"1", "true", "yes"},
    )
