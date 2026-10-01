"""FR-04, FR-06, FR-12, NFR-01: service wrappers with the external SDKs mocked."""

import json
from types import SimpleNamespace

import httpx
import pytest

from app import cloudinary_service, gemma_client
from app.cloudinary_service import CloudinaryError
from app.gemma_client import GemmaError
from tests.conftest import LIVE_SETTINGS


class FakeModels:
    def __init__(self, text=None, error=None):
        self.text, self.error, self.calls = text, error, []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(text=self.text)


def _patch_genai(monkeypatch, models):
    from google import genai

    monkeypatch.setattr(genai, "Client", lambda api_key: SimpleNamespace(models=models))


def test_gemma_sends_image_and_prompt_to_configured_model(monkeypatch):
    models = FakeModels(text=json.dumps({"title": "Red Mug", "tags": ["mug", "red", "cup"]}))
    _patch_genai(monkeypatch, models)
    listing = gemma_client.analyze_product(b"img", "image/png", LIVE_SETTINGS)
    assert listing.title == "Red Mug"
    call = models.calls[0]
    assert call["model"] == "gemma-4-test"
    assert len(call["contents"]) == 2
    assert call["contents"][1] == gemma_client.PROMPT


def test_gemma_network_error_is_wrapped_and_redacted(monkeypatch):
    _patch_genai(monkeypatch, FakeModels(error=RuntimeError("bad key test-gemini-333")))
    with pytest.raises(GemmaError) as info:
        gemma_client.analyze_product(b"img", "image/png", LIVE_SETTINGS)
    assert "test-gemini-333" not in str(info.value)
    assert "[REDACTED]" in str(info.value)


def test_gemma_unparseable_reply_raises(monkeypatch):
    _patch_genai(monkeypatch, FakeModels(text="I cannot see a product."))
    with pytest.raises(GemmaError):
        gemma_client.analyze_product(b"img", "image/png", LIVE_SETTINGS)


def test_cloudinary_upload_returns_metadata(monkeypatch):
    import cloudinary.uploader

    captured = {}

    def fake_upload(file, **options):
        captured.update(options)
        return {"public_id": "snapshelf/mug_x", "secure_url": "https://res.cloudinary.com/testcloud/mug_x.png",
                "bytes": 1234, "width": 10, "height": 20, "format": "png"}

    monkeypatch.setattr(cloudinary.uploader, "upload", fake_upload)
    result = cloudinary_service.upload_image(b"img", "mug", LIVE_SETTINGS)
    assert result == {"public_id": "snapshelf/mug_x", "url": "https://res.cloudinary.com/testcloud/mug_x.png",
                      "bytes": 1234, "width": 10, "height": 20, "format": "png"}
    assert captured["folder"] == "snapshelf"
    assert "snapshelf" in captured["tags"]


def test_cloudinary_upload_error_is_redacted(monkeypatch):
    import cloudinary.uploader

    def fake_upload(file, **options):
        raise Exception("Invalid Signature for test-key-111 / test-secret-222")

    monkeypatch.setattr(cloudinary.uploader, "upload", fake_upload)
    with pytest.raises(CloudinaryError) as info:
        cloudinary_service.upload_image(b"img", "mug", LIVE_SETTINGS)
    assert "test-key-111" not in str(info.value)
    assert "test-secret-222" not in str(info.value)


def test_measure_optimization_calculates_savings(monkeypatch):
    monkeypatch.setattr(cloudinary_service.httpx, "get", lambda *a, **k: httpx.Response(
        200, content=b"x" * 250, headers={"content-type": "image/avif"}, request=httpx.Request("GET", "https://x")))
    result = cloudinary_service.measure_optimization(1000, "https://x")
    assert result["optimized_bytes"] == 250
    assert result["saved_percent"] == 75.0
    assert result["delivered_format"] == "image/avif"


def test_measure_optimization_tolerates_network_errors(monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(cloudinary_service.httpx, "get", boom)
    result = cloudinary_service.measure_optimization(1000, "https://x")
    assert result["optimized_bytes"] is None
    assert result["saved_percent"] is None
